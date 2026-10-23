# Bibliotecas reutilizáveis

Os diretórios `telemetry-schema/`, `drift-math/` e `drift-analysis/` são **distribuições** Python; os imports corretos são `telemetry_schema`, `drift_math` e `drift_analysis` (nomes com underscore).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e packages/telemetry-schema -e packages/drift-math -e packages/drift-analysis
python -m pip install pytest pyyaml
pytest
```

`backend/` usa serviços já implementados; esses pacotes são testáveis independentemente e ficam instalados na imagem de `infrastructure/Dockerfile.backend`. Para habilitar novos relatórios HTTP, conecte-os gradualmente via `backend/analysis/services.py` e views existentes, sem mudar o contrato da ingestão e o ACK.
