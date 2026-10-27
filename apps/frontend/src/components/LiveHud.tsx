import type { ReactNode } from 'react';
import { Activity, Gauge, RotateCcw, Zap } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { formatNumber, gearLabel, radiansToDegrees } from '../lib/telemetry';
import { useLiveInterpolatedSample } from '../modules/telemetry/useLiveInterpolatedSample';
import type { TelemetrySample } from '../lib/types';

function Metric({ label, value, suffix, icon }: { label: string; value: string; suffix: string; icon: ReactNode }) {
  return <div className="metric"><div className="metric-label">{icon} {label}</div><div className="metric-line"><strong>{value}</strong><span>{suffix}</span></div></div>;
}
function PedalBar({ name, value, color }: { name: string; value: number; color: string }) {
  const pct = Math.min(100, Math.max(0, value * 100));
  return <div className="pedal-row"><span>{name}</span><div className="progress-track"><div style={{ width: `${pct}%`, background: color }} /></div><strong>{Math.round(pct)}%</strong></div>;
}
export function DriverControls({ sample }: { sample: TelemetrySample }) {
  return <div className="pedal-list"><PedalBar name="Acelerador" value={sample.throttle} color="#0db7a5" /><PedalBar name="Freio" value={sample.brake} color="#e56e6e" /><PedalBar name="Embreagem" value={sample.clutch} color="#61a8ff" /></div>;
}
export function LiveHud() {
  const { cursorSample, samples, isFollowing, demo } = useApp();
  const liveSample = useLiveInterpolatedSample(samples, isFollowing && !demo);
  const s = liveSample || cursorSample;
  if (!s) return null;
  return (
    <>
      <div className="metrics-grid">
        <Metric label="VELOCIDADE" value={formatNumber(s.speed_kmh, 1)} suffix="km/h" icon={<Gauge size={15} />} />
        <Metric label="ROTAÇÃO" value={formatNumber(s.rpm, 0)} suffix="rpm" icon={<RotateCcw size={15} />} />
        <Metric label="MARCHA" value={gearLabel(s.gear)} suffix="" icon={<Zap size={15} />} />
        <Metric label="VOLANTE" value={formatNumber(radiansToDegrees(s.steer_angle_rad), 1)} suffix="°*" icon={<Activity size={15} />} />
      </div>
    </>
  );
}

export function LiveDriverControls() {
  const { cursorSample, samples, isFollowing, demo } = useApp();
  const liveSample = useLiveInterpolatedSample(samples, isFollowing && !demo);
  const sample = liveSample || cursorSample;
  return sample ? <DriverControls sample={sample} /> : null;
}
