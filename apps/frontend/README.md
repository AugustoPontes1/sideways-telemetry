# Drift Telemetry Lab — Frontend (React, Plotly, Three.js)

Interface **TypeScript/React** para o backend Django existente. Recebe amostras históricas por REST e novos lotes pelo WebSocket autenticado por **cookie de sessão Django**. O Bearer do Telemetry Agent **nunca** chega ao navegador.

## Estrutura

```text
frontend/
├── src/
│   ├── components/                 # Layout, HUD, controles e linha do tempo
│   ├── context/AppContext.tsx      # Sessão ativa, modo demo, cursor global
│   ├── lib/                        # Contratos da API, tipos, normalização, demo
│   ├── modules/
│   │   ├── telemetry/              # WebSocket/REST e gráficos temporais
│   │   ├── cartesian-2d/           # Trajetória XY (X/Z do AC) com Plotly
│   │   ├── trajectory-3d/          # Cena React Three Fiber, modelo e replay
│   │   └── math-lab/               # Exercícios, conferência, solução opcional
│   ├── pages/                      # Visão geral + quatro páginas
│   ├── App.tsx
│   └── main.tsx
├── tests/                          # Vitest (utilitários puros)
├── deploy/nginx.conf              # Proxy de produção na mesma rede do Django
├── Dockerfile
├── vite.config.ts
└── package.json
```

## Desenvolvimento no WSL Ubuntu

Requer **Node 22.12+** (ou versão compatível com Vite 7) e npm. O sistema não precisa executar dentro do Windows; basta acessar Django via rede.

```bash
cd ~/drift-telemetry-lab/apps/frontend
cp .env.example .env
npm install
npm run dev
```

Abra `http://127.0.0.1:5173` localmente ou `http://<ip-lan-do-windows>:5173` em outra máquina. O app inicia em modo ao vivo e carrega sessões do Django. Ative **DEMO** quando quiser testar a interface sem Assetto Corsa.

Para se conectar ao backend de desenvolvimento do WSL:

```bash
# Terminal 1, WSL: backend Django
cd ~/drift-telemetry-lab/backend
source .venv/bin/activate
export DJANGO_DEBUG=1
export DJANGO_CSRF_TRUSTED_ORIGINS='http://127.0.0.1:5173'
python manage.py runserver 127.0.0.1:8000

# Terminal 2, WSL: frontend
cd ~/drift-telemetry-lab/apps/frontend
npm run dev
```

1. Entre por `http://127.0.0.1:5173/admin/login/?next=/`, usando **usuário Django `is_staff`**. O Django cria o cookie de sessão e CSRF na mesma origem visível ao navegador.
2. Volte para a página, confirme que DEMO está desativado e escolha uma sessão.
3. Inicie AC Bridge no Windows, Telemetry Agent no WSL e envie ao backend conforme os respectivos READMEs. O bridge atualiza os IDs do carro, pista e layout em tempo real a partir da memória compartilhada; enquanto o jogo carrega, usa `Documents\\Assetto Corsa\\cfg\\race.ini` como fallback. Para obter o mapa completo e os metadados de mods, ele procura automaticamente `content/tracks/<track>/ai/fast_lane.ai`, `ideal_line.ai`, `map.png`/JPEG, `ui/outline.png` e `data/map.ini` em todas as bibliotecas Steam detectadas, além de `content/cars/<car>/ui/ui_car.json`. Defina `AC_ROOT` apenas se a instalação estiver fora desses locais.

Para compartilhar os dados sem criar conta ou fazer login, abra `/visao-publica`. Essa rota oferece as mesmas páginas de visão geral, telemetria, plano 2D, replay 3D e Laboratório matemático usando endpoints públicos somente para leitura; a ingestão, o `/admin` e as rotas privadas continuam protegidos.

Para renderizar a malha e a pintura exatas do carro no navegador, instale uma vez no Windows o conversor MIT diretamente da fonte. Como o repositório está no WSL, execute a instalação a partir de uma pasta local do Windows, não de `\\wsl.localhost\...`: `Set-Location C:\Temp; py -3 -m pip install "https://github.com/semiloker/assetto-corsa-gltf/archive/refs/heads/main.zip"`. O bridge escolhe automaticamente o KN5 de maior detalhe, a pasta do carro modificado e o `CAR_0/SKIN` ativo, converte a combinação para um GLB específico no primeiro acesso e serve `/car-models/<ID>.glb?skin=<SKIN>` na porta `8766`; o Vite encaminha essa rota. Sem o conversor instalado, a interface mantém a miniatura procedural e registra o motivo no log do bridge.

KN5 protegido por CSP ou corrompido não pode ser extraído pelo conversor. O bridge tenta LODs alternativos quando existem; se todos falharem, a interface usa a miniatura procedural sem quebrar o proxy.

O proxy do Vite (`vite.config.ts`) encaminha `/api/`, `/admin/`, `/static/`, `/healthz/` e `/ws/` para o Django. Se Django rodar em outra VM, configure `VITE_BACKEND_TARGET=http://IP_INTERNO:8000` **somente para desenvolvimento em rede confiável**, atualize `DJANGO_ALLOWED_HOSTS` e permita a origem dev em `DJANGO_CSRF_TRUSTED_ORIGINS`. Nunca exponha Django debug ou o backend HTTP sem proteção na internet.

## APIs consumidas (contrato real do backend)

- `GET /api/sessions/` — lista de capturas de telemetria.
- `GET /api/sessions/{UUID}/samples/?after=...&limit=...` — amostras paginadas.
- `GET /api/sessions/{UUID}/track-map/` — mapa completo da pista, quando o bridge encontrou uma linha AI ou o overview `map.png`/JPEG/`outline.png` instalado.
- `GET /api/sessions/{UUID}/analysis/` — estatísticas e eventos de entrada.
- `GET /api/sessions/{UUID}/analysis/compare/?reference={UUID}` — distância geométrica à referência gravada.
- `GET /api/learning/topics/` — temas disponíveis (8 no backend atual).
- `GET /api/sessions/{UUID}/exercise/?topic=...&a=...&b=...` — valores + resultado, **sem solução**.
- `GET /api/sessions/{UUID}/exercise/?...&reveal=1` — passos da resolução, apenas após o usuário solicitar.
- `POST /api/sessions/{UUID}/exercise/check/` — confere JSON do aluno, com `X-CSRFToken` obtido do cookie Django.
- `WS /ws/sessions/{UUID}/live/` — lotes `telemetry.samples`; usa cookie de login e verificação de Origin.

O cliente sempre exibe o resultado esperado no Modo Estudo, conforme sua preferência. Por padrão, o código não solicita `solution` ao backend. Para conferir uma resposta, use JSON válido: `2.5`, `true`, `[2,-1]` ou `{"a":2,"b":-1}`.

## Modos de visualização

**Telemetria:** séries temporais de acelerador, freio, embreagem, velocidade, RPM e direção. Clicar em um ponto move o cursor compartilhado com o replay e a trajetória.

**2D:** projeção horizontal da posição mundial em X/Z (X no eixo horizontal do gráfico, Z no vertical), escala 1:1 e vetor velocidade escalado para visualização. Quando disponível, mostra a linha completa de `fast_lane.ai`/`ideal_line.ai` da pista e sobrepõe a sessão atual apenas para comparação; se o mod não tiver linha AI, mostra o `map.png`/JPEG/`outline.png` instalado e a sessão capturada sobre ele. O marcador pulsante do carro usa `data/map.ini` (`WIDTH`, `HEIGHT`, `X_OFFSET` e `Z_OFFSET`) quando disponível, mantendo a posição correta no mapa durante a reprodução ao vivo. Exibe uma trajetória de referência gravada **na mesma pista** se disponível. Distância e limitações são obtidas do backend.

**3D:** posição X/Y/Z e `heading_rad` brutos, malha GLB convertida automaticamente do KN5 de maior detalhe com a `CAR_0/SKIN` ativa quando o conversor está instalado ou miniatura geométrica adaptada ao identificador detectado, mapa completo da pista quando uma linha AI ou overview instalado está disponível, câmera orbital, linha temporal e replay 0,5× a 4×. O bridge lê `ui/ui_car.json`, `content/cars/<car>/skins/<skin>` e os arquivos de qualquer carro instalado, inclusive mods, e envia o ID, nome, marca e skin ao backend. O Shared Memory fornece o identificador do carro; a configuração da sessão fornece a livery ativa.

**Danos:** o Shared Memory original do Assetto Corsa fornece cinco valores agregados em `carDamage`: frente, traseira, lado esquerdo, lado direito e centro. O painel converte valores normalizados ou percentuais para exibição e mantém valores brutos acima de 100 como pontos, mas não inventa dano de peça, suspensão, pneu ou motor que não esteja no contrato de telemetria.

**Álgebra Linear:** exercícios de deslocamento, combinação linear, determinante, subespaços, posto/dimensão, sistema de Gauss e inversa, baseados nos temas existentes no backend. No modo DEMO há somente três temas locais, sempre rotulados como fictícios.

**Limitações físicas:**

- O eixo `heading_rad` e o sinal do volante requerem validação de convenção no Assetto Corsa real; a orientação 3D ainda pode precisar de ajuste por carro/mod.
- A linha tracejada é **referência gravada/simulada**. Não há cálculo de trajetória ideal a partir do RPM. Otimização exigiria aderência, limites da pista, velocidade, estado e um modelo validado.
- O backend identifica variações rápidas de controles, mas não diagnostica automaticamente por que houve rodadas ou batidas.
- O dataset de demonstração é sintético; nenhum resultado de DEMO representa uma sessão real.
- A janela local retém até **3.000 amostras**. A API REST atual permite navegar com `after` mas não disponibiliza busca por tempo nem amostragem por intervalo; replays completos muito longos exigirão melhorias no backend.
- O cliente reconecta o WS automaticamente e reconcilia a sequência pelo REST a cada 12s. Não há garantia de entrega em tempo real pelo WebSocket; o histórico persistido é a fonte de verdade.

## Testes e build

```bash
npm run typecheck
npm test
npm run build
npm run preview
```

`npm install` cria `package-lock.json`; **versione o lockfile** para builds reproduzíveis e, após isso, troque o passo do Dockerfile de `npm install` para `npm ci`.

## Produção no homelab

O frontend gera arquivos estáticos via Vite. O `Dockerfile` usa um estágio Node para build e **Nginx** para servir a SPA e encaminhar backend e WebSocket na **mesma origem**.

Adicione o exemplo `deploy/compose.service.example.yaml` **como serviço dentro de `backend/compose.yaml`**, na rede `internal` já existente. Então execute na pasta `backend`:

```bash
docker compose up -d --build
```

O exemplo publica Nginx em `127.0.0.1:8080`. Configure o HAProxy **na mesma VM**, encaminhando o domínio do dashboard para `127.0.0.1:8080`, inclusive `/ws/ingest/`, `/ws/sessions/`, `/api/`, `/admin/` e `/static/`. TLS deve terminar no HAProxy. Se HAProxy estiver em outra VM, altere o bind e permita acesso somente a partir dela via firewall. Configure Django `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://DOMINIO` e `DJANGO_TRUST_PROXY_PROTO=1`, com HAProxy removendo e recriando **X-Forwarded-Proto** (não confie no cabeçalho enviado pelo cliente). O Nginx deve estar acessível só pelo proxy de confiança.

O Dockerfile usa `npm install` enquanto não há lockfile no pacote gerado aqui. Para versão de produção, gere e versione `package-lock.json` depois de instalar dependências na sua máquina.

## Validação antes de usar a telemetria real

1. Confira que acelerador, freio e embreagem variam de 0 a 1 e reagem no sentido esperado.
2. Confira que as coordenadas X/Z descrevem o plano horizontal e que `heading_rad` corresponde à orientação na mesma convenção do modelo 3D.
3. Grave duas capturas controladas da mesma pista e compare as trajetórias. Comparação é geométrica, não temporal.
4. Confirme que a sessão no Django corresponde ao `stream_id` do bridge (uma troca de pista no mesmo stream não cria outra `DrivingSession` automaticamente).
5. Rode os testes do backend separadamente; testes isolados do frontend não substituem testes reais com Django e CSP/proxy.
