import { useEffect, useMemo, useState } from 'react';
import { BookOpen, CheckCircle2, ChevronDown, ChevronUp, Eye, EyeOff, Info, RotateCcw, XCircle } from 'lucide-react';
import { checkExercise, getExercise, getTopics } from '../../lib/api';
import { demoTopics, generateDemoExercise } from '../../lib/demo';
import { downsample, formatNumber } from '../../lib/telemetry';
import type { AnswerCheck, BasisDimensionCalculation, Exercise, ExerciseCalculation, LearningTopic, TelemetrySample } from '../../lib/types';
import { compareDemoAnswer, parseStudentAnswer, prettyJson } from './answers';

function formatVector(vector: number[]): string {
  return `(${vector.map((value) => formatNumber(value, 3)).join('; ')})`;
}

function SubspaceExplanation({ calculation }: { calculation: ExerciseCalculation }) {
  return <section className="math-explainer" aria-labelledby="subspace-explanation-title">
    <div className="math-explainer-heading">
      <span>COMO INTERPRETAR</span>
      <h3 id="subspace-explanation-title">O que significam v e W?</h3>
    </div>
    <p><strong>v</strong> é o vetor gerador: aqui ele é a velocidade observada nos eixos X/Z. Ele indica uma direção; seu módulo é <strong>{formatNumber(calculation.norm, 3)} m/s</strong> e seu ângulo a partir do eixo X é <strong>{calculation.angle_deg_from_x === null ? '—' : `${formatNumber(calculation.angle_deg_from_x, 2)}°`}</strong>.</p>
    <p><strong>W</strong> é o conjunto de todos os múltiplos escalares de v. Portanto, W não é outro vetor: é a reta que passa pela origem na direção de v.</p>
    <div className="math-definition-grid">
      <div className="math-definition-card"><span>VETOR GERADOR · v</span><strong>{formatVector(calculation.direction_vector)}</strong><small>{calculation.unit}</small></div>
      <div className="math-definition-card"><span>DEFINIÇÃO · W</span><strong>{calculation.parametric_form}</strong><small>t pode ser qualquer número real.</small></div>
    </div>
    <div className="math-calculation">
      <span className="math-calculation-title">ALGUNS VETORES QUE PERTENCEM A W</span>
      {calculation.multiples.map(({ t, vector }) => <div className="math-calculation-row" key={t}>
        <span>t = {formatNumber(t, 0)}</span><strong>t·v = {formatVector(vector)}</strong>
      </div>)}
    </div>
    <div className="math-conclusion">
      <div><span>BASE DE W</span><strong>{calculation.basis.length ? `{${formatVector(calculation.basis[0])}}` : '∅'}</strong></div>
      <div><span>DIMENSÃO</span><strong>{calculation.basis.length ? '1' : '0'}</strong></div>
      <div><span>É SUBESPAÇO?</span><strong>SIM</strong></div>
      <p>Como 0·v = 0 e a soma ou multiplicação por escalar de múltiplos de v continua sendo um múltiplo de v, W é um subespaço.</p>
    </div>
    <p className="math-dimension-explanation"><strong>Como a dimensão foi definida:</strong> dimensão é a quantidade de vetores linearmente independentes em uma base. {calculation.basis.length ? <>Como o vetor gerador mostrado acima é não nulo, ele é independente e sozinho gera todo W; por isso a base tem 1 vetor e <strong>dim(W) = 1</strong>.</> : <>Como o gerador é o vetor zero, W é o subespaço nulo; sua base é vazia e <strong>dim(W) = 0</strong>.</>}</p>
  </section>;
}

function BasisDimensionExplanation({ calculation }: { calculation: BasisDimensionCalculation }) {
  const [firstSequence, secondSequence] = calculation.sample_sequences;
  const interpretation = calculation.dimension === 2
    ? 'Os dois vetores apontam para direções independentes; juntos, geram o plano XZ.'
    : calculation.dimension === 1
      ? 'Os dois vetores estão na mesma direção (ou um deles é nulo); o espaço gerado é uma reta.'
      : 'Os dois vetores são nulos; o espaço gerado contém somente a origem.';
  return <section className="math-explainer" aria-labelledby="basis-dimension-explanation-title">
    <div className="math-explainer-heading">
      <span>COMO INTERPRETAR OS DADOS</span>
      <h3 id="basis-dimension-explanation-title">O que representam v1, v2 e a dimensão?</h3>
    </div>
    <p><strong>v1</strong> vem da amostra <strong>#{firstSequence}</strong> e <strong>v2</strong> vem da amostra <strong>#{secondSequence}</strong>. São as velocidades projetadas no plano horizontal: o primeiro valor é a componente X e o segundo é a componente Z, ambos em m/s.</p>
    <div className="math-definition-grid">
      <div className="math-definition-card"><span>AMOSTRA #{firstSequence} · v1</span><strong>{formatVector(calculation.v1)}</strong><small>Módulo da velocidade: {formatNumber(calculation.sample_speed_mps[0], 3)} m/s</small></div>
      <div className="math-definition-card"><span>AMOSTRA #{secondSequence} · v2</span><strong>{formatVector(calculation.v2)}</strong><small>Módulo da velocidade: {formatNumber(calculation.sample_speed_mps[1], 3)} m/s</small></div>
    </div>
    <div className="math-calculation">
      <span className="math-calculation-title">COMO O RESULTADO É CALCULADO</span>
      <div className="math-calculation-row"><span>Matriz formada</span><strong>A = {calculation.matrix.map(formatVector).join(' ; ')}</strong></div>
      <div className="math-calculation-row"><span>Determinante</span><strong>det(A) = {formatNumber(calculation.determinant, 3)}</strong></div>
      <div className="math-calculation-row"><span>Base encontrada</span><strong>{calculation.basis.length ? calculation.basis.map(formatVector).join(', ') : '∅'}</strong></div>
    </div>
    <div className="math-conclusion">
      <div><span>VALOR FINAL</span><strong>{calculation.dimension}</strong></div>
      <div><span>BASE</span><strong>{calculation.basis.length} vetor(es)</strong></div>
      <p><strong>O que significa:</strong> a dimensão é a quantidade de vetores linearmente independentes necessários para gerar todo o espaço. {interpretation}</p>
    </div>
    <p className="math-dimension-explanation"><strong>Por que esse valor?</strong> Se a dimensão é 2, v1 e v2 formam uma base com dois vetores independentes. Se é 1, apenas uma direção independente permanece na base. Se é 0, não há direção não nula; resta apenas o vetor zero.</p>
  </section>;
}

export function MathExercise({ streamId, samples, demo }: { streamId: string; samples: TelemetrySample[]; demo: boolean }) {
  const [topics, setTopics] = useState<LearningTopic[]>(demo ? demoTopics : []);
  const [topic, setTopic] = useState('displacement');
  const [aInput, setA] = useState<number | null>(null);
  const [bInput, setB] = useState<number | null>(null);
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [solutionTab, setSolutionTab] = useState<'result' | 'steps'>('steps');
  const [answer, setAnswer] = useState('');
  const [check, setCheck] = useState<AnswerCheck | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setTopic('displacement'); setA(null); setB(null);
    setExercise(null); setExpanded(false); setAnswer(''); setCheck(null);
    setSolutionTab('steps');
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
// Freeze choices when loading the window; live updates do not clear the student's answer.
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
    setSolutionTab('steps');
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
      setExercise(item); setExpanded(true); setSolutionTab('steps');
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
      {exercise.topic === 'subspace' && exercise.calculation && <SubspaceExplanation calculation={exercise.calculation as ExerciseCalculation}/>}
      {exercise.topic === 'basis_dimension' && exercise.calculation && <BasisDimensionExplanation calculation={exercise.calculation as BasisDimensionCalculation}/>}
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
        {expanded && exercise.solution && <>
          <div className="solution-tabs" role="tablist" aria-label="Conteúdo da resolução">
            <button type="button" role="tab" aria-selected={solutionTab === 'result'} className={solutionTab === 'result' ? 'active' : ''}
              onClick={() => setSolutionTab('result')}>Resultado</button>
            <button type="button" role="tab" aria-selected={solutionTab === 'steps'} className={solutionTab === 'steps' ? 'active' : ''}
              onClick={() => setSolutionTab('steps')}>Passo a passo</button>
          </div>
          {solutionTab === 'result' ? <div className="solution-result" role="tabpanel">
            <span>RESPOSTA FINAL</span>
            <pre>{prettyJson(exercise.expected_result)}</pre>
            <p>Este é o resultado obtido ao aplicar as operações matemáticas aos valores fornecidos.</p>
          </div> : <ol className="solution-steps" role="tabpanel">{exercise.solution.map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}</ol>}
        </>}
      </div>
      <p className="math-note"><Info size={15}/> {exercise.note}</p>
    </>}
  </div>;
}
