import type { DamageZones, TelemetrySample, Vec3 } from './types';

export const MAX_SAMPLES_IN_MEMORY = 3000;

export function isVec3(v: unknown): v is Vec3 {
  return Array.isArray(v) && v.length === 3 && v.every((x) => typeof x === 'number' && Number.isFinite(x));
}

function damageZones(value: unknown): DamageZones {
  if (Array.isArray(value) && value.length === 5 && value.every((x) => typeof x === 'number' && Number.isFinite(x))) {
    return value as DamageZones;
  }
  return [0, 0, 0, 0, 0];
}

/** Ignore malformed messages without crashing the UI; the server already validates the source. */
export function normalizeFrame(input: unknown): TelemetrySample | null {
  if (!input || typeof input !== 'object') return null;
  const v = input as Record<string, unknown>;
  const numeric = ['sequence', 'speed_kmh', 'rpm', 'gear', 'throttle', 'brake',
    'clutch', 'steer_angle_rad', 'heading_rad'];
  if (!numeric.every((key) => typeof v[key] === 'number' && Number.isFinite(v[key]))) return null;
  if (!isVec3(v.position_world_m) || !isVec3(v.velocity_world_mps)) return null;
  let sampled = typeof v.sampled_at === 'string' ? v.sampled_at : '';
  if (!sampled && typeof v.timestamp_unix_ns === 'number') {
// Sub-millisecond precision is unnecessary in the UI; the server uses ns internally.
    sampled = new Date(v.timestamp_unix_ns / 1e6).toISOString();
  }
  if (!sampled || Number.isNaN(Date.parse(sampled))) return null;
  return {
    sequence: v.sequence as number,
    sampled_at: sampled,
    received_at: typeof v.received_at === 'string' ? v.received_at : undefined,
    speed_kmh: v.speed_kmh as number,
    speed_mps: typeof v.speed_mps === 'number' ? v.speed_mps : (v.speed_kmh as number) / 3.6,
    rpm: v.rpm as number,
    gear: v.gear as number,
    throttle: v.throttle as number,
    brake: v.brake as number,
    clutch: v.clutch as number,
    steer_angle_rad: v.steer_angle_rad as number,
    heading_rad: v.heading_rad as number,
    pitch_rad: typeof v.pitch_rad === 'number' ? v.pitch_rad : undefined,
    roll_rad: typeof v.roll_rad === 'number' ? v.roll_rad : undefined,
    position_world_m: v.position_world_m,
    velocity_world_mps: v.velocity_world_mps,
    car_damage: damageZones(v.car_damage),
    completed_laps: typeof v.completed_laps === 'number' ? v.completed_laps : undefined,
  };
}

/** Sort, remove duplicate sequences, and limit tab memory use. */
export function mergeSamples(
  oldValues: TelemetrySample[], incoming: TelemetrySample[], limit = MAX_SAMPLES_IN_MEMORY,
): TelemetrySample[] {
  if (incoming.length === 0) return oldValues;
  const bySeq = new Map<number, TelemetrySample>();
  for (const item of oldValues) bySeq.set(item.sequence, item);
  for (const item of incoming) bySeq.set(item.sequence, item);
  return [...bySeq.values()].sort((a, b) => a.sequence - b.sequence).slice(-limit);
}

export function nearestBySequence(samples: TelemetrySample[], sequence: number | null): TelemetrySample | null {
  if (!samples.length) return null;
  if (sequence === null) return samples[samples.length - 1];
  let low = 0, high = samples.length - 1;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if (samples[mid].sequence < sequence) low = mid + 1;
    else high = mid;
  }
  const current = samples[low];
  const prev = samples[Math.max(0, low - 1)];
  return Math.abs(prev.sequence - sequence) < Math.abs(current.sequence - sequence) ? prev : current;
}

export function sampleTimeSeconds(s: TelemetrySample): number { return Date.parse(s.sampled_at) / 1000; }
export function radiansToDegrees(rad: number): number { return rad * 180 / Math.PI; }
export function gearLabel(gear: number): string { return gear < 0 ? 'R' : gear === 0 ? 'N' : String(gear); }
export function formatNumber(value: number | null | undefined, digits = 1): string {
  return typeof value === 'number' && Number.isFinite(value)
    ? value.toLocaleString('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits })
    : '—';
}
/** Downsample for rendering only; calculations preserve in-memory samples. */
export function downsample<T>(values: T[], maxCount = 900): T[] {
  if (values.length <= maxCount) return values;
  const stride = (values.length - 1) / (maxCount - 1);
  return Array.from({ length: maxCount }, (_, i) => values[Math.round(i * stride)]);
}
