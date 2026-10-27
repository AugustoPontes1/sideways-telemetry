import { useEffect, useState } from 'react';
import { ArrowUpRight, BarChart3, BookOpen, Boxes, Flag, Radio, Route, Signal } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Panel } from '../components/Panel';
import { PageTitle } from '../components/PageTitle';
import { EmptyState } from '../components/EmptyState';
import { LiveDriverControls, LiveHud } from '../components/LiveHud';
import { TimeSeriesChart } from '../modules/telemetry/TelemetryCharts';
import { demoAnalysis } from '../lib/demo';
import { getAnalysis } from '../lib/api';
import { formatNumber } from '../lib/telemetry';
import type { SessionAnalysis } from '../lib/types';

export function DashboardPage() {
  const { activeSession, samples, cursorSample, setCursorSequence, demo, liveStatus, streamError } = useApp();
  const [analysis, setAnalysis] = useState<SessionAnalysis | null>(demo ? demoAnalysis : null);
  useEffect(() => {
    if (demo) { setAnalysis(demoAnalysis); return; }
    if (!activeSession) { setAnalysis(null); return; }
    let valid = true;
    const load = () => { getAnalysis(activeSession.stream_id).then((v) => { if (valid) setAnalysis(v); }).catch(() => { if (valid) setAnalysis(null); }); };
    load();
    const t = setInterval(load, 20_000);
    return () => { valid = false; clearInterval(t); };
  }, [demo, activeSession?.stream_id]);
  return <>
    <PageTitle eyebrow="VISÃO GERAL / DRIFT TELEMETRY LAB" title="Centro de telemetria"
      subtitle="Acompanhe as sessões, investigue sua pilotagem e transforme cada curva em um exercício matemático."
      action={<span className="muted small"><Signal size={15}/> {demo ? 'Modo simulado' : liveStatus === 'connected' ? 'Conexão ao vivo' : 'Dados históricos'}</span>} />
    {activeSession && cursorSample ? <>
      <LiveHud />
      <div className="content-grid split-main">
        <Panel title="Telemetria da sessão" subtitle="Acelerador, freio e embreagem (%)">
          <TimeSeriesChart samples={samples} kind="inputs" selectedSequence={cursorSample.sequence} onSelect={setCursorSequence} height={292}/>
        </Panel>
        <Panel title="Controles do piloto" subtitle="Estado dos pedais no instante selecionado">
          <div className="controls-panel"><LiveDriverControls /></div>
          <div className="divider" />
          <div className="mini-stats">
            <div><span>Volta</span><strong>{cursorSample.completed_laps ?? '—'}</strong></div>
            <div><span>Máxima na sessão</span><strong>{formatNumber(analysis?.stats.speed_max_kmh)} <small>km/h</small></strong></div>
            <div><span>Rotação máxima</span><strong>{formatNumber(analysis?.stats.rpm_max, 0)} <small>rpm</small></strong></div>
          </div>
          <div className="hint">* Ângulo disponibilizado pelo jogo. Ainda precisamos validar sua convenção e calibração em relação ao G29.</div>
        </Panel>
      </div>
      <div className="content-grid split-equal">
        <Panel title="Eventos para investigar" subtitle="Indícios do backend — não são diagnósticos de erro">
          <div className="events-list">
            {analysis?.events.length ? analysis.events.slice(0, 5).map((event, idx) => <button key={`${event.sequence}-${idx}`} className="event-row" onClick={() => setCursorSequence(event.sequence)}>
              <span className="event-icon"><Radio size={15}/></span><span><strong>{event.kind === 'throttle_change' ? 'Mudança rápida no acelerador' : 'Mudança rápida no volante'}</strong><small>Seq #{event.sequence} · {formatNumber(event.rate, 2)} {event.unit}</small></span><ArrowUpRight size={15}/>
            </button>) : <p className="muted">Nenhum evento sinalizado na janela recente.</p>}
          </div>
        </Panel>
        <Panel title="Explorar a sessão" subtitle="Selecione um módulo para continuar">
          <div className="shortcut-grid">
            <Link to="/cartesian" className="shortcut"><span className="shortcut-icon"><Route size={22}/></span><strong>Trajetória 2D</strong><small>Comparar linhas</small></Link>
            <Link to="/trajectory" className="shortcut"><span className="shortcut-icon"><Boxes size={22}/></span><strong>Replay 3D</strong><small>Ver o movimento</small></Link>
            <Link to="/telemetry" className="shortcut"><span className="shortcut-icon"><BarChart3 size={22}/></span><strong>Gráficos</strong><small>Examinar controles</small></Link>
            <Link to="/math" className="shortcut"><span className="shortcut-icon"><BookOpen size={22}/></span><strong>Modo Estudo</strong><small>Resolver e conferir</small></Link>
          </div>
        </Panel>
      </div>
      <p className="page-note"><Flag size={14}/> {demo ? 'Esta sessão é fictícia; nenhuma conclusão corresponde à sua pilotagem.' : streamError || analysis?.interpretation || 'Indicadores ainda não comprovam a causa de uma rodada ou batida.'}</p>
    </> : <EmptyState />}
  </>;
}
