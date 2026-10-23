import { Radio, SkipForward } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { formatNumber } from '../lib/telemetry';

export function Timeline() {
  const { samples, cursorSample, isFollowing, setCursorSequence, resumeLive } = useApp();
  if (!samples.length) return null;
  const first = samples[0];
  const last = samples[samples.length - 1];
  const seconds = (Date.parse(cursorSample?.sampled_at ?? last.sampled_at) - Date.parse(first.sampled_at)) / 1000;
  return (
    <div className="timeline">
      <div className="timeline-top">
        <span>LINHA DO TEMPO</span>
        <div className="timeline-meta">
          <strong>{formatNumber(seconds, 2)} s</strong>
          <span className="muted">· seq #{cursorSample?.sequence ?? last.sequence}</span>
          <button className={`button-mini ${isFollowing ? 'accent-text' : ''}`} onClick={resumeLive} title="Voltar para a última amostra">
            {isFollowing ? <Radio size={14} /> : <SkipForward size={14} />} Última amostra
          </button>
        </div>
      </div>
      <input
        aria-label="Selecionar amostra da telemetria"
        type="range"
        min={first.sequence}
        max={last.sequence}
        step={1}
        value={cursorSample?.sequence ?? last.sequence}
        onChange={(event) => setCursorSequence(Number(event.target.value))}
        className="range"
      />
      <div className="timeline-labels">
        <span>#{first.sequence}</span>
        <span>#{last.sequence}</span>
      </div>
    </div>
  );
}
