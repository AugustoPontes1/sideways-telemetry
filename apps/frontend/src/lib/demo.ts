/** Dataset DETERMINÍSTICO E FICTÍCIO. Não é análise de telemetria real. */
import type { DrivingSession, TelemetrySample, Exercise, LearningTopic, SessionAnalysis } from './types';

export const DEMO_ID = '00000000-0000-4000-8000-000000000001';
const start = '2026-10-23T10:00:00.000Z';

export const demoSession: DrivingSession = {
  stream_id: DEMO_ID,
  agent_id: 'simulated-demo', car: 'Coupé RWD (exemplo)', track: 'Treino de drift (fictício)',
  session_type: 0, sample_count: 420, max_sequence: 419,
  first_sample_at: start, last_sample_at: new Date(Date.parse(start) + 419 * 50).toISOString(),
  created_at: start, updated_at: start,
};

export const demoSamples: TelemetrySample[] = Array.from({ length: 420 }, (_, i) => {
  const t = i / 20;
  const angle = t * 0.25;
  const radius = 32 + 1.8 * Math.sin(t * 0.65);
  const x = radius * Math.sin(angle);
  const z = radius * (1 - Math.cos(angle));
  const dx = radius * Math.cos(angle) * 0.25 + 1.17 * Math.cos(t * .65) * Math.sin(angle);
  const dz = radius * Math.sin(angle) * 0.25 + 1.17 * Math.cos(t * .65) * (1 - Math.cos(angle));
  const speed = Math.hypot(dx, dz);
  const throttle = Math.max(0, Math.min(1, .55 + .22 * Math.sin(t * 1.35)));
  return {
    sequence: i,
    sampled_at: new Date(Date.parse(start) + i * 50).toISOString(),
    speed_kmh: speed * 3.6,
    speed_mps: speed,
    rpm: Math.round(3300 + 1350 * throttle + 550 * Math.sin(t * 0.6)),
    gear: t < 2 ? 1 : 2,
    throttle,
    brake: .02 + Math.max(0, -.12 * Math.sin(t * .7)),
    clutch: t < 2.2 ? .2 : 0,
    steer_angle_rad: -.2 - .55 * Math.sin(t * .28),
    heading_rad: angle + .4,
    position_world_m: [x, 0.1 + .05 * Math.sin(t), z],
    velocity_world_mps: [dx, 0, dz],
    completed_laps: 0,
  };
});

export const demoAnalysis: SessionAnalysis = {
  stream_id: DEMO_ID,
  car: demoSession.car,
  track: demoSession.track,
  stats: {
    count: demoSamples.length,
    speed_min_kmh: Math.min(...demoSamples.map((s) => s.speed_kmh)),
    speed_max_kmh: Math.max(...demoSamples.map((s) => s.speed_kmh)),
    speed_avg_kmh: demoSamples.reduce((n, s) => n + s.speed_kmh, 0) / demoSamples.length,
    rpm_min: Math.min(...demoSamples.map((s) => s.rpm)),
    rpm_max: Math.max(...demoSamples.map((s) => s.rpm)),
    throttle_avg: demoSamples.reduce((n, s) => n + s.throttle, 0) / demoSamples.length,
  },
  events: [
    { kind: 'throttle_change', sequence: 180, rate: 1.7, unit: 'fração/s', label: 'Evento fictício para testar a interface' },
    { kind: 'steering_change', sequence: 288, rate: 2.4, unit: 'rad/s', label: 'Evento fictício para testar a interface' },
  ],
  event_window_samples: demoSamples.length,
  interpretation: 'Simulação ilustrativa: não representa um diagnóstico da sua pilotagem.',
};

export const demoTopics: LearningTopic[] = [
  { id: 'displacement', title: 'Deslocamento no plano XZ', lessons: [12] },
  { id: 'combination', title: 'Combinação linear na base canônica', lessons: [15, 17] },
  { id: 'determinant', title: 'Determinante de vetores velocidade', lessons: [8, 16] },
];

const r3 = (v: number) => Math.round(v * 1000) / 1000;
export function generateDemoExercise(topic: string, a: number, b: number, reveal = false): Exercise {
  const p1 = demoSamples[a]?.position_world_m ?? demoSamples[0].position_world_m;
  const p2 = demoSamples[b]?.position_world_m ?? demoSamples[1].position_world_m;
  const dx = r3(p2[0]) - r3(p1[0]);
  const dz = r3(p2[2]) - r3(p1[2]);
  const base = {
    topic, title: demoTopics.find((v) => v.id === topic)?.title || topic,
    lessons: demoTopics.find((v) => v.id === topic)?.lessons || [],
    source_sequences: [a, b],
    note: 'Exercício fictício gerado no navegador. Ao sair do modo demo, usa-se o cálculo do backend.',
  };
  if (topic === 'combination') {
    const expected_result = { a: r3(dx), b: r3(dz) };
    return { ...base, question: 'Encontre a,b tais que P2−P1 = a(1,0)+b(0,1).',
      inputs: { displacement_xz_m: [r3(dx), r3(dz)], basis: [[1, 0], [0, 1]] }, expected_result,
      ...(reveal ? { solution: ['Na base canônica, a(1,0)+b(0,1)=(a,b).', `Igualando a (${r3(dx)},${r3(dz)}), a=${r3(dx)} e b=${r3(dz)}.`] } : {}) };
  }
  if (topic === 'determinant') {
    const v1 = demoSamples[a].velocity_world_mps, v2 = demoSamples[b].velocity_world_mps;
    const matrix = [[r3(v1[0]),r3(v1[2])], [r3(v2[0]),r3(v2[2])]];
    const expected_result = r3(matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]);
    return { ...base, question: 'Calcule det(A) da matriz formada pelas velocidades XZ.',
      inputs: { matrix }, expected_result,
      ...(reveal ? { solution: ['Para A=[[a,b],[c,d]], det(A)=ad−bc.', `Substituindo os elementos: det(A)=${expected_result}.`] } : {}) };
  }
  const expected_result = { delta_x_m: r3(dx), delta_z_m: r3(dz), distance_horizontal_m: r3(Math.hypot(dx, dz)) };
  return { ...base, question: 'Calcule o deslocamento entre dois instantes no plano XZ.',
    inputs: { P1_xz_m: [r3(p1[0]), r3(p1[2])], P2_xz_m: [r3(p2[0]), r3(p2[2])] }, expected_result,
    ...(reveal ? { solution: [`P2−P1=(${r3(dx)},${r3(dz)}) m.`, `Módulo = √(Δx²+Δz²) = ${expected_result.distance_horizontal_m} m.`] } : {}) };
}
