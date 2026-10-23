"""Solve systems Ax=b; report unique/infinitely many/inconsistent solutions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .matrices import as_matrix, rref, EPS
from .vectors import as_vector

@dataclass(frozen=True)
class LinearSolution:
    kind: Literal["unique", "infinite", "inconsistent"]
    particular: NDArray[np.float64] | None
    nullspace_basis: NDArray[np.float64]
    free_columns: tuple[int, ...]
    rank: int
    # All solutions when consistent: particular + nullspace_basis @ parameters


def nullspace(a: ArrayLike, *, tol: float = EPS) -> NDArray[np.float64]:
    """Columns form a nullspace basis, shape (n, dimension)."""
    m = as_matrix(a)
    reduced = rref(m, tol=tol)
    pivots = reduced.pivot_columns
    free = [c for c in range(m.shape[1]) if c not in pivots]
    vectors = np.zeros((m.shape[1], len(free)))
    for j, col in enumerate(free):
        vectors[col, j] = 1.0
        for row, pivot in enumerate(pivots):
            vectors[pivot, j] = -reduced.matrix[row, col]
    return vectors


def solve(a: ArrayLike, b: ArrayLike, *, tol: float = EPS) -> LinearSolution:
    m = as_matrix(a); target = as_vector(b, dim=m.shape[0])
    augmented = rref(np.column_stack([m, target]), tol=tol)
    n = m.shape[1]
    inconsistent = any(
        bool(np.all(np.abs(row[:n]) <= tol) and abs(row[n]) > tol)
        for row in augmented.matrix
    )
    coeff_pivots = tuple(c for c in augmented.pivot_columns if c < n)
    free = tuple(c for c in range(n) if c not in coeff_pivots)
    space = nullspace(m, tol=tol)
    if inconsistent:
        return LinearSolution("inconsistent", None, space, free, len(coeff_pivots))
    particular = np.zeros(n)
    for row_index, c in enumerate(coeff_pivots):
        particular[c] = augmented.matrix[row_index, n]
    kind: Literal["unique", "infinite", "inconsistent"] = "unique" if len(coeff_pivots) == n else "infinite"
    return LinearSolution(kind, particular, space, free, len(coeff_pivots))
