import { useEffect, useRef, useState } from 'react';
import type { TelemetrySample, Vec3 } from '../../lib/types';

const DEFAULT_RENDER_DELAY_MS = 180;

function mix(first: number, second: number, amount: number): number {
  return first + (second - first) * amount;
}

function mixVector(first: Vec3, second: Vec3, amount: number): Vec3 {
  return [mix(first[0], second[0], amount), mix(first[1], second[1], amount), mix(first[2], second[2], amount)];
}

function mixAngle(first: number, second: number, amount: number): number {
  const delta = Math.atan2(Math.sin(second - first), Math.cos(second - first));
  return first + delta * amount;
}

function interpolate(first: TelemetrySample, second: TelemetrySample, amount: number, timeMs: number): TelemetrySample {
  return {
    ...second,
    sequence: amount < 0.5 ? first.sequence : second.sequence,
    sampled_at: new Date(timeMs).toISOString(),
    speed_kmh: mix(first.speed_kmh, second.speed_kmh, amount),
    speed_mps: mix(first.speed_mps, second.speed_mps, amount),
    rpm: mix(first.rpm, second.rpm, amount),
    gear: amount < 0.5 ? first.gear : second.gear,
    throttle: mix(first.throttle, second.throttle, amount),
    brake: mix(first.brake, second.brake, amount),
    clutch: mix(first.clutch, second.clutch, amount),
    steer_angle_rad: mix(first.steer_angle_rad, second.steer_angle_rad, amount),
    heading_rad: mixAngle(first.heading_rad, second.heading_rad, amount),
    pitch_rad: first.pitch_rad === undefined || second.pitch_rad === undefined
      ? second.pitch_rad : mix(first.pitch_rad, second.pitch_rad, amount),
    roll_rad: first.roll_rad === undefined || second.roll_rad === undefined
      ? second.roll_rad : mix(first.roll_rad, second.roll_rad, amount),
    position_world_m: mixVector(first.position_world_m, second.position_world_m, amount),
    velocity_world_mps: mixVector(first.velocity_world_mps, second.velocity_world_mps, amount),
    completed_laps: amount < 0.5 ? first.completed_laps : second.completed_laps,
  };
}

function sampleAt(samples: TelemetrySample[], timeMs: number): TelemetrySample | null {
  if (!samples.length) return null;
  if (samples.length === 1) return samples[0];
  const firstTime = Date.parse(samples[0].sampled_at);
  const lastIndex = samples.length - 1;
  const lastTime = Date.parse(samples[lastIndex].sampled_at);
  if (!Number.isFinite(firstTime) || !Number.isFinite(lastTime)) return samples[lastIndex];
  if (timeMs <= firstTime) return samples[0];
  if (timeMs >= lastTime) {
    const previousTime = Date.parse(samples[lastIndex - 1].sampled_at);
    const amount = previousTime < lastTime
      ? Math.min(10, 1 + (timeMs - lastTime) / (lastTime - previousTime)) : 1;
    return interpolate(samples[lastIndex - 1], samples[lastIndex], amount, timeMs);
  }

  let low = 0;
  let high = lastIndex;
  while (low + 1 < high) {
    const middle = Math.floor((low + high) / 2);
    if (Date.parse(samples[middle].sampled_at) <= timeMs) low = middle;
    else high = middle;
  }
  const lowerTime = Date.parse(samples[low].sampled_at);
  const upperTime = Date.parse(samples[high].sampled_at);
  const amount = upperTime > lowerTime ? (timeMs - lowerTime) / (upperTime - lowerTime) : 0;
  return interpolate(samples[low], samples[high], Math.max(0, Math.min(1, amount)), timeMs);
}

export function useLiveInterpolatedSample(
  samples: TelemetrySample[], enabled: boolean, renderDelayMs = DEFAULT_RENDER_DELAY_MS,
): TelemetrySample | null {
  const samplesRef = useRef(samples);
  const clockOffsetRef = useRef<number | null>(null);
  const previousSequenceRef = useRef<number | null>(null);
  const [visualSample, setVisualSample] = useState<TelemetrySample | null>(null);
  samplesRef.current = samples;
  const latestSequence = samples.at(-1)?.sequence ?? -1;

  useEffect(() => {
    if (!enabled || latestSequence < 0) {
      clockOffsetRef.current = null;
      previousSequenceRef.current = latestSequence;
      setVisualSample(null);
      return;
    }
    if (previousSequenceRef.current !== null && latestSequence < previousSequenceRef.current) {
      clockOffsetRef.current = null;
    }
    const latest = samples.at(-1);
    const latestTime = latest ? Date.parse(latest.sampled_at) : Number.NaN;
    if (latest && Number.isFinite(latestTime)) {
      const observedOffset = performance.now() - latestTime;
      clockOffsetRef.current = clockOffsetRef.current === null
        ? observedOffset : clockOffsetRef.current * 0.85 + observedOffset * 0.15;
      setVisualSample(latest);
    }
    previousSequenceRef.current = latestSequence;
  }, [enabled, latestSequence, samples]);

  useEffect(() => {
    if (!enabled) return undefined;
    let frame = 0;
    const render = () => {
      const offset = clockOffsetRef.current;
      if (offset !== null) {
        const targetTime = performance.now() - offset - renderDelayMs;
        const next = sampleAt(samplesRef.current, targetTime);
        if (next) setVisualSample(next);
      }
      frame = requestAnimationFrame(render);
    };
    frame = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frame);
  }, [enabled, renderDelayMs]);

  return enabled ? visualSample : null;
}
