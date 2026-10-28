import { useEffect, useMemo, useState } from 'react';
import { Compass, Info, MoveUpRight, Route } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { EmptyState } from '../components/EmptyState';
import { Panel } from '../components/Panel';
import { PageTitle } from '../components/PageTitle';
import { CartesianPlot } from '../modules/cartesian-2d/CartesianPlot';
import { useReferenceTrajectory } from '../modules/cartesian-2d/useReferenceTrajectory';
import { useLiveInterpolatedSample } from '../modules/telemetry/useLiveInterpolatedSample';
import { formatNumber } from '../lib/telemetry';
import { TrackMiniMap } from '../components/TrackMiniMap';

export function CartesianPage() {
  const { samples, cursorSample, isFollowing, setCursorSequence, sessions, activeSession, trackMap, demo, publicMode } = useApp();
  const liveSample = useLiveInterpolatedSample(samples, isFollowing && !demo, 60);
  const displaySample = liveSample || cursorSample;
  const [showRef, setShowRef] = useState(true);
  const [refId, setRefId] = useState('');
  const [showVelocity, setShowVelocity] = useState(true);
  const references = useMemo(() => sessions.filter((s) => s.stream_id !== activeSession?.stream_id && s.track === activeSession?.track), [sessions, activeSession?.stream_id, activeSession?.track]);
  useEffect(() => { setRefId(references[0]?.stream_id ?? ''); }, [activeSession?.stream_id, demo]);
  const reference = references.find((s) => s.stream_id === refId) || null;
  const result = useReferenceTrajectory(activeSession, reference, demo, showRef, publicMode);
  return <>
    <PageTitle eyebrow="MÓDULOS / ÁLGEBRA APLICADA" title="Plano cartesiano 2D"
      subtitle="Trajetória em X/Z, vetor velocidade e comparação geométrica com outra captura da mesma pista."/>
    {samples.length && displaySample ? <>
      <Panel title="Trajetória da sessão" subtitle="Eixos globais X/Z · escala 1:1 · clique na linha para selecionar uma amostra"
        action={<div className="toolbar">
          <label className="switch-label"><input type="checkbox" checked={showVelocity} onChange={(e) => setShowVelocity(e.target.checked)} /> Vetor velocidade</label>
          <label className="switch-label"><input type="checkbox" checked={showRef} onChange={(e) => setShowRef(e.target.checked)} /> Referência</label>
        </div>}>
        {showRef && !demo && <div className="reference-select"><label htmlFor="cart-ref">CAPTURA DE REFERÊNCIA</label>
          <select id="cart-ref" value={refId} onChange={(e) => setRefId(e.target.value)}>
            {!references.length && <option value="">Nenhuma sessão na mesma pista</option>}
            {references.map((s) => <option key={s.stream_id} value={s.stream_id}>{s.car_visual?.display_name || s.car} · {new Date(s.last_sample_at).toLocaleDateString('pt-BR')} · {s.stream_id.slice(0,8)}</option>)}
          </select></div>}
        <CartesianPlot samples={samples} reference={showRef ? result.positions : []} trackMap={trackMap} cursorSequence={displaySample.sequence}
          selectedSample={displaySample} onSelect={setCursorSequence} showVelocity={showVelocity} />
      </Panel>
      <Panel title="Mapa da pista" subtitle="Projeção X/Z do traçado capturado nesta sessão">
        <TrackMiniMap samples={samples} selected={displaySample} reference={showRef ? result.positions : []} trackMap={trackMap} trackName={activeSession?.track}/>
      </Panel>
      <div className="content-grid split-equal">
        <Panel title="Coordenadas do carro" subtitle={`Amostra #${displaySample.sequence}`}>
          <div className="data-list">
            <div><span>Posição X</span><strong>{formatNumber(displaySample.position_world_m[0],2)} m</strong></div>
            <div><span>Posição Z</span><strong>{formatNumber(displaySample.position_world_m[2],2)} m</strong></div>
            <div><span>Velocidade X</span><strong>{formatNumber(displaySample.velocity_world_mps[0],2)} m/s</strong></div>
            <div><span>Velocidade Z</span><strong>{formatNumber(displaySample.velocity_world_mps[2],2)} m/s</strong></div>
          </div>
        </Panel>
        <Panel title="Comparação de trajetória" subtitle="Distância geométrica até a polilinha de referência">
          <div className="comparison-cards">
            <div><MoveUpRight size={19}/><span>Desvio médio</span><strong>{result.metrics ? `${formatNumber(result.metrics.mean_distance_m,2)} m` : '—'}</strong></div>
            <div><Compass size={19}/><span>Desvio máximo</span><strong>{result.metrics ? `${formatNumber(result.metrics.max_distance_m,2)} m` : '—'}</strong></div>
          </div>
          {result.loading && <p className="muted small">Carregando a trajetória de referência…</p>}
          {result.error && <p className="inline-error">{result.error}</p>}
          <p className="hint"><Info size={14}/> {demo ? 'Exemplo fictício.' : result.metrics?.limitations || 'Selecione uma referência na mesma pista para comparar.'}</p>
        </Panel>
      </div>
      <p className="page-note"><Route size={15}/> Linha tracejada = referência gravada ou simulada, não uma trajetória fisicamente ótima. RPM sozinho não determina o traçado correto.</p>
    </> : <EmptyState />}
  </>;
}
