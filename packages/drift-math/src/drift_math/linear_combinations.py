"""Span and linear combinations: from Aula 15 to concrete vector components."""
from __future__ import annotations
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .vectors import as_vector
from .matrices import as_matrix, rank, EPS
from .linear_systems import LinearSolution, solve

def combine(columns: ArrayLike, coefficients: ArrayLike) -> NDArray[np.float64]:
    """Columns are generators; result is sum_i coeff[i]*column_i."""
    m = as_matrix(columns)
    coefs = as_vector(coefficients, dim=m.shape[1])
    return m @ coefs

def coefficients_for(target: ArrayLike, generators: ArrayLike, *, tol: float = EPS) -> LinearSolution:
    m = as_matrix(generators)
    return solve(m, as_vector(target, dim=m.shape[0]), tol=tol)

def is_in_span(target: ArrayLike, generators: ArrayLike, *, tol: float = EPS) -> bool:
    return coefficients_for(target, generators, tol=tol).kind != "inconsistent"

def span_dimension(generators: ArrayLike, *, tol: float = EPS) -> int:
    return rank(generators, tol=tol)
