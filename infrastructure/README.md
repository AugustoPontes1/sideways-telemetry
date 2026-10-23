# Drift Telemetry Lab — Homelab Compose + HAProxy

Arquitetura: `Windows/AC Bridge -> WSL/Telemetry Agent --WSS--> HAProxy(TLS) -> Nginx(frontend) -> Django Channels -> PostgreSQL/Redis`.
O browser usa a **mesma origem HTTPS** para frontend, REST e WebSocket; o token Bearer do Telemetry Agent NÃO entra no JavaScript.

## Preparação

- Docker Engine + `docker compose` no homelab; DNS local (`telemetry.lab.local` -> IP da VM).
- Copiar `.env.example` para `infrastructure/.env`, preencher `DJANGO_SECRET_KEY`, `TELEMETRY_TOKEN` e `POSTGRES_PASSWORD` com valores diferentes e aleatórios. `chmod 600 infrastructure/.env`.
- Ajustar `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` para o host e porta HTTPS escolhidos. `HTTPS_BIND_IP` começa com `127.0.0.1` de propósito: configure para o IP LAN **somente após** definir regras de firewall permitindo apenas seus dispositivos.
- Colocar certificado PEM com cert+cadeia+chave privada em `infrastructure/haproxy/certs/telemetry.pem`. Não há certificado nem senha prontos no repositório. **A imagem HAProxy executa com UID 99**: a chave montada deve ser legível por esse usuário do container (consulte os comandos abaixo para Docker rootful). Prefira CA privada confiável em Windows, WSL e navegador. Para teste local, certificado autofirmado pode exigir instalação no trust store; não desabilite verificação TLS.

Exemplo de certificado *somente para ambiente de laboratório*, com hostname específico (não usar na internet pública):

```bash
openssl req -x509 -nodes -newkey rsa:3072 -days 30 \
  -keyout /tmp/drift-tls.key -out /tmp/drift-tls.crt \
  -subj '/CN=telemetry.lab.local' -addext 'subjectAltName=DNS:telemetry.lab.local'
cat /tmp/drift-tls.crt /tmp/drift-tls.key > infrastructure/haproxy/certs/telemetry.pem
# Na imagem oficial HAProxy Alpine o processo roda como UID 99 (haproxy).
# No Docker Linux rootful, permita somente a esse usuário ler o segredo:
sudo chown 99:99 infrastructure/haproxy/certs/telemetry.pem
sudo chmod 600 infrastructure/haproxy/certs/telemetry.pem
# Se seu Docker usa user namespaces/rootless, configure permissões/ACL para o UID mapeado.
# Instale/confiabilize /tmp/drift-tls.crt como CA/cert nas máquinas que fazem conexão.
```

## Execução (na RAIZ do repositório)

```bash
python3 infrastructure/scripts/check_config.py # requer PyYAML
# valide também no seu host, com Compose instalado:
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml config --quiet
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml up -d --build
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml ps
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml exec backend python manage.py createsuperuser
```

Teste DNS e acesso HTTPS ao `https://telemetry.lab.local:8443/`. O endereço `https://telemetry.lab.local:8443/admin/login/` usa a sessão Django. O WSL deve usar `TELEMETRY_UPSTREAM_URL=wss://telemetry.lab.local:8443/ws/ingest/`, `TELEMETRY_TOKEN` e `TELEMETRY_AGENT_ID` correspondentes ao `.env` do homelab; para CA privada configure `TELEMETRY_CA_FILE` com arquivo CA PEM confiável, *não* a chave privada do servidor.

## Segurança e limitações

- **Somente HAProxy** publica HTTPS no host. PostgreSQL, Redis, Django e Nginx estão apenas nas redes Docker internas. A rede `data` é isolada até mesmo de saída externa.
- HAProxy remove valores encaminhados pelo cliente e define `X-Forwarded-Proto=https`, necessários para `SECURE_PROXY_SSL_HEADER` do Django, e trata upgrades WebSocket usando `timeout tunnel`.
- Nenhuma porta HTTP externa ou TLS inseguro é habilitado por padrão. Para LAN, defina `HTTPS_BIND_IP` para IP do homelab com firewall.
- O Nginx incluído no frontend encaminha `/ws/` para Django; o AC Bridge/WSL NÃO deve enviar diretamente para PostgreSQL.
- O `infrastructure/Dockerfile.backend` instala os 3 pacotes de `packages/`, porém a API do Django anterior continua usando seus serviços próprios. Uma posterior integração de endpoints pode usar `drift_analysis`, sem alterar o contrato de ingestão.
- O front-end entregue anteriormente faz `npm install` no build em vez de `npm ci` e não tem lockfile versionado. **Antes de implantar de modo reproduzível**, gere e versione `package-lock.json` e troque para `npm ci`.
- Os sensores `heading_rad`, sinal de direção e orientação do carro ainda requerem calibração com o Assetto Corsa original. Nenhum RPM isolado cria uma linha de drift ótima.
- Execute `docker compose ... down` sem `-v` para preservar o volume do banco.
