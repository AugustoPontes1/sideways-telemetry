import { Activity, TimerReset } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { Panel } from '../components/Panel';
import { PageTitle } from '../components/PageTitle';
import { EmptyState } from '../components/EmptyState';
import { TimeSeriesChart } from '../modules/telemetry/TelemetryCharts';
import { LiveDriverControls } from '../components/LiveHud';
import { formatNumber } from '../lib/telemetry';

export function TelemetryPage() {
  const { samples, cursorSample, setCursorSequence } = useApp();
  return <>
    <PageTitle eyebrow="MÓDULOS / TELEMETRIA" title="Análise dos comandos"
      subtitle="Compare velocidade, RPM, direção e pedais no mesmo eixo temporal. Clique no gráfico para selecionar um instante."/>
    {!samples.length || !cursorSample ? <EmptyState /> : <>
      <div className="content-grid split-main">
        <Panel title="Velocidade e rotação" subtitle="Velocidade (km/h) e motor (rpm) em eixos separados">
          <TimeSeriesChart kind="speedrpm" samples={samples} selectedSequence={cursorSample.sequence} onSelect={setCursorSequence} />
        </Panel>
        <Panel title="Controles no instante" subtitle={`Amostra #${cursorSample.sequence}`}>
          <div className="inline-kpi"><Activity size={18}/><span>Velocidade</span><strong>{formatNumber(cursorSample.speed_kmh)} km/h</strong></div>
          <div className="inline-kpi"><TimerReset size={18}/><span>RPM</span><strong>{formatNumber(cursorSample.rpm,0)}</strong></div>
          <div className="divider"/>
          <LiveDriverControls />
        </Panel>
      </div>
      <div className="content-grid split-equal">
        <Panel title="Pedais (%)" subtitle="Observe o timing da aceleração e frenagem">
          <TimeSeriesChart kind="inputs" samples={samples} selectedSequence={cursorSample.sequence} onSelect={setCursorSequence} />
        </Panel>
        <Panel title="Ângulo do volante (°)" subtitle="Sinal bruto convertido de radianos para graus">
          <TimeSeriesChart kind="steering" samples={samples} selectedSequence={cursorSample.sequence} onSelect={setCursorSequence} />
        </Panel>
      </div>
      <p className="page-note">O ângulo do volante precisa ser validado contra o movimento real do G29. Variações simultâneas são correlações temporais, não prova de causalidade.</p>
    </>}
  </>;
}
