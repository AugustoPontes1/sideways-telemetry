import { useEffect, useMemo, useState } from 'react';
import { Camera, Info, Pause, Play, RotateCcw } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { PageTitle } from '../components/PageTitle';
import { Panel } from '../components/Panel';
import { EmptyState } from '../components/EmptyState';
import { useReferenceTrajectory } from '../modules/cartesian-2d/useReferenceTrajectory';
import { TrajectoryScene } from '../modules/trajectory-3d/TrajectoryScene';
import { usePlayback } from '../modules/trajectory-3d/usePlayback';
import { formatNumber, radiansToDegrees } from '../lib/telemetry';

export function TrajectoryPage() {
  const { samples, cursorSample, sessions, activeSession, demo, setCursorSequence, resumeLive } = useApp();
  const [refId, setRefId] = useState('');
  const [showRef, setShowRef] = useState(true);
  const references = useMemo(() => sessions.filter((s) => s.stream_id !== activeSession?.stream_id && s.track === activeSession?.track), [sessions, activeSession?.stream_id, activeSession?.track]);
  useEffect(() => { setRefId(references[0]?.stream_id || ''); }, [demo, activeSession?.stream_id]);
  const reference = references.find((s) => s.stream_id === refId) || null;
  const { positions, loading, error } = useReferenceTrajectory(activeSession, reference, demo, showRef);
  const playback = usePlayback(samples, cursorSample?.sequence ?? null, setCursorSequence);
  return <>
    <PageTitle eyebrow="MÓDULOS / REPLAY" title="Trajetória em 3D"
      subtitle="Reviva o movimento em três dimensões, observe a orientação do carro e compare com um traçado de referência."/>
    {cursorSample && samples.length ? <>
      <Panel title="Visualizador do carro" subtitle="Modelo didático · coordenadas globais X/Y/Z · direção a validar"
        action={<span className="view-label"><Camera size={16}/> Câmera livre</span>}>
        <TrajectoryScene samples={samples} selected={cursorSample} reference={showRef ? positions : []}/>
        <div className="playback-toolbar">
          <button className="button button-primary" onClick={() => playback.setPlaying(!playback.playing)}>
            {playback.playing ? <Pause size={16}/> : <Play size={16}/>} {playback.playing ? 'Pausar' : 'Reproduzir'}
          </button>
          <button className="button button-secondary" title="Voltar para a última amostra" onClick={() => { playback.setPlaying(false); resumeLive(); }}><RotateCcw size={16}/> Atual</button>
          <label className="speed-select">Velocidade <select value={playback.speed} onChange={(e) => playback.setSpeed(Number(e.target.value))}>
            <option value={0.5}>0,5×</option><option value={1}>1×</option><option value={2}>2×</option><option value={4}>4×</option>
          </select></label>
          <label className="switch-label"><input type="checkbox" checked={showRef} onChange={(e) => setShowRef(e.target.checked)}/> Mostrar referência</label>
          {showRef && !demo && <select className="ref-inline" aria-label="Selecionar trajetória de referência" value={refId} onChange={(e) => setRefId(e.target.value)}>
            {!references.length && <option value="">Sem sessão de referência</option>}
            {references.map((s) => <option key={s.stream_id} value={s.stream_id}>{s.car} · {s.stream_id.slice(0,8)}</option>)}
          </select>}
        </div>
        {loading && <p className="muted small">Buscando trajetória gravada…</p>}
        {error && <p className="inline-error">{error}</p>}
      </Panel>
      <div className="content-grid split-equal">
        <Panel title="Estado atual do veículo" subtitle={`Amostra #${cursorSample.sequence}`}>
          <div className="data-list">
            <div><span>X / Y / Z</span><strong>{cursorSample.position_world_m.map((n) => formatNumber(n,1)).join(' / ')} m</strong></div>
            <div><span>Heading bruto</span><strong>{formatNumber(radiansToDegrees(cursorSample.heading_rad),1)}°</strong></div>
            <div><span>RPM</span><strong>{formatNumber(cursorSample.rpm,0)}</strong></div>
            <div><span>Velocidade</span><strong>{formatNumber(cursorSample.speed_kmh)} km/h</strong></div>
          </div>
        </Panel>
        <Panel title="Sobre a linha tracejada" subtitle="Interpretação física e limitação do modelo">
          <p className="body-copy"><Info size={15}/> A linha azul é uma <strong>captura de referência</strong> ou uma curva simulada, nunca uma trajetória calculada como ideal.</p>
          <p className="body-copy muted">A otimização de uma trajetória de drift depende também da geometria e limites da pista, velocidade, aderência, orientação e controles. A rotação do motor (RPM) é apenas um dos sinais disponíveis.</p>
        </Panel>
      </div>
    </> : <EmptyState />}
  </>;
}
