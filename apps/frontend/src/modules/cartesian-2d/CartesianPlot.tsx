import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { Data, Layout } from 'plotly.js';
import { downsample } from '../../lib/telemetry';
import type { TelemetrySample, Vec3 } from '../../lib/types';

interface CartesianPlotProps {
  samples: TelemetrySample[];
  reference: Vec3[];
  cursorSequence: number | null;
  onSelect: (seq: number) => void;
  showVelocity: boolean;
  height?: number;
}

export function CartesianPlot({ samples, reference, cursorSequence, onSelect, showVelocity, height = 490 }: CartesianPlotProps) {
  const visible = useMemo(() => downsample(samples, 1100), [samples]);
  const selected = samples.find((s) => s.sequence === cursorSequence) || samples.at(-1);
  const referenceVisible = useMemo(() => downsample(reference, 1100), [reference]);
  const data: Data[] = [
    {
      type: 'scattergl', mode: 'lines', name: 'Trajetória executada',
      x: visible.map((s) => s.position_world_m[0]), y: visible.map((s) => s.position_world_m[2]),
      line: { color: '#12baa7', width: 3 },
      customdata: visible.map((s) => s.sequence),
      hovertemplate: 'X: %{x:.2f} m<br>Z: %{y:.2f} m<br>Seq #%{customdata}<extra>Carro</extra>',
    },
  ];
  if (referenceVisible.length) data.push({
    type: 'scattergl', mode: 'lines', name: 'Referência (não ideal)',
    x: referenceVisible.map((v) => v[0]), y: referenceVisible.map((v) => v[2]),
    line: { color: '#6ca4ff', width: 2.5, dash: 'dash' },
    hovertemplate: 'X: %{x:.2f} m<br>Z: %{y:.2f} m<extra>Referência</extra>',
  });
  if (selected) {
    data.push({
      type: 'scatter', mode: 'markers', name: 'Carro (instante)',
      x: [selected.position_world_m[0]], y: [selected.position_world_m[2]],
      marker: { color: '#f8ae62', size: 13, symbol: 'circle', line: { color: '#ffffff', width: 2 } },
      hoverinfo: 'skip',
    });
    if (showVelocity) {
      const v = selected.velocity_world_mps;
      // Seta de velocidade: 0,4 s de projeção, apenas para visualização.
      const px = selected.position_world_m[0], pz = selected.position_world_m[2];
      data.push({
        type: 'scatter', mode: 'lines+markers', name: 'Vetor velocidade × 0,4s',
        x: [px, px + v[0] * .4], y: [pz, pz + v[2] * .4],
        line: { color: '#f8ae62', width: 2 },
        marker: { color: '#f8ae62', size: [0, 8] },
        hoverinfo: 'skip',
      });
    }
  }
  const layout: Partial<Layout> = {
    height,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, system-ui, sans-serif', color: '#93a0b6', size: 11 },
    margin: { l: 56, b: 55, t: 15, r: 20 },
    showlegend: true,
    legend: { orientation: 'h', x: 0, y: 1.12, bgcolor: 'rgba(0,0,0,0)' },
    xaxis: { title: { text: 'X global (m)' }, gridcolor: '#273348', zeroline: false, showline: true, linecolor: '#394861' },
    yaxis: { title: { text: 'Z global (m)' }, gridcolor: '#273348', zeroline: false, scaleanchor: 'x', scaleratio: 1, showline: true, linecolor: '#394861' },
    dragmode: 'pan', hovermode: 'closest',
  };
  return <Plot
    data={data} layout={layout} style={{ width: '100%', height }} useResizeHandler
    config={{ responsive: true, displaylogo: false, scrollZoom: true }}
    onClick={(event) => {
      const selectedPoint = event.points?.[0];
      if (selectedPoint?.curveNumber === 0 && typeof selectedPoint.pointNumber === 'number') {
        const found = visible[selectedPoint.pointNumber];
        if (found) onSelect(found.sequence);
      }
    }}
  />;
}
