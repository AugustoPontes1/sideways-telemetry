import { useEffect, useMemo, useState } from 'react';
import { BookOpen, CheckCircle2, ChevronDown, ChevronUp, Eye, EyeOff, Info, RotateCcw, XCircle } from 'lucide-react';
import { checkExercise, getExercise, getTopics } from '../../lib/api';
import { demoTopics, generateDemoExercise } from '../../lib/demo';
import { downsample } from '../../lib/telemetry';
import type { AnswerCheck, Exercise, LearningTopic, TelemetrySample } from '../../lib/types';
import { compareDemoAnswer, parseStudentAnswer, prettyJson } from './answers';

export function MathExercise({ streamId, samples, demo }: { streamId: string; samples: TelemetrySample[]; demo: boolean }) {
  const [topics, setTopics] = useState<LearningTopic[]>(demo ? demoTopics : []);
  const [topic, setTopic] = useState('displacement');
  const [aInput, setA] = useState<number | null>(null);
  const [bInput, setB] = useState<number | null>(null);
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [answer, setAnswer] = useState('');
  const [check, setCheck] = useState<AnswerCheck | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setTopic('displacement'); setA(null); setB(null);
    setExercise(null); setExpanded(false); setAnswer(''); setCheck(null);
  }, [streamId, demo]);

  useEffect(() => {
    if (demo) { setTopics(demoTopics); return; }
    let valid = true;
    getTopics().then((x) => { if (valid) setTopics(x.topics); }).catch((exc: unknown) => {
      if (valid) setError(exc instanceof Error ? exc.message : 'Falha ao listar temas.');
    });
    return () => { valid = false; };
  }, [demo]);

  const candidateSamples = useMemo(() => downsample(samples, 80), [samples]);
  // Escolhas ficam congeladas ao carregar a janela; atualizações ao vivo não apagam a resposta do aluno.
  useEffect(() => {
    if (samples.length < 2) return;
    setA((old) => old !== null && samples.some((s) => s.sequence === old) ? old : samples[Math.max(0, Math.floor(samples.length * .35))].sequence);
    setB((old) => old !== null && samples.some((s) => s.sequence === old) ? old : samples[Math.max(0, Math.floor(samples.length * .85))].sequence);
  }, [samples]);
  const a = aInput ?? -1;
  const b = bInput ?? -1;
  const choices = useMemo(() => [...new Set([...candidateSamples.map((s) => s.sequence), a, b])].filter((s) => s >= 0).sort((x, y) => x - y), [candidateSamples, a, b]);

  useEffect(() => {
    setExercise(null); setExpanded(false); setCheck(null); setAnswer('');
    setError(null);
    if (a < 0 || b < 0 || a === b || !samples.length) return;
    if (demo) { setExercise(generateDemoExercise(topic, a, b)); return; }
    let active = true;
    const timer = setTimeout(() => {
      setBusy(true);
      getExercise(streamId, topic, a, b).then((x) => { if (active) setExercise(x); })
        .catch((exc: unknown) => { if (active) setError(exc instanceof Error ? exc.message : 'Exercício indisponível.'); })
        .finally(() => { if (active) setBusy(false); });
    }, 180);
    return () => { active = false; clearTimeout(timer); };
  }, [streamId, topic, a, b, demo]);

  async function reveal() {
    if (expanded) { setExpanded(false); return; }
    if (!exercise) return;
    setError(null);
    setBusy(true);
    try {
      const item = demo ? generateDemoExercise(topic, a, b, true) : await getExercise(streamId, topic, a, b, true);
      setExercise(item); setExpanded(true);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Não foi possível revelar a resolução.');
    } finally { setBusy(false); }
  }

  async function evaluate() {
    if (!exercise) return;
    setError(null);
    try {
      const parsed = parseStudentAnswer(answer);
      setBusy(true);
      const result = demo ? {
        correct: compareDemoAnswer(exercise.expected_result, parsed),
        expected_result: exercise.expected_result, solution_revealed: false,
      } : await checkExercise(streamId, topic, a, b, parsed);
      setCheck(result);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Erro ao conferir a resposta.');
    } finally { setBusy(false); }
  }

  return <div className="math-flow">
    <div className="math-config">
      <label><span>TEMA</span><select value={topic} onChange={(e) => setTopic(e.target.value)}>
        {topics.map((t) => <option key={t.id} value={t.id}>{t.title} (Aula {t.lessons.join(', ')})</option>)}
      </select></label>
      <label><span>AMOSTRA A</span><select value={a} onChange={(e) => setA(Number(e.target.value))}>
        {choices.map((seq) => <option key={seq} value={seq}>#{seq}</option>)}
      </select></label>
      <label><span>AMOSTRA B</span><select value={b} onChange={(e) => setB(Number(e.target.value))}>
        {choices.map((seq) => <option key={seq} value={seq}>#{seq}</option>)}
      </select></label>
    </div>
    {busy && <p className="muted small">Calculando ou consultando o backend…</p>}
    {a === b && <p className="inline-error">Escolha duas amostras diferentes.</p>}
    {error && <p className="inline-error" role="alert">{error}</p>}
    {exercise && <>
      <div className="exercise-head"><div className="exercise-icon"><BookOpen size={21}/></div><div><span>EXERCÍCIO · {exercise.lessons.map((i) => `AULA ${i}`).join(' / ')}</span><h2>{exercise.title}</h2></div></div>
      <p className="exercise-question">{exercise.question}</p>
      <div className="math-two-col">
        <div className="math-code-box"><span>VALORES FORNECIDOS</span><pre>{prettyJson(exercise.inputs)}</pre></div>
        <div className="math-code-box answer-box"><span>RESULTADO ESPERADO</span><pre>{prettyJson(exercise.expected_result)}</pre></div>
      </div>
      <div className="student-check">
        <label htmlFor="student-answer">MINHA RESPOSTA (JSON)</label>
        <p>Resolva no papel antes de preencher. Para múltiplos valores, digite um objeto ou vetor no formato exibido.</p>
        <textarea id="student-answer" rows={4} spellCheck={false} value={answer} onChange={(e) => { setAnswer(e.target.value); setCheck(null); }}
          placeholder={prettyJson(exercise.expected_result).replace(/[-\d.]+/g, '?')} />
        <div className="actions-row">
          <button className="button button-primary" disabled={busy || !answer.trim()} onClick={() => void evaluate()}><CheckCircle2 size={16}/> Conferir resposta</button>
          <button className="button button-secondary" onClick={() => { setAnswer(''); setCheck(null); setExpanded(false); }}><RotateCcw size={15}/> Limpar</button>
        </div>
        {check && <div className={`answer-feedback ${check.correct ? 'correct' : 'incorrect'}`} role="status">
          {check.correct ? <CheckCircle2 size={19}/> : <XCircle size={19}/>}
          <strong>{check.correct ? 'Seu resultado está correto.' : 'O resultado não corresponde ao esperado. Reveja as operações.'}</strong>
        </div>}
      </div>
      <div className="solution-area">
        <button className="solution-trigger" aria-expanded={expanded} onClick={() => void reveal()} disabled={busy}>
          <span>{expanded ? <EyeOff size={18}/> : <Eye size={18}/>} {expanded ? 'Ocultar resolução' : 'Revelar resolução passo a passo'}</span>
          {expanded ? <ChevronUp size={18}/> : <ChevronDown size={18}/>}
        </button>
        {expanded && exercise.solution && <ol className="solution-steps">{exercise.solution.map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}</ol>}
      </div>
      <p className="math-note"><Info size={15}/> {exercise.note}</p>
    </>}
  </div>;
}
