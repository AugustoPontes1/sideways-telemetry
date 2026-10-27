"""Exercises generated from real telemetry; solutions are hidden by default."""
from __future__ import annotations

import math
from typing import Any


class ExerciseUnavailable(ValueError):
    """The topic or samples do not support a well-defined math exercise."""


TOPICS = {
    "displacement": {"title": "Deslocamento no plano XZ", "lessons": [12]},
    "combination": {"title": "Combinação linear na base canônica", "lessons": [15, 17]},
    "determinant": {"title": "Determinante de vetores velocidade", "lessons": [8, 16]},
    "basis_dimension": {"title": "Base e dimensão geradas por dois vetores", "lessons": [16, 17, 18]},
    "subspace": {"title": "Subespaço gerado por uma direção", "lessons": [12, 13, 15]},
    "affine_subspace": {"title": "Reta deslocada: é subespaço?", "lessons": [12, 13, 14]},
    "gauss": {"title": "Sistema linear com dados do veículo", "lessons": [4, 5, 6, 7]},
    "inverse": {"title": "Inversa de matriz 2x2", "lessons": [8, 9, 11]},
}


def p3(x: float) -> float:
    number = round(float(x), 3)
    return number if number else 0.0


def vec_xz(values: list[float]) -> tuple[float, float]:
    """Project onto global X,Z axes (assumed horizontal until verified)."""
    return p3(values[0]), p3(values[2])


def determinant2(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


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
                      *, reveal: bool = False) -> dict:
    if topic not in TOPICS:
        raise ExerciseUnavailable(f"Tema desconhecido; use um de: {', '.join(TOPICS)}")
    if sample_a.sequence == sample_b.sequence:
        raise ExerciseUnavailable("Selecione duas amostras distintas")
    definition = TOPICS[topic]
    exercise = {
        "topic": topic,
        "title": definition["title"],
        "lessons": definition["lessons"],
        "source_sequences": [sample_a.sequence, sample_b.sequence],
    }
    steps: list[str] = []

    p1, p2 = vec_xz(sample_a.position_world_m), vec_xz(sample_b.position_world_m)
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
