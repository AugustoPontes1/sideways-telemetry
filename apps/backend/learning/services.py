"""Exercícios gerados de telemetria real; solução oculta por padrão."""
from __future__ import annotations

import math
from typing import Any


class ExerciseUnavailable(ValueError):
    """Tema ou amostras não permitem um exercício matemático bem definido."""


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
    """Projeção nos eixos globais X,Z (assumidos horizontais até validar)."""
    return p3(values[0]), p3(values[2])


def determinant2(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


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
        ]
    elif topic == "combination":
        exercise["question"] = "Ache a,b tais que P2-P1 = a(1,0)+b(0,1)."
        exercise["inputs"] = {"displacement_xz_m": [dx, dz], "basis": [[1, 0], [0, 1]]}
        exercise["expected_result"] = {"a": dx, "b": dz}
        steps = [
            "A base canônica ordenada do plano é B=((1,0),(0,1)).",
            f"a(1,0)+b(0,1)=(a,b)=({dx},{dz}).",
            f"Comparando coordenadas: a={dx} e b={dz}.",
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
        ]
    elif topic == "basis_dimension":
        rank = numeric_rank2(v1, v2)
        exercise["question"] = "Estime a dimensão do subespaço gerado por estes dois vetores no plano XZ."
        exercise["inputs"] = {"v1": list(v1), "v2": list(v2), "numeric_tolerance": 1e-6}
        exercise["expected_result"] = rank
        steps = [
            "Monte A com os vetores velocidade como linhas ou colunas.",
            f"det(A)={p3(determinant2(v1, v2))}; compare com as normas e tolerância numérica.",
            f"O posto numérico é {rank}, igual à dimensão do espaço gerado.",
            "A dimensão é aproximada por causa de arredondamentos e ruído da telemetria.",
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
            steps = [
                "Como p pertence a span(v), W coincide com span(v).",
                "O vetor zero pertence a W, e combinações lineares permanecem em W.",
                f"Portanto W é um subespaço de dimensão {rank}.",
            ]
        else:
            steps = [
                "Teste primeiro o vetor zero: existe t tal que p + t*v = (0,0)?",
                "Não existe esse t porque p não pertence a span(v).",
                "Como 0 não pertence a W, W não é subespaço. Não faz sentido atribuir dimensão vetorial a W.",
            ]
    elif topic == "subspace":
        rank = 1 if math.hypot(*v1) > 1e-8 else 0
        exercise["question"] = "W=span{v}. Mostre que W é um subespaço de R² e encontre sua dimensão."
        exercise["inputs"] = {"v": list(v1), "W": "{t*v | t real}"}
        exercise["expected_result"] = {"is_subspace": True, "dimension": rank}
        steps = [
            "O vetor zero pertence a W porque 0*v=(0,0).",
            "Se u=a*v e w=b*v, então u+w=(a+b)*v também pertence a W.",
            "Para todo escalar k, k*u=(k*a)*v pertence a W.",
            f"Logo W é subespaço. Sua dimensão é {rank} (vetor gerador {'não nulo' if rank else 'nulo'}).",
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
                f"det(A)=ad-bc={p3(det)}, que é diferente de 0.",
                "Para A=[[a,b],[c,d]], A^(-1)=(1/det(A))*[[d,-b],[-c,a]].",
                f"Divida os quatro elementos por {p3(det)} e confira A*A^(-1)=I.",
            ]
        else:
            rhs = [p3(2 * a - b), p3(2 * c - d)]
            exercise["question"] = "Resolva o sistema linear A*[x,y]^T=b usando eliminação de Gauss."
            exercise["inputs"] = {"matrix_A": matrix, "vector_b": rhs}
            exercise["expected_result"] = [2.0, -1.0]
            steps = [
                "Monte a matriz ampliada [A|b] e, se necessário, troque as linhas para criar um pivô.",
                "Elimine a primeira incógnita da segunda equação e faça substituição retroativa.",
                "Como det(A) != 0, o sistema tem solução única: x=2 e y=-1.",
                "Confira substituindo os valores nas duas equações originais.",
            ]
    exercise["note"] = (
        "Dados provenientes das projeções X/Z em coordenadas globais; "
        "o sentido positivo dos eixos do jogo ainda requer validação em campo."
    )
    if reveal:
        exercise["solution"] = steps
    return exercise


def compare_answer(expected: Any, answer: Any) -> bool:
    """Tolerância explícita para números da telemetria; inteiro e bool exatos."""
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
