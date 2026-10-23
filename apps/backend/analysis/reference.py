"""Comparação GEOMÉTRICA com referência gravada, nunca linha ótima presumida."""
from __future__ import annotations

import math
from typing import Iterable


def closest_distance_xz(position: list[float], polyline: list[list[float]]) -> float:
    """Menor distância euclidiana XZ a um segmento da polilinha de referência."""
    x, z = position[0], position[2]
    if not polyline:
        raise ValueError("A trajetória de referência está vazia")
    if len(polyline) == 1:
        return math.hypot(x - polyline[0][0], z - polyline[0][2])
    best = math.inf
    for first, second in zip(polyline, polyline[1:]):
        x1, z1 = first[0], first[2]
        dx, dz = second[0] - x1, second[2] - z1
        length_sq = dx * dx + dz * dz
        t = max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / length_sq)) if length_sq > 0 else 0.0
        nearest_x, nearest_z = x1 + t * dx, z1 + t * dz
        best = min(best, math.hypot(x - nearest_x, z - nearest_z))
    return best


def compare_with_reference(
    actual: list[list[float]], reference: list[list[float]],
) -> dict:
    if not actual or not reference:
        raise ValueError("Ambas as trajetórias precisam ter coordenadas")
    distances = [closest_distance_xz(position, reference) for position in actual]
    return {
        "evaluated_points": len(distances),
        "mean_distance_m": round(sum(distances) / len(distances), 3),
        "max_distance_m": round(max(distances), 3),
        "per_point_distance_m": [round(value, 3) for value in distances],
        "actual_path_xz_m": [[v[0], v[2]] for v in actual],
        "reference_path_xz_m": [[v[0], v[2]] for v in reference],
        "method": "shortest-distance-to-recorded-polyline (XZ)",
        "limitations": (
            "A referência é uma tentativa gravada, não uma trajetória ótima. "
            "Busca o trecho espacial mais próximo, sem alinhamento de progresso, tempo ou RPM; "
            "pode associar trechos errados quando trajetórias se cruzam. "
            "Avalie curvas equivalentes e refine a comparação com limites da pista."
        ),
    }
