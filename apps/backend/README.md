# Drift Telemetry Lab — Backend (Django no homelab)

MVP do backend para **Assetto Corsa original + Content Manager**. A ingestão implementa **exatamente** o envelope do `telemetry-agent/transport.py` do projeto anterior.

## Separação de responsabilidades

```text
backend/
├── config/             # settings, URLs, ASGI/Channels
├── sessions/           # captura por stream_id, contagem, carro e pista
├── telemetry/          # validação do protocolo, ingestão, modelos, WebSockets e API
├── analysis/           # estatísticas, eventos e comparação com referência gravada
├── learning/           # exercícios das aulas; solução oculta por padrão
├── tests/              # testes de protocolo, álgebra e integração Django
├── compose.yaml        # Django/Daphne + PostgreSQL + Redis
└── Dockerfile
```

> **Atenção:** por enquanto, uma `DrivingSession` representa **um stream_id do AC Bridge**, não necessariamente uma única volta ou sessão dentro do jogo. Se trocar de carro/pista sem reiniciar a ponte, o stream continua: a versão futura precisará subdividi-lo em sessões de pilotagem, usando eventos de transição. Não inferimos isso apenas pelo contador de voltas.

## Contrato WSL → backend

O `telemetry-agent/transport.py` conecta-se em `wss://SEU_HOST/ws/ingest/` com `Authorization: Bearer <TELEMETRY_TOKEN>` e envia:

```json
{
  "type": "telemetry.batch",
  "schema_version": 1,
  "batch_id": "024d5d9c-4a19-4fb2-8f4b-3935a165afba",
  "agent_id": "wsl-assetto-agent",
  "samples": [
    {"type": "telemetry", "stream_id": "d0d04919-ff5c-4f86-b13f-688114a9b1e4", "sequence": 0,
     "received_at_unix_ns": 1792500000000000000, "telemetry": {"...": "frame completo normalizado"}}
  ]
}
```

O exemplo é **estrutural**: a `telemetry` precisa conter os campos completos produzidos por `normalizer.py`, e não apenas o marcador `...`.

Somente depois do COMMIT de todo o lote o backend confirma:

```json
{"type":"telemetry.ack","batch_id":"024d5d9c-4a19-4fb2-8f4b-3935a165afba","accepted":1}
```

- `accepted` é a quantidade *reconhecida*, incluindo amostras já salvas. Isso coincide com o que o agente espera em `_check_ack()`.
- Há unicidade de `(session_id, sequence)` e verificação do hash de cada quadro para detectar reenvio divergente.
- O lote inteiro é atômico, mesmo contendo mais de um `stream_id`.
- Em erro, retorna `telemetry.error` ou fecha a conexão **sem ACK**; o buffer do WSL retém os dados para reenvio. Lotes inválidos precisam de correção: o agente não faz descarte automático.
- As mesmas amostras são publicadas para clientes WebSocket autenticados após o ACK; o canal ao vivo não substitui a leitura durável da API.

## Instalação de desenvolvimento (WSL, sem Docker)

Requer Python **3.11+** e acesso às dependências PyPI.

```bash
cd ~/drift-telemetry-lab/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Em desenvolvimento, o backend carrega automaticamente `apps/backend/.env`.
Coloque nele `DJANGO_DEBUG=True` e `TELEMETRY_TOKEN`.

No **outro terminal** do WSL, inicie o agente com o mesmo token. O teste de `ws://` só é permitido para localhost:

```bash
cd ~/drift-telemetry-lab/telemetry-agent
source .venv/bin/activate
python main.py --allow-insecure-dev
```

O agente também carrega automaticamente o mesmo `apps/backend/.env`. O
`TELEMETRY_TOKEN` deve ser idêntico nos dois processos; reinicie-os depois de
alterar o arquivo.

Depois, em outro terminal na **raiz** do repositório:

```bash
python examples/fake_ac_bridge.py --count 120 --hz 50
```

Ou execute o `ac-bridge/publisher.py` no Python do Windows enquanto joga.

Esse teste usa o Django no WSL como *backend de desenvolvimento*, sem Proxmox. Em produção, o agente apontará para o hostname interno do homelab, com `wss://` e certificado verificado.

## Implantação no homelab com Docker Compose

Este `compose.yaml` presume que o **HAProxy está na mesma VM** em que se publica a porta local do backend. Se o HAProxy estiver em outra VM, exponha apenas na interface interna necessária e restrinja por firewall à origem do HAProxy.

```bash
cd ~/drift-telemetry-lab/backend
cp .env.example .env
chmod 600 .env
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'   # DJANGO_SECRET_KEY
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'   # TELEMETRY_TOKEN (OUTRO segredo)
```

Edite `.env`, preenchendo também `POSTGRES_PASSWORD` com senha forte e o hostname que seu HAProxy realmente atende. **Não reutilize os exemplos em produção.**

```bash
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
docker compose ps
```

Verifique a saúde:

```bash
curl -f http://127.0.0.1:8000/healthz/
```

O backend usa PostgreSQL para histórico, Redis exclusivamente para distribuir mensagens ao vivo entre processos e Daphne para HTTP/WebSocket. O Compose roda migrações e `collectstatic` no início para **uma única instância do backend**; quando escalar, separe migrações em um job de implantação.

No HAProxy:

- Faça a terminação TLS e encaminhe HTTP + WebSocket (`Upgrade`/`Connection`) para o backend.
- Ajuste `timeout tunnel` para as sessões WebSocket e encaminhe `Authorization` sem removê-lo.
- Sob um proxy de confiança, substitua/remova cabeçalhos `X-Forwarded-Proto` enviados pelo cliente e defina `X-Forwarded-Proto: https` no proxy.
- Restrinja o endpoint `/ws/ingest/` à rede e aos dispositivos autorizados, além do Bearer token; mantenha o Daphne fora da internet.
- Configure no Django `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` e as opções de proxy de `.env`.

No WSL, envie ao serviço real:

```bash
export TELEMETRY_TOKEN='MESMO_SEGREDO_CONFIGURADO_NO_BACKEND'
export TELEMETRY_UPSTREAM_URL='wss://SEU_HOST_INTERNO/ws/ingest/'
export TELEMETRY_CA_FILE='/caminho/para/sua-ca.pem' # somente se usa CA privada
python main.py
```

Use DNS ou IP no certificado de TLS compatível com o `TELEMETRY_UPSTREAM_URL`. **Não desative validação TLS**. O token do `telemetry-agent` tem que ser idêntico ao do backend e `TELEMETRY_AGENT_ID` deve corresponder a `wsl-assetto-agent` (ou ser alterado nos dois lados).

## API REST

A API privada não aceita Bearer token do agente: usa sessão/cookie Django e exige usuário `is_staff`. Nas requisições POST pelo frontend inclua o token CSRF exigido pelo Django. Após login em `/admin/login/`, acesse pelo mesmo domínio. Para compartilhamento local, o frontend oferece `/visao-publica`; essa área usa somente as rotas com prefixo `/api/public/` e o WebSocket `/ws/public/`, sem conta, sem login e sem permissão de escrita. A ingestão `/ws/ingest/` continua exigindo `TELEMETRY_TOKEN`.

| Método e caminho | Descrição |
|---|---|
| `GET /api/sessions/` | Capturas ordenadas pela última amostra; inclui `car_visual` quando o bridge encontrou metadados do carro |
| `GET /api/sessions/<UUID>/` | Metadados da captura |
| `GET /api/sessions/<UUID>/samples/?after=-1&limit=250` | Página sequencial de telemetria para 2D/3D |
| `GET /api/sessions/<UUID>/track-map/` | Linha completa ou overview da pista extraído pelo bridge, quando uma linha AI, `map.png`/JPEG ou `outline.png` foi encontrado |
| `GET /api/sessions/<UUID>/analysis/` | Estatísticas globais e eventos na janela recente |
| `GET /api/sessions/<UUID>/analysis/compare/?reference=<OUTRO_UUID>` | Distância geométrica até uma trajetória de referência gravada |
| `GET /api/learning/topics/` | Temas de exercícios disponíveis |
| `GET /api/sessions/<UUID>/exercise/?topic=displacement&a=1&b=50` | Valores e resultado; sem resolução |
| `GET /api/sessions/<UUID>/exercise/?topic=displacement&a=1&b=50&reveal=1` | Resolução passo a passo |
| `POST /api/sessions/<UUID>/exercise/check/` | Conferir resultado escrito à mão (JSON) |

Exemplo de conferência:

```json
{"topic":"combination","a":1,"b":50,"answer":{"a":1.5,"b":-3.25}}
```

As alternativas de `topic` incluem `displacement`, `combination`, `determinant`, `basis_dimension`, `subspace`, `affine_subspace`, `gauss` e `inverse`. Esses são **exercícios iniciais**, não a implementação integral das 16 aulas. Alguns exigem escolher instantes de direções suficientemente diferentes.

### WebSocket do dashboard

O navegador (usuário `is_staff` logado, com Origin permitido) pode se conectar em:

```
wss://SEU_HOST/ws/sessions/<UUID>/live/
```

Receberá lotes `telemetry.samples` com a sequência, timestamp, velocidade, RPM, pedais, direção e posição/velocidade mundiais. O backend publica todas as amostras *novas* de cada lote para o frontend poder interpolar o movimento do carro, mesmo recebendo os lotes a cada ~200 ms. Se perder a conexão, retome pelo endpoint REST com `after=<ultima_sequence>`.

O modo público usa o mesmo formato de mensagens em:

```
ws://SEU_HOST/ws/public/sessions/<UUID>/live/
```

e replica as leituras REST com `/api/public/`.

## Matemática e análise — limites explícitos

- `analysis` detecta **mudanças rápidas de acelerador/volante** com limiares provisórios e registra velocidade/RPM; **não afirma a causa de um acidente**.
- `analysis/compare` usa o menor afastamento em X/Z até uma polilinha de outra captura **na mesma pista**. Não sincroniza tempo/progresso, não incorpora RPM na referência e **não demonstra a melhor trajetória para drift**.
- `learning` usa vetores X/Z em coordenadas globais da telemetria, arredondados para problemas manuais. Para determinar inclinação lateral, heading, sideslip e trajetória fisicamente admissível será necessário validar convenções e dados reais do Assetto Corsa.
- Para séries de alta frequência, a tabela cresce rapidamente. Planeje retenção e arquivo em Parquet antes de sessões longas; não está automatizado neste MVP.

## Testes

```bash
cd ~/drift-telemetry-lab/backend
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest -q tests
```

Os testes puros de normalização e álgebra podem ser executados sem Django; os testes de WebSocket/ORM exigem a instalação completa e o banco de teste configurado. No primeiro deployment, verifique o contrato do agente e a persistência com o mock/gerador do projeto anterior antes de expor o serviço à LAN.
