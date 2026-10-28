/** DETERMINISTIC, FICTIONAL dataset. This is not real telemetry analysis. */
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
    car_damage: [0, 0, 0, 0, 0],
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
  { id: 'subspace', title: 'Subespaço gerado por uma direção', lessons: [12, 13, 15] },
  { id: 'basis_dimension', title: 'Base e dimensão gerada por dois vetores', lessons: [16, 17, 18] },
  { id: 'determinant', title: 'Determinante de vetores velocidade', lessons: [8, 16] },
];

const r3 = (v: number) => Math.round(v * 1000) / 1000;
export function generateDemoExercise(topic: string, a: number, b: number, reveal = false): Exercise {
  const p1 = demoSamples[a]?.position_world_m ?? demoSamples[0].position_world_m;
  const p2 = demoSamples[b]?.position_world_m ?? demoSamples[1].position_world_m;
  const velocity = demoSamples[a]?.velocity_world_mps ?? demoSamples[0].velocity_world_mps;
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
      ...(reveal ? { solution: ['Na base canônica, a(1,0)+b(0,1)=(a,b).', `Igualando a (${r3(dx)},${r3(dz)}), a=${r3(dx)} e b=${r3(dz)}.`, `Resposta final: a=${r3(dx)} e b=${r3(dz)}.`] } : {}) };
  }
  if (topic === 'subspace') {
    const direction = [r3(velocity[0]), r3(velocity[2])];
    const multiples = [-1, 0, 1, 2].map((t) => ({
      t, vector: [r3(t * direction[0]), r3(t * direction[1])],
    }));
    const calculation = {
      direction_vector: direction,
      unit: 'm/s · velocidade projetada nos eixos X/Z',
      norm: r3(Math.hypot(...direction)),
      angle_deg_from_x: r3(Math.atan2(direction[1], direction[0]) * 180 / Math.PI),
      parametric_form: `W = {t·(${direction[0]}, ${direction[1]}) | t ∈ ℝ}`,
      multiples,
      basis: [direction],
    };
    const expected_result = { is_subspace: true, dimension: 1 };
    return { ...base, question: 'W=span{v}. Mostre que W é um subespaço de R² e encontre sua dimensão.',
      inputs: { v: direction, W: `span{v} = {t·(${direction[0]}, ${direction[1]}) | t ∈ ℝ}` }, expected_result, calculation,
      ...(reveal ? { solution: [
        `Os valores do exemplo dão v=(${direction[0]}, ${direction[1]}) m/s, com ||v||=${calculation.norm}; como v≠(0,0), ele é não nulo.`,
        `W=span{v}={t·(${direction[0]}, ${direction[1]}) | t∈ℝ}: cada ponto é um múltiplo de v.`,
        'Vetor zero: 0·v=(0,0), então (0,0)∈W.',
        `Exemplo numérico: a=2 e b=-1 dão u=2·v=(${multiples[3].vector[0]}, ${multiples[3].vector[1]}) e w=-1·v=(${multiples[0].vector[0]}, ${multiples[0].vector[1]}).`,
        `Soma: u+w=(${multiples[3].vector[0]}, ${multiples[3].vector[1]})+(${multiples[0].vector[0]}, ${multiples[0].vector[1]})=(${multiples[2].vector[0]}, ${multiples[2].vector[1]})=1·v.`,
        `Com k=3, k·u=3·(${multiples[3].vector[0]}, ${multiples[3].vector[1]})=(${r3(6 * direction[0])}, ${r3(6 * direction[1])})=6·v.`,
        'Esses valores ilustram a regra; para quaisquer a,b,k reais, u+w=(a+b)·v e k·u=(ka)·v.',
        `Dimensão é a quantidade de vetores de uma base. Como v é não nulo, B={v}=(${direction[0]}, ${direction[1]}) é uma base com 1 vetor.`,
        'Resposta final: W é subespaço, a base é {v} e dimensão(W)=1.',
      ] } : {}) };
  }
  if (topic === 'basis_dimension') {
    const firstVelocity = demoSamples[a]?.velocity_world_mps ?? demoSamples[0].velocity_world_mps;
    const secondVelocity = demoSamples[b]?.velocity_world_mps ?? demoSamples[1].velocity_world_mps;
    const v1 = [r3(firstVelocity[0]), r3(firstVelocity[2])];
    const v2 = [r3(secondVelocity[0]), r3(secondVelocity[2])];
    const determinant = r3(v1[0] * v2[1] - v1[1] * v2[0]);
    const firstNorm = Math.hypot(...v1), secondNorm = Math.hypot(...v2);
    const dimension = Math.max(firstNorm, secondNorm) < 1e-8
      ? 0 : Math.min(firstNorm, secondNorm) < 1e-8 || Math.abs(determinant) <= 1e-6 * firstNorm * secondNorm ? 1 : 2;
    const basis = dimension === 2 ? [v1, v2] : dimension === 1 ? [firstNorm >= secondNorm ? v1 : v2] : [];
    const calculation = {
      sample_sequences: [a, b], sample_speed_mps: [r3(demoSamples[a]?.speed_mps ?? firstNorm), r3(demoSamples[b]?.speed_mps ?? secondNorm)],
      v1, v2, matrix: [v1, v2], determinant, basis, dimension, numeric_tolerance: 1e-6,
    };
    const expected_result = dimension;
    return { ...base, question: 'Estime a dimensão do subespaço gerado por estes dois vetores no plano XZ.',
      inputs: { v1, v2, numeric_tolerance: 1e-6 }, expected_result, calculation,
      ...(reveal ? { solution: [
        `v1 vem da amostra #${a}: (${v1[0]}, ${v1[1]}) m/s; v2 vem da amostra #${b}: (${v2[0]}, ${v2[1]}) m/s.`,
        `A=[[${v1[0]},${v1[1]}],[${v2[0]},${v2[1]}]].`,
        `det(A)=(${v1[0]})(${v2[1]})-(${v1[1]})(${v2[0]})=${determinant}.`,
        `A base numérica é ${basis.length ? basis.map((vector) => `(${vector.join('; ')})`).join(', ') : '∅'}; ela contém ${basis.length} vetor(es) independente(s).`,
        `Resposta final: dimensão(span{v1,v2})=${dimension}.`,
      ] } : {}) };
  }
  if (topic === 'determinant') {
    const v1 = demoSamples[a].velocity_world_mps, v2 = demoSamples[b].velocity_world_mps;
    const matrix = [[r3(v1[0]),r3(v1[2])], [r3(v2[0]),r3(v2[2])]];
    const expected_result = r3(matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]);
    return { ...base, question: 'Calcule det(A) da matriz formada pelas velocidades XZ.',
      inputs: { matrix }, expected_result,
      ...(reveal ? { solution: ['Para A=[[a,b],[c,d]], det(A)=ad−bc.', `Substituindo os elementos: det(A)=${expected_result}.`, `Resposta final: det(A)=${expected_result}.`] } : {}) };
  }
  const expected_result = { delta_x_m: r3(dx), delta_z_m: r3(dz), distance_horizontal_m: r3(Math.hypot(dx, dz)) };
  return { ...base, question: 'Calcule o deslocamento entre dois instantes no plano XZ.',
    inputs: { P1_xz_m: [r3(p1[0]), r3(p1[2])], P2_xz_m: [r3(p2[0]), r3(p2[2])] }, expected_result,
    ...(reveal ? { solution: [`P2−P1=(${r3(dx)},${r3(dz)}) m.`, `Módulo = √(Δx²+Δz²) = ${expected_result.distance_horizontal_m} m.`, `Resposta final: Δ=(${r3(dx)},${r3(dz)}) m e ||Δ||=${expected_result.distance_horizontal_m} m.`] } : {}) };
}
