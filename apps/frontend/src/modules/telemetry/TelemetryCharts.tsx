import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { Data, Layout } from 'plotly.js';
import type { TelemetrySample } from '../../lib/types';
import { downsample, radiansToDegrees } from '../../lib/telemetry';

const chartColors = { teal: '#19c4ad', blue: '#5f9afa', orange: '#f4aa66', pink: '#e97c88' };
const transparent = 'rgba(0,0,0,0)';

export function TimeSeriesChart({ samples, selectedSequence, onSelect, kind = 'inputs', height = 285 }: {
  samples: TelemetrySample[];
  selectedSequence: number | null;
  onSelect?: (sequence: number) => void;
  kind?: 'inputs' | 'speedrpm' | 'steering';
  height?: number;
}) {
  const visible = useMemo(() => downsample(samples, 750), [samples]);
  const firstTime = samples[0] ? Date.parse(samples[0].sampled_at) : 0;
  const x = visible.map((s) => (Date.parse(s.sampled_at) - firstTime) / 1000);
  const selected = samples.find((s) => s.sequence === selectedSequence);
  const selectedT = selected ? (Date.parse(selected.sampled_at) - firstTime) / 1000 : undefined;
  const traces = useMemo(() => {
    const make = (label: string, y: number[], color: string, axis: 'y' | 'y2' = 'y'): Data => ({
      x, y, name: label, type: 'scattergl', mode: 'lines', yaxis: axis,
      line: { color, width: 2.2 }, hovertemplate: '%{x:.2f}s · %{y:.1f}<extra>%{fullData.name}</extra>',
    });
    if (kind === 'inputs') return [
      make('Acelerador (%)', visible.map((s) => s.throttle * 100), chartColors.teal),
      make('Freio (%)', visible.map((s) => s.brake * 100), chartColors.pink),
      make('Embreagem (%)', visible.map((s) => s.clutch * 100), chartColors.blue),
    ];
    if (kind === 'speedrpm') return [
      make('Velocidade (km/h)', visible.map((s) => s.speed_kmh), chartColors.teal),
      make('RPM', visible.map((s) => s.rpm), chartColors.orange, 'y2'),
    ];
    return [make('Direção (°)*', visible.map((s) => radiansToDegrees(s.steer_angle_rad)), chartColors.blue)];
  }, [visible, x, kind]);
  const layout: Partial<Layout> = {
    height, autosize: true, paper_bgcolor: transparent, plot_bgcolor: transparent,
    margin: { l: 52, r: kind === 'speedrpm' ? 50 : 16, t: 16, b: 42 },
    font: { family: 'Inter, system-ui, sans-serif', color: '#8192a8', size: 11 },
    legend: { orientation: 'h', x: 0, y: 1.18, bgcolor: transparent, font: { size: 10 } },
    xaxis: { title: { text: 'Tempo (s)', font: { size: 10 } }, gridcolor: '#253044', zeroline: false },
    yaxis: { gridcolor: '#253044', zeroline: false, title: { text: kind === 'inputs' ? '%' : kind === 'speedrpm' ? 'km/h' : '°' } },
    ...(kind === 'speedrpm' ? {
      yaxis2: { title: { text: 'RPM' }, overlaying: 'y' as const, side: 'right' as const, showgrid: false },
    } : {}),
    ...(selectedT !== undefined ? { shapes: [{ type: 'line', x0: selectedT, x1: selectedT,
      y0: 0, y1: 1, xref: 'x' as const, yref: 'paper' as const,
      line: { color: '#ccd6e5', width: 1, dash: 'dot' as const } }] } : {}),
    hovermode: 'x unified',
  };
  return <Plot
    data={traces} layout={layout} useResizeHandler style={{ width: '100%', height }}
    config={{ responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d'] }}
    onClick={(e) => {
      const point = e.points?.[0];
      const index = point?.pointNumber;
      if (typeof index === 'number' && visible[index] && onSelect) onSelect(visible[index].sequence);
    }}
  />;
}
