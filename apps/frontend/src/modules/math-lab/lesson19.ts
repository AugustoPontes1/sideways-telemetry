import type { Exercise, ExerciseValue, LearningTopic } from '../../lib/types';

export const lesson19Topics: LearningTopic[] = [
  { id: 'lesson19_coordinates', title: 'Coordenadas de vetores em R² e R³', lessons: [19] },
  { id: 'lesson19_polynomials', title: 'Coordenadas de polinômios em P₁ e P₂', lessons: [19] },
  { id: 'lesson19_reconstruction', title: 'Reconstrução de vetores e polinômios', lessons: [19] },
  { id: 'lesson19_change_of_basis', title: 'Coordenadas e mudança de base', lessons: [19] },
];

type Lesson19Definition = {
  title: string;
  question: string;
  inputs: Record<string, ExerciseValue>;
  expected_result: ExerciseValue;
  solution: string[];
};

const definitions: Record<string, Lesson19Definition> = {
  lesson19_01: {
    title: 'Coordenadas na base canônica de R²',
    question: 'Seja β = {(1, 0), (0, 1)}. Determine as coordenadas de v = (3, −2) em relação à base β.',
    inputs: { basis: [[1, 0], [0, 1]], vector: [3, -2] },
    expected_result: { a: 3, b: -2 },
    solution: ['Escreva v = a(1,0) + b(0,1).', 'A combinação resulta em (a,b) = (3,−2).', 'Logo, [v]β = (3,−2)ᵀ.'],
  },
  lesson19_02: {
    title: 'Coordenadas em uma base oblíqua de R²',
    question: 'Seja β = {(1, 1), (1, −1)}. Determine as coordenadas de v = (4, 2) em relação à base β.',
    inputs: { basis: [[1, 1], [1, -1]], vector: [4, 2] },
    expected_result: { a: 3, b: 1 },
    solution: ['Escreva (4,2) = a(1,1) + b(1,−1).', 'Comparando as coordenadas: a+b=4 e a−b=2.', 'Somando as equações, 2a=6; então a=3 e b=1.', 'Logo, [v]β = (3,1)ᵀ.'],
  },
  lesson19_03: {
    title: 'Coordenadas de vetor em R²',
    question: 'Seja β = {(1, 2), (2, 1)}. Encontre [v]β para v = (5, 4).',
    inputs: { basis: [[1, 2], [2, 1]], vector: [5, 4] },
    expected_result: { a: 1, b: 2 },
    solution: ['Escreva (5,4) = a(1,2) + b(2,1).', 'O sistema é a+2b=5 e 2a+b=4.', 'Resolvendo, b=2 e a=1.', 'Portanto, [v]β = (1,2)ᵀ.'],
  },
  lesson19_04: {
    title: 'Coordenadas em R³',
    question: 'Seja β = {(1, 1, 0), (0, 1, 1), (1, 0, 1)}. Determine as coordenadas de v = (2, −1, 5) em relação à base β.',
    inputs: { basis: [[1, 1, 0], [0, 1, 1], [1, 0, 1]], vector: [2, -1, 5] },
    expected_result: { a: -2, b: 1, c: 4 },
    solution: ['Escreva v = a(1,1,0) + b(0,1,1) + c(1,0,1).', 'Comparando coordenadas: a+c=2, a+b=−1 e b+c=5.', 'A soma das três equações dá a+b+c=3; daí c=4, a=−2 e b=1.', 'Logo, [v]β = (−2,1,4)ᵀ.'],
  },
  lesson19_05: {
    title: 'Coordenadas em R³ com base não canônica',
    question: 'Seja β = {(1, 0, 1), (1, 1, 0), (0, 0, 1)}. Determine as coordenadas de v = (3, 4, 5) em relação à base β.',
    inputs: { basis: [[1, 0, 1], [1, 1, 0], [0, 0, 1]], vector: [3, 4, 5] },
    expected_result: { a: -1, b: 4, c: 6 },
    solution: ['Escreva (3,4,5) = a(1,0,1) + b(1,1,0) + c(0,0,1).', 'Comparando coordenadas: a+b=3, b=4 e a+c=5.', 'Assim, a=−1 e c=6.', 'Portanto, [v]β = (−1,4,6)ᵀ.'],
  },
  lesson19_06: {
    title: 'Coordenadas de polinômio em P₁',
    question: 'Seja β = {1+t, 1−t}. Determine as coordenadas de p(t) = 5+t em relação à base β.',
    inputs: { basis: ['1+t', '1−t'], polynomial: '5+t' },
    expected_result: { a: 3, b: 2 },
    solution: ['Escreva 5+t = a(1+t) + b(1−t).', 'Comparando os coeficientes: a+b=5 e a−b=1.', 'Resolvendo o sistema, a=3 e b=2.', 'Logo, [p]β = (3,2)ᵀ.'],
  },
  lesson19_07: {
    title: 'Coordenadas em P₂',
    question: 'Seja β = {1, 1+t, t²}. Determine as coordenadas de p(t) = 3+2t+t² em relação à base β.',
    inputs: { basis: ['1', '1+t', 't²'], polynomial: '3+2t+t²' },
    expected_result: { a: 1, b: 2, c: 1 },
    solution: ['Escreva 3+2t+t² = a·1 + b(1+t) + c·t².', 'O coeficiente de t² dá c=1; o de t dá b=2.', 'No termo constante, a+b=3, então a=1.', 'Portanto, [p]β = (1,2,1)ᵀ.'],
  },
  lesson19_08: {
    title: 'Reconstrução do vetor pela base',
    question: 'Seja β = {(1, 1), (2, 1)}. Sabendo que [v]β = (2, 3)ᵀ, determine o vetor v na base canônica.',
    inputs: { basis: [[1, 1], [2, 1]], coordinates_beta: [2, 3] },
    expected_result: { x: 8, y: 5 },
    solution: ['Reconstrua o vetor: v = 2(1,1) + 3(2,1).', 'Calculando componente a componente, v = (2+6, 2+3).', 'Assim, v = (8,5) na base canônica.'],
  },
  lesson19_09: {
    title: 'Reconstrução do vetor em R³',
    question: 'Seja β = {(1, 0, 1), (0, 1, 1), (1, 1, 0)}. Sabendo que [v]β = (1, 2, 3)ᵀ, determine o vetor v.',
    inputs: { basis: [[1, 0, 1], [0, 1, 1], [1, 1, 0]], coordinates_beta: [1, 2, 3] },
    expected_result: { x: 4, y: 5, z: 3 },
    solution: ['Reconstrua v = 1(1,0,1) + 2(0,1,1) + 3(1,1,0).', 'Somando as componentes, v = (1+3, 2+3, 1+2).', 'Logo, v = (4,5,3).'],
  },
  lesson19_10: {
    title: 'Reconstrução de polinômio',
    question: 'Seja β = {1+t, t, 1−t+t²}. Sabendo que [p]β = (2, −1, 3)ᵀ, determine o polinômio p(t).',
    inputs: { basis: ['1+t', 't', '1−t+t²'], coordinates_beta: [2, -1, 3] },
    expected_result: { constant: 5, t: -2, t2: 3 },
    solution: ['Reconstrua p(t) = 2(1+t) − t + 3(1−t+t²).', 'Agrupando os termos constantes, lineares e quadráticos: p(t)=5−2t+3t².', 'Portanto, as coordenadas na base canônica de P₂ são (5,−2,3)ᵀ.'],
  },
  lesson19_11: {
    title: 'Coordenadas entre duas bases',
    question: 'Sejam β = {(1, 1), (1, −1)} e β′ = {(1, 0), (0, 1)}. Sabendo que [v]β = (2, 1)ᵀ, determine [v]β′.',
    inputs: { basis_beta: [[1, 1], [1, -1]], basis_beta_prime: [[1, 0], [0, 1]], coordinates_beta: [2, 1] },
    expected_result: { x: 3, y: 1 },
    solution: ['Reconstrua o vetor na base canônica: v = 2(1,1) + 1(1,−1).', 'A soma é v=(3,1).', 'Como β′ é a base canônica, [v]β′=(3,1)ᵀ.'],
  },
  lesson19_12: {
    title: 'Matriz de mudança de base',
    question: 'Sejam β = {(1, 2), (3, 1)} e β′ = {(1, 0), (0, 1)}. Determine a matriz de mudança de base [I]β′β.',
    inputs: { basis_beta: [[1, 2], [3, 1]], basis_beta_prime: [[1, 0], [0, 1]] },
    expected_result: [[-0.2, 0.6], [0.4, -0.2]],
    solution: ['A matriz que leva coordenadas de β′ para β é formada pelas coordenadas dos vetores de β′ na base β.', 'A matriz da base β é B=[[1,3],[2,1]], então [I]β′β = B⁻¹.', 'Como det(B)=−5, B⁻¹ = (1/−5)[[1,−3],[−2,1]].', 'Resposta final: [I]β′β = [[−1/5, 3/5],[2/5, −1/5]].'],
  },
  lesson19_13: {
    title: 'Matriz e matriz inversa de mudança',
    question: 'Sejam β = {(2, 1), (1, 3)} e β′ = {(1, 0), (0, 1)}. Encontre [I]β′β e [I]ββ′.',
    inputs: { basis_beta: [[2, 1], [1, 3]], basis_beta_prime: [[1, 0], [0, 1]] },
    expected_result: {
      I_betaPrime_to_beta: [[0.6, -0.2], [-0.2, 0.4]],
      I_beta_to_betaPrime: [[2, 1], [1, 3]],
    },
    solution: ['A matriz da base β é B=[[2,1],[1,3]].', 'A mudança de β para a base canônica é B: [I]ββ′=[[2,1],[1,3]].', 'Como det(B)=5, B⁻¹=[[3/5,−1/5],[−1/5,2/5]].', 'Resposta final: [I]β′β=[[3/5,−1/5],[−1/5,2/5]] e [I]ββ′=[[2,1],[1,3]].'],
  },
  lesson19_14: {
    title: 'Mudança da base β para β′',
    question: 'Sejam β = {(1, 1), (1, −1)} e β′ = {(1, 0), (0, 1)}. Determine uma matriz de mudança de base de β para β′.',
    inputs: { basis_beta: [[1, 1], [1, -1]], basis_beta_prime: [[1, 0], [0, 1]] },
    expected_result: [[1, 1], [1, -1]],
    solution: ['Para levar coordenadas de β para β′, coloque os vetores de β como colunas na base β′.', 'Como β′ é a base canônica, a matriz é [[1,1],[1,−1]].', 'Essa matriz transforma [v]β em [v]β′.'],
  },
  lesson19_coordinates: {
    title: 'Coordenadas de vetores em R² e R³',
    question: 'Calcule as coordenadas dos dois vetores fornecidos em suas bases: um exemplo em R² e outro em R³.',
    inputs: {
      exemplo_R2: { basis: [[1, 2], [2, 1]], vector: [5, 4] },
      exemplo_R3: { basis: [[1, 0, 1], [1, 1, 0], [0, 0, 1]], vector: [3, 4, 5] },
    },
    expected_result: { coordenadas_R2: [1, 2], coordenadas_R3: [-1, 4, 6] },
    solution: [
      'Coordenadas são os coeficientes que multiplicam os vetores da base para reconstruir o vetor dado.',
      'No R²: (5,4) = a(1,2) + b(2,1). O sistema é a+2b=5 e 2a+b=4; portanto a=1 e b=2.',
      'Logo, no primeiro exemplo [v]β=(1,2)ᵀ. O vetor continua sendo (5,4); apenas sua descrição mudou para a base β.',
      'No R³: (3,4,5) = a(1,0,1) + b(1,1,0) + c(0,0,1). Comparando componentes: a+b=3, b=4 e a+c=5.',
      'Assim, a=−1, b=4 e c=6; portanto [v]β=(−1,4,6)ᵀ.',
      'Na base canônica, as coordenadas coincidem diretamente com as componentes do vetor. Em uma base não canônica, é necessário resolver o sistema.',
      'Resposta final: coordenadas_R2=(1,2) e coordenadas_R3=(−1,4,6).',
    ],
  },
  lesson19_polynomials: {
    title: 'Coordenadas de polinômios em P₁ e P₂',
    question: 'Encontre as coordenadas dos dois polinômios nas bases fornecidas: um exemplo em P₁ e outro em P₂.',
    inputs: {
      exemplo_P1: { basis: ['1+t', '1−t'], polynomial: '5+t' },
      exemplo_P2: { basis: ['1', '1+t', 't²'], polynomial: '3+2t+t²' },
    },
    expected_result: { coordenadas_P1: [3, 2], coordenadas_P2: [1, 2, 1] },
    solution: [
      'Em um espaço de polinômios, cada elemento da base é um polinômio e as coordenadas são os coeficientes da combinação linear.',
      'Em P₁: 5+t = a(1+t)+b(1−t). Comparando termos, a+b=5 e a−b=1; logo a=3 e b=2.',
      'Em P₂: 3+2t+t² = a·1+b(1+t)+c·t². O termo t² dá c=1; o termo t dá b=2; o termo constante dá a+b=3, então a=1.',
      'A ordem das coordenadas segue a ordem da base. Por isso [5+t]β=(3,2) e [3+2t+t²]β=(1,2,1).',
      'Resposta final: coordenadas_P1=(3,2) e coordenadas_P2=(1,2,1).',
    ],
  },
  lesson19_reconstruction: {
    title: 'Reconstrução de vetores e polinômios',
    question: 'Reconstrua os vetores e o polinômio a partir de suas coordenadas nas respectivas bases.',
    inputs: {
      vetor_R2: { basis: [[1, 1], [2, 1]], coordinates_beta: [2, 3] },
      vetor_R3: { basis: [[1, 0, 1], [0, 1, 1], [1, 1, 0]], coordinates_beta: [1, 2, 3] },
      polinomio: { basis: ['1+t', 't', '1−t+t²'], coordinates_beta: [2, -1, 3] },
    },
    expected_result: { vetor_R2: [8, 5], vetor_R3: [4, 5, 3], polinomio: '5−2t+3t²' },
    solution: [
      'Reconstruir é fazer o caminho inverso: multiplicar cada vetor ou polinômio da base pela coordenada correspondente e somar.',
      'R²: v=2(1,1)+3(2,1)=(2+6,2+3)=(8,5).',
      'R³: v=1(1,0,1)+2(0,1,1)+3(1,1,0)=(1+3,2+3,1+2)=(4,5,3).',
      'Polinômio: p(t)=2(1+t)−t+3(1−t+t²)=5−2t+3t².',
      'Esse cálculo mostra que as coordenadas são suficientes para recuperar exatamente o objeto original quando a base é conhecida.',
      'Resposta final: vetor_R2=(8,5), vetor_R3=(4,5,3) e p(t)=5−2t+3t².',
    ],
  },
  lesson19_change_of_basis: {
    title: 'Coordenadas e mudança de base',
    question: 'Converta coordenadas entre β e β′ e encontre as matrizes de mudança nos dois sentidos.',
    inputs: {
      base_beta: [[1, 1], [1, -1]],
      base_beta_prime: [[1, 0], [0, 1]],
      coordenadas_beta: [2, 1],
    },
    expected_result: {
      coordenadas_beta_prime: [3, 1],
      matriz_beta_para_beta_prime: [[1, 1], [1, -1]],
      matriz_beta_prime_para_beta: [[0.5, 0.5], [0.5, -0.5]],
    },
    solution: [
      'Para converter [v]β para [v]β′, primeiro reconstrua o vetor: v=2(1,1)+1(1,−1)=(3,1). Como β′ é canônica, [v]β′=(3,1).',
      'A matriz que leva coordenadas de β para β′ coloca os vetores de β como colunas escritas em β′: Pβ→β′=[[1,1],[1,−1]].',
      'Para o caminho inverso, calcule a inversa: det(P)=−2 e P⁻¹=[[(1/2),(1/2)],[(1/2),(−1/2)]].',
      'Multiplicando as duas matrizes obtemos a identidade; por isso uma desfaz exatamente a mudança feita pela outra.',
      'Resposta final: [v]β′=(3,1), Pβ→β′=[[1,1],[1,−1]] e Pβ′→β=[[0.5,0.5],[0.5,−0.5]].',
    ],
  },
};

export function generateLesson19Exercise(topic: string, reveal = false): Exercise {
  const definition = definitions[topic];
  const topicInfo = lesson19Topics.find((item) => item.id === topic);
  if (!definition || !topicInfo) throw new Error('Tema da Aula 19 desconhecido.');
  return {
    topic,
    title: topicInfo.title,
    lessons: topicInfo.lessons,
    source_sequences: [],
    question: definition.question,
    inputs: definition.inputs,
    expected_result: definition.expected_result,
    note: 'Exercício fixo da Aula 19: resolva igualando o vetor ou polinômio à combinação linear dos elementos da base.',
    ...(reveal ? { solution: definition.solution } : {}),
  };
}
