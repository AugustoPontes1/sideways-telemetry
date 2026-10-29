"""Exercises generated from real telemetry; solutions are hidden by default."""
from __future__ import annotations

import math
from typing import Any


class ExerciseUnavailable(ValueError):
    """The topic or samples do not support a well-defined math exercise."""


TOPICS = {
    "displacement": {"title": "Deslocamento no plano XZ", "lessons": [12]},
    "displacement_3d": {"title": "Deslocamento no espaço R³", "lessons": [12, 13]},
    "combination": {"title": "Combinação linear na base canônica", "lessons": [15, 17]},
    "combination_3d": {"title": "Combinação linear na base canônica de R³", "lessons": [15, 17]},
    "determinant": {"title": "Determinante de vetores velocidade", "lessons": [8, 16]},
    "basis_dimension": {"title": "Base e dimensão geradas por dois vetores", "lessons": [16, 17, 18]},
    "basis_dimension_3d": {"title": "Base e dimensão no espaço R³", "lessons": [16, 17, 18]},
    "subspace": {"title": "Subespaço gerado por uma direção", "lessons": [12, 13, 15]},
    "affine_subspace": {"title": "Reta deslocada: é subespaço?", "lessons": [12, 13, 14]},
    "gauss": {"title": "Sistema linear com dados do veículo", "lessons": [4, 5, 6, 7]},
    "inverse": {"title": "Inversa de matriz 2x2", "lessons": [8, 9, 11]},
    "lesson19_coordinates": {"title": "Coordenadas de vetores em R² e R³", "lessons": [19]},
    "lesson19_polynomials": {"title": "Coordenadas de polinômios em P₁ e P₂", "lessons": [19]},
    "lesson19_reconstruction": {"title": "Reconstrução de vetores e polinômios", "lessons": [19]},
    "lesson19_change_of_basis": {"title": "Coordenadas e mudança de base", "lessons": [19]},
}


LESSON19_EXERCISES = {
    "lesson19_01": {
        "question": "Seja β = {(1, 0), (0, 1)}. Determine as coordenadas de v = (3, −2) em relação à base β.",
        "inputs": {"basis": [[1, 0], [0, 1]], "vector": [3, -2]},
        "expected_result": {"a": 3, "b": -2},
        "solution": ["Escreva v = a(1,0) + b(0,1).", "A combinação resulta em (a,b) = (3,−2).", "Logo, [v]β = (3,−2)ᵀ."],
    },
    "lesson19_02": {
        "question": "Seja β = {(1, 1), (1, −1)}. Determine as coordenadas de v = (4, 2) em relação à base β.",
        "inputs": {"basis": [[1, 1], [1, -1]], "vector": [4, 2]},
        "expected_result": {"a": 3, "b": 1},
        "solution": ["Escreva (4,2) = a(1,1) + b(1,−1).", "Comparando as coordenadas: a+b=4 e a−b=2.", "Somando as equações, 2a=6; então a=3 e b=1.", "Logo, [v]β = (3,1)ᵀ."],
    },
    "lesson19_03": {
        "question": "Seja β = {(1, 2), (2, 1)}. Encontre [v]β para v = (5, 4).",
        "inputs": {"basis": [[1, 2], [2, 1]], "vector": [5, 4]},
        "expected_result": {"a": 1, "b": 2},
        "solution": ["Escreva (5,4) = a(1,2) + b(2,1).", "O sistema é a+2b=5 e 2a+b=4.", "Resolvendo, b=2 e a=1.", "Portanto, [v]β = (1,2)ᵀ."],
    },
    "lesson19_04": {
        "question": "Seja β = {(1, 1, 0), (0, 1, 1), (1, 0, 1)}. Determine as coordenadas de v = (2, −1, 5) em relação à base β.",
        "inputs": {"basis": [[1, 1, 0], [0, 1, 1], [1, 0, 1]], "vector": [2, -1, 5]},
        "expected_result": {"a": -2, "b": 1, "c": 4},
        "solution": ["Escreva v = a(1,1,0) + b(0,1,1) + c(1,0,1).", "Comparando coordenadas: a+c=2, a+b=−1 e b+c=5.", "A soma das três equações dá a+b+c=3; daí c=4, a=−2 e b=1.", "Logo, [v]β = (−2,1,4)ᵀ."],
    },
    "lesson19_05": {
        "question": "Seja β = {(1, 0, 1), (1, 1, 0), (0, 0, 1)}. Determine as coordenadas de v = (3, 4, 5) em relação à base β.",
        "inputs": {"basis": [[1, 0, 1], [1, 1, 0], [0, 0, 1]], "vector": [3, 4, 5]},
        "expected_result": {"a": -1, "b": 4, "c": 6},
        "solution": ["Escreva (3,4,5) = a(1,0,1) + b(1,1,0) + c(0,0,1).", "Comparando coordenadas: a+b=3, b=4 e a+c=5.", "Assim, a=−1 e c=6.", "Portanto, [v]β = (−1,4,6)ᵀ."],
    },
    "lesson19_06": {
        "question": "Seja β = {1+t, 1−t}. Determine as coordenadas de p(t) = 5+t em relação à base β.",
        "inputs": {"basis": ["1+t", "1−t"], "polynomial": "5+t"},
        "expected_result": {"a": 3, "b": 2},
        "solution": ["Escreva 5+t = a(1+t) + b(1−t).", "Comparando os coeficientes: a+b=5 e a−b=1.", "Resolvendo o sistema, a=3 e b=2.", "Logo, [p]β = (3,2)ᵀ."],
    },
    "lesson19_07": {
        "question": "Seja β = {1, 1+t, t²}. Determine as coordenadas de p(t) = 3+2t+t² em relação à base β.",
        "inputs": {"basis": ["1", "1+t", "t²"], "polynomial": "3+2t+t²"},
        "expected_result": {"a": 1, "b": 2, "c": 1},
        "solution": ["Escreva 3+2t+t² = a·1 + b(1+t) + c·t².", "O coeficiente de t² dá c=1; o de t dá b=2.", "No termo constante, a+b=3, então a=1.", "Portanto, [p]β = (1,2,1)ᵀ."],
    },
    "lesson19_08": {
        "question": "Seja β = {(1, 1), (2, 1)}. Sabendo que [v]β = (2, 3)ᵀ, determine o vetor v na base canônica.",
        "inputs": {"basis": [[1, 1], [2, 1]], "coordinates_beta": [2, 3]},
        "expected_result": {"x": 8, "y": 5},
        "solution": ["Reconstrua o vetor: v = 2(1,1) + 3(2,1).", "Calculando componente a componente, v = (2+6, 2+3).", "Assim, v = (8,5) na base canônica."],
    },
    "lesson19_09": {
        "question": "Seja β = {(1, 0, 1), (0, 1, 1), (1, 1, 0)}. Sabendo que [v]β = (1, 2, 3)ᵀ, determine o vetor v.",
        "inputs": {"basis": [[1, 0, 1], [0, 1, 1], [1, 1, 0]], "coordinates_beta": [1, 2, 3]},
        "expected_result": {"x": 4, "y": 5, "z": 3},
        "solution": ["Reconstrua v = 1(1,0,1) + 2(0,1,1) + 3(1,1,0).", "Somando as componentes, v = (1+3, 2+3, 1+2).", "Logo, v = (4,5,3)."],
    },
    "lesson19_10": {
        "question": "Seja β = {1+t, t, 1−t+t²}. Sabendo que [p]β = (2, −1, 3)ᵀ, determine o polinômio p(t).",
        "inputs": {"basis": ["1+t", "t", "1−t+t²"], "coordinates_beta": [2, -1, 3]},
        "expected_result": {"constant": 5, "t": -2, "t2": 3},
        "solution": ["Reconstrua p(t) = 2(1+t) − t + 3(1−t+t²).", "Agrupando os termos constantes, lineares e quadráticos: p(t)=5−2t+3t².", "Portanto, as coordenadas na base canônica de P₂ são (5,−2,3)ᵀ."],
    },
    "lesson19_11": {
        "question": "Sejam β = {(1, 1), (1, −1)} e β′ = {(1, 0), (0, 1)}. Sabendo que [v]β = (2, 1)ᵀ, determine [v]β′.",
        "inputs": {"basis_beta": [[1, 1], [1, -1]], "basis_beta_prime": [[1, 0], [0, 1]], "coordinates_beta": [2, 1]},
        "expected_result": {"x": 3, "y": 1},
        "solution": ["Reconstrua o vetor na base canônica: v = 2(1,1) + 1(1,−1).", "A soma é v=(3,1).", "Como β′ é a base canônica, [v]β′=(3,1)ᵀ."],
    },
    "lesson19_12": {
        "question": "Sejam β = {(1, 2), (3, 1)} e β′ = {(1, 0), (0, 1)}. Determine a matriz de mudança de base [I]β′β.",
        "inputs": {"basis_beta": [[1, 2], [3, 1]], "basis_beta_prime": [[1, 0], [0, 1]]},
        "expected_result": [[-0.2, 0.6], [0.4, -0.2]],
        "solution": ["A matriz que leva coordenadas de β′ para β é formada pelas coordenadas dos vetores de β′ na base β.", "A matriz da base β é B=[[1,3],[2,1]], então [I]β′β = B⁻¹.", "Como det(B)=−5, B⁻¹ = (1/−5)[[1,−3],[−2,1]].", "Resposta final: [I]β′β = [[−1/5, 3/5],[2/5, −1/5]]."],
    },
    "lesson19_13": {
        "question": "Sejam β = {(2, 1), (1, 3)} e β′ = {(1, 0), (0, 1)}. Encontre [I]β′β e [I]ββ′.",
        "inputs": {"basis_beta": [[2, 1], [1, 3]], "basis_beta_prime": [[1, 0], [0, 1]]},
        "expected_result": {"I_betaPrime_to_beta": [[0.6, -0.2], [-0.2, 0.4]], "I_beta_to_betaPrime": [[2, 1], [1, 3]]},
        "solution": ["A matriz da base β é B=[[2,1],[1,3]].", "A mudança de β para a base canônica é B: [I]ββ′=[[2,1],[1,3]].", "Como det(B)=5, B⁻¹=[[3/5,−1/5],[−1/5,2/5]].", "Resposta final: [I]β′β=[[3/5,−1/5],[−1/5,2/5]] e [I]ββ′=[[2,1],[1,3]]."],
    },
    "lesson19_14": {
        "question": "Sejam β = {(1, 1), (1, −1)} e β′ = {(1, 0), (0, 1)}. Determine uma matriz de mudança de base de β para β′.",
        "inputs": {"basis_beta": [[1, 1], [1, -1]], "basis_beta_prime": [[1, 0], [0, 1]]},
        "expected_result": [[1, 1], [1, -1]],
        "solution": ["Para levar coordenadas de β para β′, coloque os vetores de β como colunas na base β′.", "Como β′ é a base canônica, a matriz é [[1,1],[1,−1]].", "Essa matriz transforma [v]β em [v]β′."],
    },
    "lesson19_coordinates": {
        "question": "Calcule as coordenadas dos dois vetores fornecidos em suas bases: um exemplo em R² e outro em R³.",
        "inputs": {
            "exemplo_R2": {"basis": [[1, 2], [2, 1]], "vector": [5, 4]},
            "exemplo_R3": {"basis": [[1, 0, 1], [1, 1, 0], [0, 0, 1]], "vector": [3, 4, 5]},
        },
        "expected_result": {"coordenadas_R2": [1, 2], "coordenadas_R3": [-1, 4, 6]},
        "solution": [
            "Coordenadas são os coeficientes que multiplicam os vetores da base para reconstruir o vetor dado.",
            "No R²: (5,4) = a(1,2) + b(2,1). O sistema é a+2b=5 e 2a+b=4; portanto a=1 e b=2.",
            "Logo, no primeiro exemplo [v]β=(1,2)ᵀ. O vetor continua sendo (5,4); apenas sua descrição mudou para a base β.",
            "No R³: (3,4,5) = a(1,0,1) + b(1,1,0) + c(0,0,1). Comparando componentes: a+b=3, b=4 e a+c=5.",
            "Assim, a=−1, b=4 e c=6; portanto [v]β=(−1,4,6)ᵀ.",
            "Na base canônica, as coordenadas coincidem diretamente com as componentes do vetor. Em uma base não canônica, é necessário resolver o sistema.",
            "Resposta final: coordenadas_R2=(1,2) e coordenadas_R3=(−1,4,6).",
        ],
    },
    "lesson19_polynomials": {
        "question": "Encontre as coordenadas dos dois polinômios nas bases fornecidas: um exemplo em P₁ e outro em P₂.",
        "inputs": {
            "exemplo_P1": {"basis": ["1+t", "1−t"], "polynomial": "5+t"},
            "exemplo_P2": {"basis": ["1", "1+t", "t²"], "polynomial": "3+2t+t²"},
        },
        "expected_result": {"coordenadas_P1": [3, 2], "coordenadas_P2": [1, 2, 1]},
        "solution": [
            "Em um espaço de polinômios, cada elemento da base é um polinômio e as coordenadas são os coeficientes da combinação linear.",
            "Em P₁: 5+t = a(1+t)+b(1−t). Comparando termos, a+b=5 e a−b=1; logo a=3 e b=2.",
            "Em P₂: 3+2t+t² = a·1+b(1+t)+c·t². O termo t² dá c=1; o termo t dá b=2; o termo constante dá a+b=3, então a=1.",
            "A ordem das coordenadas segue a ordem da base. Por isso [5+t]β=(3,2) e [3+2t+t²]β=(1,2,1).",
            "Resposta final: coordenadas_P1=(3,2) e coordenadas_P2=(1,2,1).",
        ],
    },
    "lesson19_reconstruction": {
        "question": "Reconstrua os vetores e o polinômio a partir de suas coordenadas nas respectivas bases.",
        "inputs": {
            "vetor_R2": {"basis": [[1, 1], [2, 1]], "coordinates_beta": [2, 3]},
            "vetor_R3": {"basis": [[1, 0, 1], [0, 1, 1], [1, 1, 0]], "coordinates_beta": [1, 2, 3]},
            "polinomio": {"basis": ["1+t", "t", "1−t+t²"], "coordinates_beta": [2, -1, 3]},
        },
        "expected_result": {"vetor_R2": [8, 5], "vetor_R3": [4, 5, 3], "polinomio": "5−2t+3t²"},
        "solution": [
            "Reconstruir é fazer o caminho inverso: multiplicar cada vetor ou polinômio da base pela coordenada correspondente e somar.",
            "R²: v=2(1,1)+3(2,1)=(2+6,2+3)=(8,5).",
            "R³: v=1(1,0,1)+2(0,1,1)+3(1,1,0)=(1+3,2+3,1+2)=(4,5,3).",
            "Polinômio: p(t)=2(1+t)−t+3(1−t+t²)=5−2t+3t².",
            "Esse cálculo mostra que as coordenadas são suficientes para recuperar exatamente o objeto original quando a base é conhecida.",
            "Resposta final: vetor_R2=(8,5), vetor_R3=(4,5,3) e p(t)=5−2t+3t².",
        ],
    },
    "lesson19_change_of_basis": {
        "question": "Converta coordenadas entre β e β′ e encontre as matrizes de mudança nos dois sentidos.",
        "inputs": {
            "base_beta": [[1, 1], [1, -1]],
            "base_beta_prime": [[1, 0], [0, 1]],
            "coordenadas_beta": [2, 1],
        },
        "expected_result": {
            "coordenadas_beta_prime": [3, 1],
            "matriz_beta_para_beta_prime": [[1, 1], [1, -1]],
            "matriz_beta_prime_para_beta": [[0.5, 0.5], [0.5, -0.5]],
        },
        "solution": [
            "Para converter [v]β para [v]β′, primeiro reconstrua o vetor: v=2(1,1)+1(1,−1)=(3,1). Como β′ é canônica, [v]β′=(3,1).",
            "A matriz que leva coordenadas de β para β′ coloca os vetores de β como colunas escritas em β′: Pβ→β′=[[1,1],[1,−1]].",
            "Para o caminho inverso, calcule a inversa: det(P)=−2 e P⁻¹=[[(1/2),(1/2)],[(1/2),(−1/2)]].",
            "Multiplicando as duas matrizes obtemos a identidade; por isso uma desfaz exatamente a mudança feita pela outra.",
            "Resposta final: [v]β′=(3,1), Pβ→β′=[[1,1],[1,−1]] e Pβ′→β=[[0.5,0.5],[0.5,−0.5]].",
        ],
    },
}


def p3(x: float) -> float:
    number = round(float(x), 3)
    return number if number else 0.0


def vec_xz(values: list[float]) -> tuple[float, float]:
    """Project onto global X,Z axes (assumed horizontal until verified)."""
    return p3(values[0]), p3(values[2])


def vec_xyz(values: list[float]) -> tuple[float, float, float]:
    return p3(values[0]), p3(values[1]), p3(values[2])


def determinant2(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


def determinant3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    c: tuple[float, float, float],
) -> float:
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def cross3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vector_norm3(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def numeric_rank3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    c: tuple[float, float, float],
) -> int:
    vectors = (a, b, c)
    norms = [vector_norm3(vector) for vector in vectors]
    if max(norms) < 1e-8:
        return 0
    pairs = ((a, b), (a, c), (b, c))
    if max(vector_norm3(cross3(first, second)) for first, second in pairs) <= 1e-6 * max(max(norms) ** 2, 1.0):
        return 1
    if abs(determinant3(a, b, c)) <= 1e-6 * max(norms[0] * norms[1] * norms[2], 1.0):
        return 2
    return 3


def independent_basis3(
    vectors: tuple[tuple[float, float, float], ...],
) -> list[list[float]]:
    basis: list[tuple[float, float, float]] = []
    for vector in vectors:
        if vector_norm3(vector) < 1e-8:
            continue
        if not basis:
            basis.append(vector)
        elif len(basis) == 1:
            if vector_norm3(cross3(basis[0], vector)) > 1e-6 * max(vector_norm3(basis[0]) * vector_norm3(vector), 1.0):
                basis.append(vector)
        elif abs(determinant3(basis[0], basis[1], vector)) > 1e-6 * max(
            vector_norm3(basis[0]) * vector_norm3(basis[1]) * vector_norm3(vector), 1.0
        ):
            basis.append(vector)
        if len(basis) == 3:
            break
    return [list(vector) for vector in basis]


def scale2(vector: tuple[float, float], factor: float) -> list[float]:
    return [p3(factor * vector[0]), p3(factor * vector[1])]


def numeric_rank2(a: tuple[float, float], b: tuple[float, float]) -> int:
    na, nb = math.hypot(*a), math.hypot(*b)
    if max(na, nb) < 1e-8:
        return 0
    if min(na, nb) < 1e-8:
        return 1
    if abs(determinant2(a, b)) <= 1e-6 * na * nb:
        return 1
    return 2


def generate_exercise(topic: str, sample_a: Any, sample_b: Any,
                      sample_c: Any | None = None, *, reveal: bool = False) -> dict:
    if topic not in TOPICS:
        raise ExerciseUnavailable(f"Tema desconhecido; use um de: {', '.join(TOPICS)}")
    if topic.startswith("lesson19_"):
        definition = LESSON19_EXERCISES.get(topic)
        if definition is None:
            raise ExerciseUnavailable("Exercício da Aula 19 indisponível")
        exercise = {
            "topic": topic,
            "title": TOPICS[topic]["title"],
            "lessons": TOPICS[topic]["lessons"],
            "source_sequences": [],
            **definition,
            "note": "Exercício fixo da Aula 19: resolva igualando o vetor ou polinômio à combinação linear dos elementos da base.",
        }
        if not reveal:
            exercise.pop("solution", None)
        return exercise
    if sample_a.sequence == sample_b.sequence:
        raise ExerciseUnavailable("Selecione duas amostras distintas")
    if topic == "basis_dimension_3d":
        if sample_c is None:
            raise ExerciseUnavailable("Selecione três amostras para o exercício em R³")
        if sample_c.sequence in {sample_a.sequence, sample_b.sequence}:
            raise ExerciseUnavailable("As três amostras precisam ser distintas")
    definition = TOPICS[topic]
    exercise = {
        "topic": topic,
        "title": definition["title"],
        "lessons": definition["lessons"],
        "source_sequences": [sample_a.sequence, sample_b.sequence],
    }
    steps: list[str] = []

    p1, p2 = vec_xz(sample_a.position_world_m), vec_xz(sample_b.position_world_m)
    p1_xyz, p2_xyz = vec_xyz(sample_a.position_world_m), vec_xyz(sample_b.position_world_m)
    v1, v2 = vec_xz(sample_a.velocity_world_mps), vec_xz(sample_b.velocity_world_mps)
    dx, dz = p3(p2[0] - p1[0]), p3(p2[1] - p1[1])

    if topic == "displacement":
        exercise["question"] = "Calcule o vetor deslocamento e sua magnitude no plano horizontal XZ."
        exercise["inputs"] = {"P1_xz_m": p1, "P2_xz_m": p2}
        exercise["expected_result"] = {
            "delta_x_m": dx, "delta_z_m": dz,
            "distance_horizontal_m": p3(math.hypot(dx, dz)),
        }
        steps = [
            f"Use a subtração vetorial P2 - P1: ({p2[0]} - {p1[0]}, {p2[1]} - {p1[1]}).",
            f"O vetor deslocamento é ({dx}, {dz}) m.",
            f"Seu módulo horizontal é sqrt(({dx})² + ({dz})²) = {p3(math.hypot(dx, dz))} m.",
            "Esse deslocamento é entre dois instantes, não a distância total percorrida na curva.",
            f"Resposta final: Δ=({dx}, {dz}) m e ||Δ||={p3(math.hypot(dx, dz))} m.",
        ]
    elif topic == "displacement_3d":
        delta = tuple(p2_xyz[index] - p1_xyz[index] for index in range(3))
        distance = p3(vector_norm3(delta))
        exercise["question"] = "Calcule o vetor deslocamento e sua magnitude no espaço R³."
        exercise["inputs"] = {"P1_xyz_m": list(p1_xyz), "P2_xyz_m": list(p2_xyz)}
        exercise["expected_result"] = {
            "delta_x_m": delta[0], "delta_y_m": delta[1], "delta_z_m": delta[2],
            "distance_3d_m": distance,
        }
        steps = [
            f"Use P2-P1=({p2_xyz[0]}-{p1_xyz[0]}, {p2_xyz[1]}-{p1_xyz[1]}, {p2_xyz[2]}-{p1_xyz[2]}).",
            f"O vetor deslocamento é ({delta[0]}, {delta[1]}, {delta[2]}) m.",
            f"Seu módulo é sqrt(({delta[0]})²+({delta[1]})²+({delta[2]})²)={distance} m.",
            "A componente Y representa a variação de altura; ela não pode ser descartada em uma pista com subida ou descida.",
            f"Resposta final: Δ=({delta[0]}, {delta[1]}, {delta[2]}) m e ||Δ||={distance} m.",
        ]
    elif topic == "combination":
        exercise["question"] = "Ache a,b tais que P2-P1 = a(1,0)+b(0,1)."
        exercise["inputs"] = {"displacement_xz_m": [dx, dz], "basis": [[1, 0], [0, 1]]}
        exercise["expected_result"] = {"a": dx, "b": dz}
        steps = [
            "A base canônica ordenada do plano é B=((1,0),(0,1)).",
            f"a(1,0)+b(0,1)=(a,b)=({dx},{dz}).",
            f"Comparando coordenadas: a={dx} e b={dz}.",
            f"Resposta final: a={dx} e b={dz}.",
        ]
    elif topic == "combination_3d":
        delta = tuple(p2_xyz[index] - p1_xyz[index] for index in range(3))
        exercise["question"] = "Ache a,b,c tais que P2-P1 = a(1,0,0)+b(0,1,0)+c(0,0,1)."
        exercise["inputs"] = {
            "displacement_xyz_m": list(delta),
            "basis": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        }
        exercise["expected_result"] = {"a": delta[0], "b": delta[1], "c": delta[2]}
        steps = [
            "A base canônica de R³ é B=((1,0,0),(0,1,0),(0,0,1)).",
            f"a(1,0,0)+b(0,1,0)+c(0,0,1)=(a,b,c)=({delta[0]},{delta[1]},{delta[2]}).",
            f"Comparando coordenadas: a={delta[0]}, b={delta[1]} e c={delta[2]}.",
            f"Resposta final: (a,b,c)=({delta[0]},{delta[1]},{delta[2]}).",
        ]
    elif topic == "determinant":
        det = p3(determinant2(v1, v2))
        exercise["question"] = "Calcule o determinante da matriz cujas linhas são estes vetores velocidade XZ."
        exercise["inputs"] = {"matrix": [list(v1), list(v2)], "unit": "m/s"}
        exercise["expected_result"] = det
        steps = [
            f"A=[[{v1[0]},{v1[1]}],[{v2[0]},{v2[1]}]].",
            f"det(A)=({v1[0]})({v2[1]})-({v1[1]})({v2[0]})={det}.",
            "Determinante próximo de zero sugere direções quase dependentes, mas dados reais têm ruído.",
            f"Resposta final: det(A)={det}.",
        ]
    elif topic == "basis_dimension":
        rank = numeric_rank2(v1, v2)
        determinant = p3(determinant2(v1, v2))
        basis_vector = v1 if math.hypot(*v1) >= 1e-8 else v2
        basis = [list(v1), list(v2)] if rank == 2 else [list(basis_vector)] if rank == 1 else []
        exercise["question"] = "Estime a dimensão do subespaço gerado por estes dois vetores no plano XZ."
        exercise["inputs"] = {"v1": list(v1), "v2": list(v2), "numeric_tolerance": 1e-6}
        exercise["expected_result"] = rank
        exercise["calculation"] = {
            "sample_sequences": [sample_a.sequence, sample_b.sequence],
            "sample_speed_mps": [
                p3(getattr(sample_a, "speed_mps", math.hypot(*v1))),
                p3(getattr(sample_b, "speed_mps", math.hypot(*v2))),
            ],
            "v1": list(v1),
            "v2": list(v2),
            "matrix": [list(v1), list(v2)],
            "determinant": determinant,
            "basis": basis,
            "dimension": rank,
            "numeric_tolerance": 1e-6,
        }
        steps = [
            f"Os vetores da simulação são v1=({v1[0]}, {v1[1]}) e v2=({v2[0]}, {v2[1]}) m/s.",
            f"Monte A=[[{v1[0]},{v1[1]}],[{v2[0]},{v2[1]}]].",
            f"det(A)=({v1[0]})({v2[1]})-({v1[1]})({v2[0]})={determinant}; compare com a tolerância 1e-6.",
            f"O posto numérico é {rank}, igual à dimensão do espaço gerado por v1 e v2.",
            f"Uma base numérica é {basis}.",
            "A dimensão é aproximada por causa de arredondamentos e ruído da telemetria.",
            f"Resposta final: dimensão(span{{v1,v2}})={rank}.",
        ]
    elif topic == "basis_dimension_3d":
        vector_a = vec_xyz(sample_a.velocity_world_mps)
        vector_b = vec_xyz(sample_b.velocity_world_mps)
        vector_c = vec_xyz(sample_c.velocity_world_mps)
        vectors = (vector_a, vector_b, vector_c)
        exercise["source_sequences"] = [sample_a.sequence, sample_b.sequence, sample_c.sequence]
        rank = numeric_rank3(*vectors)
        determinant = p3(determinant3(*vectors))
        basis = independent_basis3(vectors)
        exercise["question"] = "Estime a dimensão do subespaço gerado por três velocidades no espaço R³."
        exercise["inputs"] = {
            "v1": list(vector_a), "v2": list(vector_b), "v3": list(vector_c),
            "numeric_tolerance": 1e-6,
        }
        exercise["expected_result"] = rank
        exercise["calculation"] = {
            "sample_sequences": [sample_a.sequence, sample_b.sequence, sample_c.sequence],
            "sample_speed_mps": [
                p3(getattr(sample_a, "speed_mps", vector_norm3(vector_a))),
                p3(getattr(sample_b, "speed_mps", vector_norm3(vector_b))),
                p3(getattr(sample_c, "speed_mps", vector_norm3(vector_c))),
            ],
            "vectors": [list(vector) for vector in vectors],
            "matrix": [list(vector) for vector in vectors],
            "determinant": determinant,
            "basis": basis,
            "dimension": rank,
            "numeric_tolerance": 1e-6,
        }
        steps = [
            f"v1 vem da amostra #{sample_a.sequence}: {vector_a} m/s; v2 vem da amostra #{sample_b.sequence}: {vector_b} m/s; v3 vem da amostra #{sample_c.sequence}: {vector_c} m/s.",
            f"Monte A={exercise['calculation']['matrix']}.",
            f"det(A)={determinant}; compare o valor normalizado com a tolerância 1e-6.",
            f"O posto numérico é {rank}; ele é a dimensão do subespaço gerado pelos três vetores.",
            f"Uma base numérica é {basis if basis else '∅'}.",
            "Em R³, dimensão 3 significa três direções independentes; dimensão 2 é um plano, dimensão 1 é uma reta e dimensão 0 é somente a origem.",
            f"Resposta final: dimensão(span{{v1,v2,v3}})={rank}.",
        ]
    elif topic == "affine_subspace":
        rank = 1 if math.hypot(*v1) > 1e-8 else 0
        if rank:
            is_subspace = abs(determinant2(p1, v1)) <= 1e-6 * max(math.hypot(*p1) * math.hypot(*v1), 1.0)
        else:
            is_subspace = math.hypot(*p1) <= 1e-8
        exercise["question"] = (
            "Considere W={p+t*v | t real}, com p e v no plano XZ. "
            "Verifique se W é subespaço de R²."
        )
        exercise["inputs"] = {"p": list(p1), "v": list(v1)}
        exercise["expected_result"] = {"is_subspace": is_subspace, "dimension": rank if is_subspace else None}
        if is_subspace:
            if rank:
                parameter = -p1[0] / v1[0] if abs(v1[0]) >= abs(v1[1]) else -p1[1] / v1[1]
                zero_check = [p3(p1[0] + parameter * v1[0]), p3(p1[1] + parameter * v1[1])]
                steps = [
                    f"Os valores da simulação são p=({p1[0]}, {p1[1]}) e v=({v1[0]}, {v1[1]}) no plano XZ.",
                    f"W={{p+t·v}}={{({p1[0]}, {p1[1]})+t·({v1[0]}, {v1[1]}) | t∈ℝ}}.",
                    f"det(p,v)=({p1[0]})({v1[1]})-({p1[1]})({v1[0]})={p3(determinant2(p1, v1))}; os vetores são colineares.",
                    f"Com t={p3(parameter)}, p+t·v=({zero_check[0]}, {zero_check[1]}), portanto o vetor zero pertence a W.",
                    "Como p é múltiplo de v, W coincide com span(v); a soma e a multiplicação por escalar permanecem nessa mesma direção.",
                    f"Resposta final: W é subespaço e dimensão(W)={rank}.",
                ]
            else:
                steps = [
                    f"Os valores da simulação são p=({p1[0]}, {p1[1]}) e v=(0,0).",
                    "Logo W contém somente o ponto (0,0), que é o subespaço nulo.",
                    "A base do subespaço nulo é vazia, portanto sua dimensão é 0.",
                    "Resposta final: W é subespaço e dimensão(W)=0.",
                ]
        else:
            if rank:
                steps = [
                    f"Os valores da simulação são p=({p1[0]}, {p1[1]}) e v=({v1[0]}, {v1[1]}).",
                    f"det(p,v)=({p1[0]})({v1[1]})-({p1[1]})({v1[0]})={p3(determinant2(p1, v1))}≠0; p não está na direção de v.",
                    "Assim não existe t real capaz de fazer p+t·v=(0,0); o vetor zero não pertence a W.",
                    "Como 0 não pertence a W, W não é subespaço e não recebe dimensão vetorial.",
                    "Resposta final: W não é subespaço e sua dimensão vetorial é indefinida.",
                ]
            else:
                steps = [
                    f"Os valores da simulação são p=({p1[0]}, {p1[1]}) e v=(0,0).",
                    "W contém apenas o ponto p, que não é o vetor zero.",
                    "Como 0 não pertence a W, W não é subespaço e não recebe dimensão vetorial.",
                    "Resposta final: W não é subespaço e sua dimensão vetorial é indefinida.",
                ]
    elif topic == "subspace":
        rank = 1 if math.hypot(*v1) > 1e-8 else 0
        exercise["question"] = "W=span{v}. Mostre que W é um subespaço de R² e encontre sua dimensão."
        exercise["inputs"] = {
            "v": list(v1),
            "W": f"span{{v}} = {{t·({v1[0]}, {v1[1]}) | t ∈ ℝ}}",
        }
        exercise["expected_result"] = {"is_subspace": True, "dimension": rank}
        exercise["calculation"] = {
            "direction_vector": list(v1),
            "unit": "m/s · velocidade projetada nos eixos X/Z",
            "norm": p3(math.hypot(*v1)),
            "angle_deg_from_x": p3(math.degrees(math.atan2(v1[1], v1[0]))) if rank else None,
            "parametric_form": f"W = {{t·({v1[0]}, {v1[1]}) | t ∈ ℝ}}",
            "multiples": [
                {"t": factor, "vector": scale2(v1, factor)}
                for factor in (-1, 0, 1, 2)
            ],
            "basis": [list(v1)] if rank else [],
        }
        if rank:
            example_u = scale2(v1, 2)
            example_w = scale2(v1, -1)
            example_sum = scale2(v1, 1)
            example_scalar = scale2(v1, 6)
            steps = [
                f"Os valores da simulação dão v=({v1[0]}, {v1[1]}) m/s, com ||v||={p3(math.hypot(*v1))}; como v≠(0,0), ele é um gerador não nulo.",
                f"W=span{{v}}={{t·({v1[0]}, {v1[1]}) | t∈ℝ}}: cada ponto de W é um múltiplo de v.",
                "Vetor zero: 0·v=(0,0), então (0,0)∈W.",
                f"Exemplo numérico: escolha a=2 e b=-1. u=a·v=({example_u[0]}, {example_u[1]}) e w=b·v=({example_w[0]}, {example_w[1]}).",
                f"Soma: u+w=({example_u[0]}, {example_u[1]})+({example_w[0]}, {example_w[1]})=({example_sum[0]}, {example_sum[1]})=1·v, portanto o resultado continua em W.",
                f"Outro exemplo: com k=3, k·u=3·({example_u[0]}, {example_u[1]})=({example_scalar[0]}, {example_scalar[1]})=6·v, também em W.",
                "Os valores a=2, b=-1 e k=3 ilustram a regra; para quaisquer a,b,k reais, u+w=(a+b)·v e k·u=(ka)·v.",
                f"Dimensão é a quantidade de vetores de uma base. Aqui B={{v}}=({v1[0]}, {v1[1]}) é uma base com 1 vetor, porque v é não nulo e gera todo W.",
                "Resposta final: W é subespaço, a base é {v} e dimensão(W)=1.",
            ]
        else:
            steps = [
                "Os valores da simulação dão v=(0,0).",
                "W=span{v} contém somente (0,0), o subespaço nulo.",
                "Sua base é vazia; como a dimensão é o número de vetores da base, dimensão(W)=0.",
                "Resposta final: W é subespaço nulo e dimensão(W)=0.",
            ]
    elif topic in ("gauss", "inverse"):
        matrix = [list(v1), list(v2)]
        a, b = v1
        c, d = v2
        det = determinant2(v1, v2)
        norm_scale = max(math.hypot(*v1) * math.hypot(*v2), 1.0)
        if abs(det) < 1e-3 * norm_scale:
            raise ExerciseUnavailable(
                "Matriz quase singular; selecione instantes com direções de movimento diferentes"
            )
        if topic == "inverse":
            exercise["question"] = "Calcule a inversa da matriz 2x2 formada pelos vetores velocidade."
            exercise["inputs"] = {"matrix": matrix}
            exercise["expected_result"] = [
                [p3(d / det), p3(-b / det)],
                [p3(-c / det), p3(a / det)],
            ]
            steps = [
                f"A=[[{a},{b}],[{c},{d}]] e det(A)=({a})({d})-({b})({c})={p3(det)}, que é diferente de 0.",
                "Para A=[[a,b],[c,d]], A^(-1)=(1/det(A))*[[d,-b],[-c,a]].",
                f"Substituindo os valores: A^(-1)=(1/{p3(det)})*[[{d}, {-b}], [{-c}, {a}]]={exercise['expected_result']}.",
                f"A multiplicação A*A^(-1) retorna a matriz identidade; resposta final: A^(-1)={exercise['expected_result']}.",
            ]
        else:
            rhs = [p3(2 * a - b), p3(2 * c - d)]
            exercise["question"] = "Resolva o sistema linear A*[x,y]^T=b usando eliminação de Gauss."
            exercise["inputs"] = {"matrix_A": matrix, "vector_b": rhs}
            exercise["expected_result"] = [2.0, -1.0]
            steps = [
                f"O sistema numérico é {a}x+({b})y={rhs[0]} e {c}x+({d})y={rhs[1]}.",
                f"A matriz ampliada é [[{a},{b}|{rhs[0]}],[{c},{d}|{rhs[1]}]]. Após a eliminação de Gauss, obtemos x=2 e y=-1.",
                f"Conferência na primeira equação: {a}·2+({b})·(-1)={rhs[0]}; na segunda: {c}·2+({d})·(-1)={rhs[1]}.",
                "Como as duas equações são satisfeitas e det(A) != 0, a solução é única.",
                "Resposta final: (x,y)=(2,-1).",
            ]
    exercise["note"] = (
        "Dados provenientes das projeções X/Z em coordenadas globais; "
        "o sentido positivo dos eixos do jogo ainda requer validação em campo."
    )
    if reveal:
        exercise["solution"] = steps
    return exercise


def compare_answer(expected: Any, answer: Any) -> bool:
    """Use explicit tolerance for telemetry numbers; require exact integers and booleans."""
    if type(expected) is bool:
        return type(answer) is bool and expected == answer
    if type(expected) in (int, float):
        if type(answer) not in (int, float) or not math.isfinite(answer):
            return False
        if type(expected) is int:
            return type(answer) is int and expected == answer
        return math.isclose(expected, answer, abs_tol=0.02, rel_tol=1e-3)
    if isinstance(expected, dict):
        return isinstance(answer, dict) and expected.keys() == answer.keys() and all(
            compare_answer(v, answer[k]) for k, v in expected.items()
        )
    if isinstance(expected, (list, tuple)):
        return isinstance(answer, list) and len(expected) == len(answer) and all(
            compare_answer(v, a) for v, a in zip(expected, answer)
        )
    return expected == answer
