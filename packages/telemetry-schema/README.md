# telemetry-schema

Contrato de rede v1 compatível com `apps/ac-bridge` (aqui `ac-bridge`), `telemetry-agent/normalizer.py` e `backend/telemetry/validators.py` existentes.

As amostras possuem `stream_id` UUID, `sequence` inteiro, `received_at_unix_ns` e objeto `telemetry`, com `timestamp_unix_ns`, `rpm`, `gear`, `speed_kmh`, `speed_mps`, `position_world_m` etc.

- `validate_frame` aplica validação e normaliza somente o par km/h ↔ m/s, não interpreta eixos/ângulos físicos.
- `validate_sample`, `validate_batch` e `validate_ack` verificam envelopes e confirmam que ACK é integral antes de apagar buffers.
- `new_batch` é helper para testes, não substitui o transporte com persistência do agente.
- Campos opcionais **não foram acrescentados** ao protocolo, para não quebrar o código existente. Para extensões futuras, versionar o contrato.

Instale com `pip install -e packages/telemetry-schema` a partir da raiz.

O arquivo `src/telemetry_schema/schemas/telemetry-v1.schema.json` oferece um contrato JSON Schema portável para outras stacks; `load_json_schema_v1()` o lê do wheel. JSON Schema valida estrutura e limites, mas não a consistência numérica `speed_kmh / 3.6 ≈ speed_mps` nem as duplicações de lote: para isso use `validation.py`.
