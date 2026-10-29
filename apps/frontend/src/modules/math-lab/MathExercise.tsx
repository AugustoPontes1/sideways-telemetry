import { useEffect, useMemo, useState } from 'react';
import { BookOpen, CheckCircle2, ChevronDown, ChevronUp, Eye, EyeOff, Info, RotateCcw, XCircle } from 'lucide-react';
import { checkExercise, getExercise, getTopics } from '../../lib/api';
import { demoTopics, generateDemoExercise } from '../../lib/demo';
import { downsample, formatNumber } from '../../lib/telemetry';
import type { AnswerCheck, BasisDimension3DCalculation, BasisDimensionCalculation, Exercise, ExerciseCalculation, ExerciseValue, LearningTopic, TelemetrySample } from '../../lib/types';
import { compareDemoAnswer, parseStudentAnswer, prettyJson } from './answers';
import { generateLesson19Exercise } from './lesson19';

function formatVector(vector: number[]): string {
  return `(${vector.map((value) => formatNumber(value, 3)).join('; ')})`;
}

type ExplanationCard = { label: string; value: string; meaning: string };
type ExerciseExplanation = {
  sourceIntro: string;
  sourceLines: string[];
  cards: ExplanationCard[];
  why: string;
  result: string;
};

function sampleBySequence(samples: TelemetrySample[], sequence: number): TelemetrySample | undefined {
  return samples.find((sample) => sample.sequence === sequence);
}

function samplePositionXZ(sample: TelemetrySample | undefined): number[] | null {
  return sample ? [sample.position_world_m[0], sample.position_world_m[2]] : null;
}

function sampleVelocityXZ(sample: TelemetrySample | undefined): number[] | null {
  return sample ? [sample.velocity_world_mps[0], sample.velocity_world_mps[2]] : null;
}

function telemetrySampleLine(sample: TelemetrySample | undefined, sequence: number): string {
  if (!sample) return `Amostra #${sequence}: sequência selecionada; os campos brutos não estão no lote atual.`;
  const [px, py, pz] = sample.position_world_m;
  const [vx, vy, vz] = sample.velocity_world_mps;
  return `Amostra #${sample.sequence}: posição global ${formatVector([px, py, pz])} m; velocidade global ${formatVector([vx, vy, vz])} m/s; velocidade escalar ${formatNumber(sample.speed_mps, 3)} m/s.`;
}

function valueCard(label: string, value: ExerciseValue, meaning: string): ExplanationCard {
  return { label, value: prettyJson(value), meaning };
}

function buildExerciseExplanation(exercise: Exercise, samples: TelemetrySample[]): ExerciseExplanation {
  const [firstSequence, secondSequence] = exercise.source_sequences;
  const thirdSequence = exercise.source_sequences[2];
  const first = sampleBySequence(samples, firstSequence);
  const second = sampleBySequence(samples, secondSequence);
  const p1 = samplePositionXZ(first);
  const p2 = samplePositionXZ(second);
  const v1 = sampleVelocityXZ(first);
  const v2 = sampleVelocityXZ(second);
  const sourceLines = exercise.source_sequences.map((sequence) => telemetrySampleLine(sampleBySequence(samples, sequence), sequence));
  const sourcePrefix = exercise.topic.endsWith('_3d')
    ? `As amostras selecionadas foram escolhidas nos seletores acima. O agente registra posição e velocidade em coordenadas globais X/Y/Z, preservando as três componentes para trabalhar em R³.`
    : `As amostras #${firstSequence} e #${secondSequence} foram escolhidas nos seletores acima. O agente registra posição e velocidade em coordenadas globais; o exercício projeta esses vetores no plano horizontal X/Z, descartando Y para trabalhar em R².`;
  const calculation = exercise.calculation;

  switch (exercise.topic) {
    case 'displacement':
      return {
        sourceIntro: `${sourcePrefix} P1 é a posição X/Z da amostra A e P2 é a posição X/Z da amostra B.`,
        sourceLines,
        cards: [
          valueCard('P1 · amostra A', p1 ?? exercise.inputs.P1_xz_m, 'Posição do carro no primeiro instante, em metros, apenas nos eixos X e Z.'),
          valueCard('P2 · amostra B', p2 ?? exercise.inputs.P2_xz_m, 'Posição do carro no segundo instante, em metros, apenas nos eixos X e Z.'),
          valueCard('P2 − P1', exercise.expected_result, 'A diferença entre as posições produz o deslocamento; a terceira parcela é seu módulo horizontal.'),
        ],
        why: 'Calcular o deslocamento transforma duas fotografias da telemetria em uma mudança de posição com direção e tamanho. Isso permite saber para que lado e quanto o carro avançou entre os instantes, sem confundir esse intervalo com a distância total da trajetória.',
        result: 'O resultado final é um vetor Δ no plano XZ e sua magnitude. Δx e Δz dizem como a posição mudou em cada eixo; a magnitude diz quantos metros separam os dois pontos em linha reta no plano horizontal.',
      };
    case 'displacement_3d':
      return {
        sourceIntro: `${sourcePrefix} Neste exercício, P1 e P2 mantêm X, Y e Z: Y representa a altura e não é descartado.`,
        sourceLines,
        cards: [
          valueCard('P1 · amostra A', exercise.inputs.P1_xyz_m, 'Posição global completa no primeiro instante, em metros.'),
          valueCard('P2 · amostra B', exercise.inputs.P2_xyz_m, 'Posição global completa no segundo instante, em metros.'),
          valueCard('P2 − P1', exercise.expected_result, 'Diferença das três coordenadas; a última parcela é o módulo do deslocamento espacial.'),
        ],
        why: 'Calcular em R³ preserva a variação vertical. Isso importa em subidas, descidas, saltos e pistas inclinadas, onde a distância horizontal XZ não representa todo o movimento do carro.',
        result: 'O resultado final tem três componentes: Δx, Δy e Δz. A magnitude 3D é a distância em linha reta entre as posições e inclui a altura.',
      };
    case 'combination':
      return {
        sourceIntro: `${sourcePrefix} Primeiro calcula-se Δ = P2 − P1; depois esse vetor é escrito na base canônica B = {(1,0),(0,1)}.`,
        sourceLines,
        cards: [
          valueCard('Deslocamento extraído', exercise.inputs.displacement_xz_m, 'Vetor obtido subtraindo a posição X/Z da amostra A da posição X/Z da amostra B.'),
          valueCard('Base usada', exercise.inputs.basis, 'A base canônica separa o plano em uma direção X e uma direção Z.'),
          valueCard('a e b', exercise.expected_result, 'Coeficientes que multiplicam as duas direções da base para reconstruir o deslocamento.'),
        ],
        why: 'Encontrar a e b mostra como uma mudança observada na pista é decomposta em componentes independentes. Essa é a ponte entre o vetor geométrico e suas coordenadas em uma base.',
        result: 'O resultado final são coordenadas: a mede quanto do deslocamento está na direção X e b quanto está na direção Z. Recombinar a(1,0)+b(0,1) deve devolver exatamente Δ.',
      };
    case 'combination_3d':
      return {
        sourceIntro: `${sourcePrefix} O deslocamento completo P2 − P1 é escrito na base canônica de R³, formada pelas direções X, Y e Z.`,
        sourceLines,
        cards: [
          valueCard('Deslocamento extraído', exercise.inputs.displacement_xyz_m, 'Vetor 3D obtido subtraindo as posições globais completas das duas amostras.'),
          valueCard('Base canônica de R³', exercise.inputs.basis, 'Três direções independentes: X, Y e Z.'),
          valueCard('a, b e c', exercise.expected_result, 'Coeficientes que reconstroem o deslocamento em cada eixo.'),
        ],
        why: 'Encontrar os três coeficientes mostra como uma posição espacial é decomposta sem perder a altura. É a extensão direta da combinação linear no plano para o espaço.',
        result: 'O resultado final são as coordenadas do deslocamento na base canônica: a corresponde a X, b a Y e c a Z. A recombinação deve devolver o vetor 3D original.',
      };
    case 'determinant':
      return {
        sourceIntro: `${sourcePrefix} A velocidade X/Z da amostra A forma a primeira linha da matriz e a velocidade X/Z da amostra B forma a segunda linha.`,
        sourceLines,
        cards: [
          valueCard('Velocidade X/Z · A', v1 ?? (exercise.inputs.matrix as ExerciseValue[] | undefined)?.[0] ?? null, 'Direção instantânea do movimento na amostra A, em m/s.'),
          valueCard('Velocidade X/Z · B', v2 ?? (exercise.inputs.matrix as ExerciseValue[] | undefined)?.[1] ?? null, 'Direção instantânea do movimento na amostra B, em m/s.'),
          valueCard('Matriz A', exercise.inputs.matrix, 'As duas velocidades organizadas como linhas para comparar suas direções.'),
        ],
        why: 'O determinante mede se as duas direções ocupam áreas diferentes no plano. Ele é a ferramenta rápida para detectar independência linear e saber se a matriz pode ser invertida.',
        result: 'O resultado final é um número assinado: módulo grande indica direções independentes; zero ou um valor muito pequeno indica vetores paralelos ou quase paralelos. Com velocidades, a unidade é m²/s².',
      };
    case 'basis_dimension': {
      const dimension = calculation && 'dimension' in calculation ? calculation.dimension : null;
      return {
        sourceIntro: `${sourcePrefix} v1 e v2 são as velocidades projetadas em X/Z; os módulos de velocidade exibidos na resolução ajudam a distinguir direção de intensidade.`,
        sourceLines,
        cards: [
          valueCard('v1 · amostra A', exercise.inputs.v1, 'Primeira direção observada, composta pelas componentes X e Z da velocidade.'),
          valueCard('v2 · amostra B', exercise.inputs.v2, 'Segunda direção observada, composta pelas componentes X e Z da velocidade.'),
          valueCard('Tolerância numérica', exercise.inputs.numeric_tolerance, 'Limite usado para tratar um determinante muito pequeno como dependência, considerando arredondamento e ruído da telemetria.'),
          valueCard('Dimensão calculada', dimension === null ? exercise.expected_result : dimension, 'Quantidade de direções independentes necessárias para gerar o subespaço formado por v1 e v2.'),
        ],
        why: 'Calcular a dimensão reduz dois vetores possivelmente redundantes ao número real de direções independentes. Isso informa se os dados geram apenas uma reta, o plano inteiro ou somente a origem.',
        result: dimension === 2
          ? 'O resultado final 2 significa que as duas velocidades são independentes e formam uma base do plano XZ.'
          : dimension === 1
            ? 'O resultado final 1 significa que existe apenas uma direção independente; o espaço gerado é uma reta, mesmo que tenham sido fornecidos dois vetores.'
            : 'O resultado final 0 significa que não há direção não nula; o espaço gerado contém somente o vetor zero.',
      };
    }
    case 'basis_dimension_3d': {
      const calculation3d = calculation as BasisDimension3DCalculation | undefined;
      const dimension = calculation3d?.dimension ?? exercise.expected_result;
      const numericDimension = typeof dimension === 'number' ? dimension : null;
      return {
        sourceIntro: `${sourcePrefix} v1, v2 e v3 vêm de três amostras diferentes e preservam as componentes X, Y e Z da velocidade, todas em m/s.`,
        sourceLines,
        cards: [
          valueCard(`v1 · amostra #${firstSequence}`, exercise.inputs.v1, 'Primeira direção observada no espaço, com componentes X, Y e Z.'),
          valueCard(`v2 · amostra #${secondSequence}`, exercise.inputs.v2, 'Segunda direção observada no espaço, com componentes X, Y e Z.'),
          valueCard(`v3 · amostra #${thirdSequence}`, exercise.inputs.v3, 'Terceira direção observada no espaço, com componentes X, Y e Z.'),
          valueCard('Determinante e tolerância', calculation3d ? { determinant: calculation3d.determinant, numeric_tolerance: calculation3d.numeric_tolerance } : null, 'O determinante testa se as três direções preenchem o espaço; a tolerância evita interpretar ruído arredondado como independência.'),
        ],
        why: 'Calcular o posto em R³ informa quantas direções independentes existem de fato. Isso diferencia uma reta (1), um plano (2), o espaço completo (3) e a origem (0).',
        result: numericDimension === 3
          ? 'O resultado final 3 significa que os três vetores são independentes e formam uma base de R³.'
          : numericDimension === 2
            ? 'O resultado final 2 significa que os vetores geram um plano dentro de R³; há três componentes, mas apenas duas direções independentes.'
            : numericDimension === 1
              ? 'O resultado final 1 significa que todos os vetores úteis apontam para uma única direção: uma reta em R³.'
              : 'O resultado final 0 significa que todos os vetores são nulos e o espaço gerado é somente a origem.',
      };
    }
    case 'subspace':
      return {
        sourceIntro: `${sourcePrefix} O vetor v vem da velocidade X/Z da amostra A. W não é uma nova medição: é o conjunto matemático de todos os múltiplos escalares desse vetor.`,
        sourceLines,
        cards: [
          valueCard('v · amostra A', exercise.inputs.v, 'Vetor gerador: indica a direção instantânea do carro no plano horizontal.'),
          valueCard('W = span{v}', exercise.inputs.W, 'Conjunto de todos os pontos t·v, com t real; geometricamente, uma reta pela origem.'),
          valueCard('Base e dimensão', calculation && 'basis' in calculation ? calculation.basis : exercise.expected_result, 'A base guarda os geradores independentes; a dimensão é a quantidade de vetores nessa base.'),
        ],
        why: 'Calcular se W é subespaço verifica as três propriedades fundamentais: conter o zero, ser fechado para soma e ser fechado para multiplicação por escalar. A dimensão resume quantas direções independentes existem em W.',
        result: 'O resultado final diz se todos os múltiplos de v formam um subespaço e quantas direções independentes ele possui. Para um gerador não nulo, a resposta é uma reta de dimensão 1; para v = 0, é o subespaço nulo de dimensão 0.',
      };
    case 'affine_subspace':
      return {
        sourceIntro: `${sourcePrefix} p é a posição X/Z da amostra A e v é a velocidade X/Z dessa mesma amostra. A reta é construída como W = {p + t·v}.`,
        sourceLines,
        cards: [
          valueCard('p · amostra A', exercise.inputs.p, 'Ponto inicial deslocado da origem, em metros, usado como translação da reta.'),
          valueCard('v · amostra A', exercise.inputs.v, 'Direção da reta, extraída da velocidade no plano X/Z.'),
          valueCard('Teste de subespaço', exercise.expected_result, 'A análise verifica principalmente se a reta contém a origem; sem a origem, não pode ser subespaço.'),
        ],
        why: 'Calcular esse teste distingue uma reta vetorial, que passa pela origem, de uma reta afim, que apenas é paralela a uma direção. Essa diferença é essencial para interpretar corretamente “dimensão” e fechamento.',
        result: 'O resultado final informa se W é subespaço. Se for verdadeiro, a dimensão é o número de direções independentes; se for falso, a reta ainda pode existir geometricamente, mas não tem dimensão de subespaço vetorial.',
      };
    case 'gauss':
      return {
        sourceIntro: `${sourcePrefix} As velocidades X/Z formam a matriz A. O vetor b não é uma leitura bruta: ele é calculado a partir de A para que o sistema tenha a solução didática (x,y) = (2,−1).`,
        sourceLines,
        cards: [
          valueCard('Matriz A · velocidades', exercise.inputs.matrix_A, 'Cada linha contém uma velocidade X/Z observada em uma amostra.'),
          valueCard('Vetor b · derivado', exercise.inputs.vector_b, 'Termos independentes calculados a partir de A; servem para montar um sistema verificável com os dados reais.'),
          valueCard('Variáveis x e y', '[x, y]', 'Coeficientes desconhecidos que combinam as duas linhas de A para produzir b.'),
        ],
        why: 'A eliminação de Gauss transforma as equações acopladas em uma forma que revela diretamente os coeficientes. É útil para verificar se as velocidades permitem uma solução única e para aprender a resolver combinações de dados.',
        result: 'O resultado final é o par (x,y). Ele não é uma nova velocidade: são os coeficientes que, multiplicados pelas linhas de A, reproduzem o vetor b. Como b foi construído para este exercício, a solução esperada é (2,−1) quando a matriz é invertível.',
      };
    case 'inverse':
      return {
        sourceIntro: `${sourcePrefix} A matriz é formada diretamente pelas duas velocidades X/Z selecionadas, uma em cada linha.`,
        sourceLines,
        cards: [
          valueCard('Matriz A · velocidades', exercise.inputs.matrix, 'Transforma coeficientes em uma combinação das duas direções observadas.'),
          valueCard('det(A)', v1 && v2 ? v1[0] * v2[1] - v1[1] * v2[0] : null, 'Verificação de que as direções são independentes; sem determinante não nulo, não existe inversa.'),
          valueCard('A⁻¹', exercise.expected_result, 'Matriz que desfaz a transformação de A quando multiplicada por ela.'),
        ],
        why: 'Calcular a inversa mostra se é possível recuperar unicamente os coeficientes a partir de uma combinação de velocidades. A condição central é det(A) diferente de zero.',
        result: 'O resultado final A⁻¹ é a transformação que desfaz A: A·A⁻¹ = I. Ele permite voltar de um vetor combinado para os coeficientes originais, desde que as duas direções sejam independentes.',
      };
    default:
      return {
        sourceIntro: sourcePrefix,
        sourceLines,
        cards: Object.entries(exercise.inputs).map(([label, value]) => valueCard(label, value, 'Valor fornecido pelo exercício e usado nas operações abaixo.')),
        why: 'O cálculo transforma leituras da telemetria em uma quantidade matemática que pode ser comparada, verificada e interpretada.',
        result: 'O resultado final é a consequência das operações aplicadas aos valores fornecidos; leia-o junto da unidade e da definição apresentada na questão.',
      };
  }
}

function ExerciseDataExplanation({ exercise, samples }: { exercise: Exercise; samples: TelemetrySample[] }) {
  const explanation = buildExerciseExplanation(exercise, samples);
  return <section className="math-exercise-explanation" aria-labelledby={`exercise-explanation-${exercise.topic}`}>
    <div className="math-explainer-heading">
      <span>LEITURA PEDAGÓGICA DOS DADOS</span>
      <h3 id={`exercise-explanation-${exercise.topic}`}>De onde vêm os valores e o que o resultado significa?</h3>
    </div>
    <p>{explanation.sourceIntro}</p>
    <div className="math-source-samples">
      <span className="math-context-label">AMOSTRAS BRUTAS USADAS</span>
      {explanation.sourceLines.map((line) => <p key={line}>{line}</p>)}
    </div>
    <div className="math-explanation-block">
      <span className="math-context-label">O QUE CADA VALOR REPRESENTA</span>
      <div className="math-explanation-cards">
        {explanation.cards.map((card) => <div className="math-explanation-card" key={card.label}>
          <span>{card.label}</span><strong>{card.value}</strong><small>{card.meaning}</small>
        </div>)}
      </div>
    </div>
    <div className="math-explanation-block">
      <span className="math-context-label">POR QUE ESTE CÁLCULO IMPORTA?</span>
      <p>{explanation.why}</p>
    </div>
    <div className="math-final-meaning">
      <span className="math-context-label">COMO LER O RESULTADO FINAL</span>
      <p>{explanation.result}</p>
    </div>
  </section>;
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

type DriftBandStatus = 'below' | 'within' | 'above' | 'unknown';

type DriftMetric = {
  label: string;
  value: string;
  reference: string;
  status: DriftBandStatus;
  explanation: string;
};

function classifyDriftBand(value: number | null, lower: number, upper: number): DriftBandStatus {
  if (value === null || !Number.isFinite(value)) return 'unknown';
  if (value < lower) return 'below';
  if (value > upper) return 'above';
  return 'within';
}

function driftStatusLabel(status: DriftBandStatus): string {
  return status === 'below' ? 'ABAIXO DA FAIXA' : status === 'above' ? 'ACIMA DA FAIXA' : status === 'within' ? 'NA FAIXA' : 'SEM LEITURA';
}

function signedAngleDifference(first: number, second: number): number {
  return Math.atan2(Math.sin(first - second), Math.cos(first - second));
}

function estimatedSideslipDegrees(sample: TelemetrySample): number | null {
  const [velocityX, , velocityZ] = sample.velocity_world_mps;
  const horizontalSpeed = Math.hypot(velocityX, velocityZ);
  if (!Number.isFinite(horizontalSpeed) || horizontalSpeed < 2) return null;
  const velocityHeading = Math.atan2(velocityZ, velocityX);
  return Math.abs(signedAngleDifference(velocityHeading, sample.heading_rad)) * 180 / Math.PI;
}

function DriftBenchmarkPanel({ exercise, samples }: { exercise: Exercise; samples: TelemetrySample[] }) {
  const selectedSamples = exercise.source_sequences
    .map((sequence) => sampleBySequence(samples, sequence))
    .filter((sample): sample is TelemetrySample => Boolean(sample));
  if (!selectedSamples.length) return null;

  const average = (values: number[]) => values.length ? values.reduce((total, value) => total + value, 0) / values.length : null;
  const speed = average(selectedSamples.map((sample) => sample.speed_kmh).filter(Number.isFinite));
  const sideslip = average(selectedSamples.map(estimatedSideslipDegrees).filter((value): value is number => value !== null));
  const throttle = average(selectedSamples.map((sample) => sample.throttle * 100).filter(Number.isFinite));
  const gears = [...new Set(selectedSamples.map((sample) => sample.gear))];
  const gearLabel = gears.length === 1 ? `${gears[0] > 0 ? gears[0] : 'N'}ª` : gears.map((gear) => gear > 0 ? `${gear}ª` : 'N').join(' → ');
  const metrics: DriftMetric[] = [
    {
      label: 'Sideslip estimado',
      value: sideslip === null ? '—' : `${formatNumber(sideslip, 1)}°`,
      reference: 'faixa didática: 8°–35°',
      status: classifyDriftBand(sideslip, 8, 35),
      explanation: 'Diferença entre a direção da velocidade horizontal e o heading do carro; não é o slip angle de cada pneu.',
    },
    {
      label: 'Acelerador médio',
      value: throttle === null ? '—' : `${formatNumber(throttle, 0)}%`,
      reference: 'faixa didática: 35%–90%',
      status: classifyDriftBand(throttle, 35, 90),
      explanation: 'Indica se há torque suficiente e progressivo para sustentar a rotação; 100% não significa automaticamente melhor controle.',
    },
    {
      label: 'Velocidade média',
      value: speed === null ? '—' : `${formatNumber(speed, 1)} km/h`,
      reference: 'mínimo prático: 20 km/h',
      status: classifyDriftBand(speed, 20, Number.POSITIVE_INFINITY),
      explanation: 'Abaixo disso, a estimativa de direção da velocidade fica pouco confiável para classificar um drift.',
    },
    {
      label: 'Marcha observada',
      value: gearLabel,
      reference: 'sem marcha universal; manter torque e evitar troca no meio',
      status: gears.length === 1 && gears[0] > 0 ? 'within' : 'unknown',
      explanation: 'A marcha adequada depende do torque, diferencial, pneus, velocidade e raio da curva do carro usado.',
    },
  ];

  const tips: string[] = [];
  if (sideslip === null) tips.push('Selecione amostras com pelo menos 2 m/s de velocidade horizontal para obter uma estimativa de sideslip.');
  else if (sideslip < 8) tips.push('O ângulo estimado está baixo: pratique uma entrada suave, transferência de peso progressiva e aumento gradual do acelerador.');
  else if (sideslip > 35) tips.push('O ângulo estimado está alto: alivie o acelerador progressivamente e faça a correção de direção mais cedo para recuperar estabilidade.');
  else tips.push('O ângulo está dentro da faixa didática: priorize constância de heading, velocidade e trajetória, não um ângulo máximo.');
  if (throttle !== null && throttle < 35) tips.push('O acelerador médio está baixo para sustentar a derrapagem; procure uma aplicação contínua, sem alternar entre zero e máximo.');
  if (throttle !== null && throttle > 90) tips.push('O acelerador está muito próximo do máximo: compare também temperatura, rotação e saída da curva antes de aumentar mais.');
  if (gears.length > 1) tips.push('Houve troca de marcha entre as amostras: teste uma marcha que mantenha o motor na faixa de torque sem trocar durante a fase de drift.');
  if (speed !== null && speed < 20) tips.push('A velocidade está baixa para esta referência; não interprete a faixa como uma meta para todas as curvas.');
  if (!tips.length) tips.push('Use esta leitura como ponto de partida e compare várias passagens na mesma curva para medir consistência.');

  return <section className="drift-benchmark" aria-labelledby={`drift-benchmark-${exercise.topic}`}>
    <div className="math-explainer-heading">
      <span>REFERÊNCIA DE TREINO · AMOSTRAS SELECIONADAS</span>
      <h3 id={`drift-benchmark-${exercise.topic}`}>Como esses valores se comparam a uma condução de drift?</h3>
    </div>
    <p className="drift-benchmark-intro">Não existe um ângulo, velocidade, marcha ou posição ideal universal. As bandas abaixo são apenas referências didáticas para comparar os valores extraídos desta questão; carro, pneus, superfície, raio, inclinação e fase da curva mudam o alvo.</p>
    <div className="drift-metric-grid">
      {metrics.map((metric) => <div className={`drift-metric drift-metric-${metric.status}`} key={metric.label}>
        <span>{metric.label}</span>
        <strong>{metric.value}</strong>
        <b>{driftStatusLabel(metric.status)}</b>
        <small>{metric.reference}</small>
        <p>{metric.explanation}</p>
      </div>)}
    </div>
    <div className="drift-benchmark-tips">
      <span className="math-context-label">COMO MELHORAR NESTA LEITURA</span>
      {tips.map((tip) => <p key={tip}>• {tip}</p>)}
    </div>
    <p className="drift-benchmark-limit">Limitação atual: a aplicação compara amostras e não conhece ainda a curvatura exata, linha ideal ou fase entrada–manutenção–saída da curva. Estudos de controle de drift tratam sideslip, yaw, velocidade e trajetória como variáveis acopladas; portanto, estes números não são uma prescrição de pilotagem.</p>
  </section>;
}

export function MathExercise({ streamId, samples, demo, publicMode }: {
  streamId: string; samples: TelemetrySample[]; demo: boolean; publicMode: boolean;
}) {
  const [topics, setTopics] = useState<LearningTopic[]>(demo ? demoTopics : []);
  const [topic, setTopic] = useState('displacement');
  const [aInput, setA] = useState<number | null>(null);
  const [bInput, setB] = useState<number | null>(null);
  const [cInput, setC] = useState<number | null>(null);
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [solutionTab, setSolutionTab] = useState<'result' | 'steps'>('steps');
  const [answer, setAnswer] = useState('');
  const [check, setCheck] = useState<AnswerCheck | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setTopic('displacement'); setA(null); setB(null); setC(null);
    setExercise(null); setExpanded(false); setAnswer(''); setCheck(null);
    setSolutionTab('steps');
  }, [streamId, demo]);

  useEffect(() => {
    if (demo) { setTopics(demoTopics); return; }
    let valid = true;
    getTopics(publicMode).then((x) => { if (valid) setTopics(x.topics); }).catch((exc: unknown) => {
      if (valid) setError(exc instanceof Error ? exc.message : 'Falha ao listar temas.');
    });
    return () => { valid = false; };
  }, [demo, publicMode]);

  const candidateSamples = useMemo(() => downsample(samples, 80), [samples]);
// Freeze choices when loading the window; live updates do not clear the student's answer.
  useEffect(() => {
    if (samples.length < 2) return;
    setA((old) => old !== null && samples.some((s) => s.sequence === old) ? old : samples[Math.max(0, Math.floor(samples.length * .2))].sequence);
    setB((old) => old !== null && samples.some((s) => s.sequence === old) ? old : samples[Math.max(0, Math.floor(samples.length * .8))].sequence);
    setC((old) => old !== null && samples.some((s) => s.sequence === old) ? old : samples[Math.max(0, Math.floor(samples.length * .5))].sequence);
  }, [samples]);
  const a = aInput ?? -1;
  const b = bInput ?? -1;
  const c = cInput ?? -1;
  const isLesson19Topic = topic.startsWith('lesson19_');
  const needsThreeSamples = !isLesson19Topic && topic === 'basis_dimension_3d';
  const choices = useMemo(() => [...new Set([...candidateSamples.map((s) => s.sequence), a, b, c])].filter((s) => s >= 0).sort((x, y) => x - y), [candidateSamples, a, b, c]);

  useEffect(() => {
    setExercise(null); setExpanded(false); setCheck(null); setAnswer('');
    setSolutionTab('steps');
    setError(null);
    if (isLesson19Topic) {
      if (demo) {
        setExercise(generateLesson19Exercise(topic, false));
        return;
      }
      let active = true;
      const timer = setTimeout(() => {
        setBusy(true);
        getExercise(streamId, topic, undefined, undefined, false, publicMode).then((x) => { if (active) setExercise(x); })
          .catch((exc: unknown) => { if (active) setError(exc instanceof Error ? exc.message : 'Exercício indisponível.'); })
          .finally(() => { if (active) setBusy(false); });
      }, 180);
      return () => { active = false; clearTimeout(timer); };
    }
    if (a < 0 || b < 0 || a === b || !samples.length || (needsThreeSamples && (c < 0 || c === a || c === b))) return;
    if (demo) { setExercise(generateDemoExercise(topic, a, b, false, needsThreeSamples ? c : undefined)); return; }
    let active = true;
    const timer = setTimeout(() => {
      setBusy(true);
      getExercise(streamId, topic, a, b, false, publicMode, needsThreeSamples ? c : undefined).then((x) => { if (active) setExercise(x); })
        .catch((exc: unknown) => { if (active) setError(exc instanceof Error ? exc.message : 'Exercício indisponível.'); })
        .finally(() => { if (active) setBusy(false); });
    }, 180);
    return () => { active = false; clearTimeout(timer); };
  }, [streamId, topic, a, b, c, demo, publicMode, needsThreeSamples]);

  async function reveal() {
    if (expanded) { setExpanded(false); return; }
    if (!exercise) return;
    setError(null);
    setBusy(true);
    try {
      const item = isLesson19Topic
        ? generateLesson19Exercise(topic, true)
        : demo
          ? generateDemoExercise(topic, a, b, true, needsThreeSamples ? c : undefined)
          : await getExercise(streamId, topic, a, b, true, publicMode, needsThreeSamples ? c : undefined);
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
      } : await checkExercise(streamId, topic, isLesson19Topic ? undefined : a, isLesson19Topic ? undefined : b, parsed, publicMode, needsThreeSamples ? c : undefined);
      setCheck(result);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Erro ao conferir a resposta.');
    } finally { setBusy(false); }
  }

  return <div className="math-flow">
    <div className={`math-config ${isLesson19Topic ? 'lesson19-topic-config' : ''}`}>
      <label><span>TEMA</span><select value={topic} onChange={(e) => setTopic(e.target.value)}>
        {topics.map((t) => <option key={t.id} value={t.id}>{t.title} (Aula {t.lessons.join(', ')})</option>)}
      </select></label>
      {!isLesson19Topic && <label><span>AMOSTRA A</span><select value={a} onChange={(e) => setA(Number(e.target.value))}>
        {choices.map((seq) => <option key={seq} value={seq}>#{seq}</option>)}
      </select></label>}
      {!isLesson19Topic && <label><span>AMOSTRA B</span><select value={b} onChange={(e) => setB(Number(e.target.value))}>
        {choices.map((seq) => <option key={seq} value={seq}>#{seq}</option>)}
      </select></label>}
      {needsThreeSamples && <label><span>AMOSTRA C</span><select value={c} onChange={(e) => setC(Number(e.target.value))}>
        {choices.map((seq) => <option key={seq} value={seq}>#{seq}</option>)}
      </select></label>}
    </div>
    {busy && <p className="muted small">Calculando ou consultando o backend…</p>}
    {!isLesson19Topic && (a === b || (needsThreeSamples && (c === a || c === b))) && <p className="inline-error">Escolha amostras diferentes.</p>}
    {!isLesson19Topic && needsThreeSamples && samples.length < 3 && <p className="inline-error">O exercício em R³ precisa de pelo menos três amostras.</p>}
    {error && <p className="inline-error" role="alert">{error}</p>}
    {exercise && <>
      <div className="exercise-head"><div className="exercise-icon"><BookOpen size={21}/></div><div><span>EXERCÍCIO · {exercise.lessons.map((i) => `AULA ${i}`).join(' / ')}</span><h2>{exercise.title}</h2></div></div>
      <p className="exercise-question">{exercise.question}</p>
      <div className="math-two-col">
        <div className="math-code-box"><span>VALORES FORNECIDOS</span><pre>{prettyJson(exercise.inputs)}</pre></div>
        <div className="math-code-box answer-box"><span>RESULTADO ESPERADO</span><pre>{prettyJson(exercise.expected_result)}</pre></div>
      </div>
      {!isLesson19Topic && <>
        <ExerciseDataExplanation exercise={exercise} samples={samples}/>
        {exercise.topic === 'subspace' && exercise.calculation && <SubspaceExplanation calculation={exercise.calculation as ExerciseCalculation}/>}
        {exercise.topic === 'basis_dimension' && exercise.calculation && <BasisDimensionExplanation calculation={exercise.calculation as BasisDimensionCalculation}/>}
        <DriftBenchmarkPanel exercise={exercise} samples={samples}/>
      </>}
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
