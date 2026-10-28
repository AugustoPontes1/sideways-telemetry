import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { Data, Layout } from 'plotly.js';
import { downsample } from '../../lib/telemetry';
import type { TelemetrySample, TrackMap, Vec3 } from '../../lib/types';

interface CartesianPlotProps {
  samples: TelemetrySample[];
  reference: Vec3[];
  trackMap?: TrackMap | null;
  cursorSequence: number | null;
  selectedSample?: TelemetrySample | null;
  onSelect: (seq: number) => void;
  showVelocity: boolean;
  height?: number;
}

export function CartesianPlot({ samples, reference, trackMap, cursorSequence, selectedSample, onSelect, showVelocity, height = 490 }: CartesianPlotProps) {
  const visible = useMemo(() => downsample(samples, 1100), [samples]);
  const fullTrack = useMemo(() => trackMap && Array.isArray(trackMap.points) && trackMap.points.length >= 2
    ? downsample(trackMap.points, 1200) : [], [trackMap]);
  const selected = selectedSample || samples.find((s) => s.sequence === cursorSequence) || samples.at(-1);
  const referenceVisible = useMemo(() => downsample(reference, 1100), [reference]);
  const trajectoryTrace = useMemo<Data>(() => ({
      type: 'scattergl', mode: 'lines', name: fullTrack.length ? 'Pista completa' : 'Trajetória executada',
      x: (fullTrack.length ? fullTrack.map((point) => point[0]) : visible.map((s) => s.position_world_m[0])),
      y: (fullTrack.length ? fullTrack.map((point) => point[2]) : visible.map((s) => s.position_world_m[2])),
      line: { color: '#12baa7', width: 3 },
      hovertemplate: 'X: %{x:.2f} m<br>Z: %{y:.2f} m<extra>Pista</extra>',
  }), [fullTrack, visible]);
  const sessionTrace = useMemo<Data | null>(() => fullTrack.length ? ({
      type: 'scattergl', mode: 'lines', name: 'Minha sessão',
      x: visible.map((s) => s.position_world_m[0]), y: visible.map((s) => s.position_world_m[2]),
      line: { color: '#f8ae62', width: 2, dash: 'dot' },
      customdata: visible.map((s) => s.sequence),
      hovertemplate: 'X: %{x:.2f} m<br>Z: %{y:.2f} m<br>Seq #%{customdata}<extra>Minha sessão</extra>',
  }) : null, [fullTrack, visible]);
  const referenceTrace = useMemo<Data | null>(() => referenceVisible.length ? ({
      type: 'scattergl', mode: 'lines', name: 'Referência (não ideal)',
      x: referenceVisible.map((v) => v[0]), y: referenceVisible.map((v) => v[2]),
      line: { color: '#6ca4ff', width: 2.5, dash: 'dash' },
      hovertemplate: 'X: %{x:.2f} m<br>Z: %{y:.2f} m<extra>Referência</extra>',
  }) : null, [referenceVisible]);
  const staticData = useMemo(() => [trajectoryTrace, ...(sessionTrace ? [sessionTrace] : []), ...(referenceTrace ? [referenceTrace] : [])], [referenceTrace, sessionTrace, trajectoryTrace]);
  const data: Data[] = [...staticData];
  if (selected) {
    data.push({
      type: 'scatter', mode: 'markers', name: 'Carro (instante)',
      x: [selected.position_world_m[0]], y: [selected.position_world_m[2]],
      marker: { color: '#f8ae62', size: 13, symbol: 'circle', line: { color: '#ffffff', width: 2 } },
      hoverinfo: 'skip',
    });
    if (showVelocity) {
      const v = selected.velocity_world_mps;
// Velocity arrow: 0.4-second projection for visualization only.
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
  const layout = useMemo<Partial<Layout>>(() => ({
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
  }), [height]);
  return <Plot
    data={data} layout={layout} style={{ width: '100%', height }} useResizeHandler
    config={{ responsive: true, displaylogo: false, scrollZoom: true }}
    onClick={(event) => {
      const selectedPoint = event.points?.[0];
      const selectableCurve = fullTrack.length ? 1 : 0;
      if (selectedPoint?.curveNumber === selectableCurve && typeof selectedPoint.pointNumber === 'number') {
        const found = visible[selectedPoint.pointNumber];
        if (found) onSelect(found.sequence);
      }
    }}
  />;
}
