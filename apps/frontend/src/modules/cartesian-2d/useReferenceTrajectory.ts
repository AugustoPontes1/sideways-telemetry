import { useEffect, useState } from 'react';
import { compareSessions, getRecentSamples } from '../../lib/api';
import { demoSamples } from '../../lib/demo';
import type { DrivingSession, TrajectoryComparison, Vec3 } from '../../lib/types';

interface ReferenceState {
  positions: Vec3[];
  metrics: TrajectoryComparison | null;
  error: string | null;
  loading: boolean;
}

const demoPositions = demoSamples.map((s, i): Vec3 => {
  const [x, y, z] = s.position_world_m;
  return [x - 1.0 * Math.sin(i / 30), y, z - 0.9 * Math.cos(i / 48)];
});

export function useReferenceTrajectory(
  current: DrivingSession | null, reference: DrivingSession | null, demo: boolean, enabled: boolean,
): ReferenceState {
  const [state, setState] = useState<ReferenceState>({ positions: [], metrics: null, error: null, loading: false });
  const currentId = current?.stream_id || '';
  const referenceId = reference?.stream_id || '';
  useEffect(() => {
    if (!enabled || !current) {
      setState({ positions: [], metrics: null, error: null, loading: false });
      return;
    }
    if (demo) {
      const deviations = demoPositions.map((v, i) => Math.hypot(v[0] - demoSamples[i].position_world_m[0], v[2] - demoSamples[i].position_world_m[2]));
      setState({ positions: demoPositions, error: null, loading: false,
        metrics: {
          evaluated_points: deviations.length,
          mean_distance_m: deviations.reduce((a, b) => a + b, 0) / deviations.length,
          max_distance_m: Math.max(...deviations),
          per_point_distance_m: deviations,
          actual_path_xz_m: demoSamples.map((s) => [s.position_world_m[0],s.position_world_m[2]]),
          reference_path_xz_m: demoPositions.map((s) => [s[0],s[2]]),
          method: 'Exemplo simulado com correspondência por índice (não é a API Django)',
          limitations: 'Referência fictícia ilustrativa; não é uma linha de drift ideal.',
          current_stream_id: currentId, reference_stream_id: 'referencia-demo',
        },
      });
      return;
    }
    if (!reference || currentId === referenceId) {
      setState({ positions: [], metrics: null, error: null, loading: false });
      return;
    }
    let valid = true;
    const controller = new AbortController();
    setState({ positions: [], metrics: null, error: null, loading: true });
    Promise.all([compareSessions(currentId, referenceId), getRecentSamples(reference, 2000, controller.signal)])
      .then(([metrics, samples]) => {
        if (valid) setState({ positions: samples.map((s) => s.position_world_m), metrics, error: null, loading: false });
      }).catch((exc: unknown) => {
        if (valid) setState({ positions: [], metrics: null, error: exc instanceof Error ? exc.message : 'Falha ao obter referência.', loading: false });
      });
    return () => { valid = false; controller.abort(); };
  }, [currentId, referenceId, demo, enabled]);
  return state;
}
