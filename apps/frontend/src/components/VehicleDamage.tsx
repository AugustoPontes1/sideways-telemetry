import type { TelemetrySample } from '../lib/types';

const zones = [
  { key: 0, label: 'Frente', className: 'front' },
  { key: 1, label: 'Traseira', className: 'rear' },
  { key: 2, label: 'Lado esquerdo', className: 'left' },
  { key: 3, label: 'Lado direito', className: 'right' },
  { key: 4, label: 'Centro', className: 'center' },
] as const;

type DamageDisplayMode = 'normalized' | 'percentage' | 'points';

function displayMode(values: number[]): DamageDisplayMode {
  if (values.every((value) => value <= 1)) return 'normalized';
  if (values.every((value) => value <= 100)) return 'percentage';
  return 'points';
}

function damagePercent(value: number, mode: DamageDisplayMode, maximum: number): number {
  const percentage = mode === 'normalized' ? value * 100
    : mode === 'percentage' ? value
    : maximum > 0 ? (value / maximum) * 100 : 0;
  return Math.max(0, Math.min(100, percentage));
}

function severity(value: number): string {
  if (value <= 0.01) return 'clear';
  if (value < 25) return 'minor';
  if (value < 60) return 'moderate';
  return 'severe';
}

function formatDamage(value: number, mode: DamageDisplayMode): string {
  const displayValue = mode === 'normalized' ? value * 100 : value;
  const formatted = displayValue.toLocaleString('pt-BR', { maximumFractionDigits: 1 });
  return mode === 'points' ? `${formatted} pts` : `${formatted}%`;
}

export function VehicleDamage({ sample }: { sample: TelemetrySample }) {
  const rawValues = zones.map(({ key }) => sample.car_damage[key]);
  const mode = displayMode(rawValues);
  const rawMaximum = Math.max(...rawValues);
  const values = rawValues.map((value) => damagePercent(value, mode, rawMaximum));
  const rawAverage = rawValues.reduce((sum, value) => sum + value, 0) / rawValues.length;

  return <div className="vehicle-condition">
    <div className="vehicle-condition-summary">
      <div><span>Dano máximo</span><strong>{formatDamage(rawMaximum, mode)}</strong></div>
      <div><span>Média das zonas</span><strong>{formatDamage(rawAverage, mode)}</strong></div>
      <div><span>Amostra</span><strong>#{sample.sequence}</strong></div>
    </div>
    <div className="damage-diagram" aria-label="Mapa das zonas de dano do veículo">
      {zones.map(({ key, label, className }) => {
        const rawValue = rawValues[key];
        const percent = values[key];
        return <div key={label} className={`damage-zone damage-zone-${className} ${severity(percent)}`}>
          <span>{label}</span><strong>{formatDamage(rawValue, mode)}</strong>
        </div>;
      })}
    </div>
    <div className="damage-list">
      {zones.map(({ key, label }) => {
        const rawValue = rawValues[key];
        const percent = values[key];
        return <div key={label}>
          <div className="damage-list-label"><span>{label}</span><strong>{formatDamage(rawValue, mode)}</strong></div>
          <div className="damage-progress"><i className={severity(percent)} style={{ width: `${percent}%` }}/></div>
        </div>;
      })}
    </div>
    <p className="damage-note">O Shared Memory do Assetto Corsa disponibiliza cinco zonas agregadas: frente, traseira, lados e centro. Isso não representa peças individuais, suspensão ou pneus.</p>
  </div>;
}
