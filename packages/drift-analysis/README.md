# drift-analysis

Instalação: `pip install -e packages/drift-math -e packages/drift-analysis`.

- `drift_detector.analyze_drift`: possíveis intervalos de deslizamento sustentado, exige `yaw_calibrated=True` explicitamente. Calibre orientação X/Z e sinal do yaw em uma sessão real primeiro.
- `steering_analysis.steering_events`: taxas elevadas de comando e inversões de direção.
- `throttle_analysis.throttle_events`: tip-in, lift-off, troca de marcha, queda de RPM.
- `trajectory_comparison.compare_trajectories`: desvios entre duas sessões no mesmo trecho, alinhadas por distância percorrida normalizada. NÃO compara por tempo; NÃO é trajetória ideal.
- `trajectory_comparison.build_recorded_reference`: converte uma volta gravada em polilinha 3D tracejada e perfil RPM/velocidade por progresso. Não calcula trajetória ótima a partir de RPM.

Aceita dict do protocolo `telemetry-schema` (`{"telemetry": frame}`), frames normalizados puros ou dicts retornados pelo serializer REST do Django (`sampled_at`, `position_world_m`, `rpm`, etc.).

A API Django já fornecida usa serviços próprios. Os módulos são bibliotecas prontas para migração gradual; instalar o pacote, sem mudar `backend/analysis/views.py`, NÃO ativa automaticamente esses diagnósticos na API existente.

CLI demonstrativa: `python examples/analyze_session.py sessao.json --reference volta_gravada.json`. Gera `recorded_reference.json` com posições 3D, RPM e velocidade por progresso (para o tracejado do Three.js).
