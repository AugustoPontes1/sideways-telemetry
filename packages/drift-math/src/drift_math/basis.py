"""Bases, ordered bases, and dimension in finite-dimensional Euclidean spaces."""
from __future__ import annotations
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .matrices import as_matrix, rref, rank, EPS
from .vectors import as_vector
from .linear_systems import solve


def independent(columns: ArrayLike, *, tol: float = EPS) -> bool:
    a = as_matrix(columns)
    return rank(a, tol=tol) == a.shape[1]


def extract_basis(generators: ArrayLike, *, tol: float = EPS) -> NDArray[np.float64]:
    """Pivot columns from the ORIGINAL matrix, keeping their initial order.

    For the trivial span, returns an array of shape (ambient_dimension, 0).
    """
    a = as_matrix(generators)
    pivots = rref(a, tol=tol).pivot_columns
    return a[:, list(pivots)].copy()


def dimension_of_span(generators: ArrayLike, *, tol: float = EPS) -> int:
    return rank(generators, tol=tol)


def is_basis_of_ambient(ordered_vectors: ArrayLike, *, tol: float = EPS) -> bool:
    """Columns are in the requested order; bases of R^n must be n×n full rank."""
    m = as_matrix(ordered_vectors)
    return m.shape[0] == m.shape[1] and independent(m, tol=tol)


def coordinates_in_basis(vector: ArrayLike, ordered_basis: ArrayLike,
                         *, tol: float = EPS) -> NDArray[np.float64]:
    basis = as_matrix(ordered_basis)
    if not independent(basis, tol=tol):
        raise ValueError("the selected ordered basis is linearly dependent")
    result = solve(basis, as_vector(vector, dim=basis.shape[0]), tol=tol)
    if result.kind != "unique" or result.particular is None:
        raise ValueError("vector not in the span of the ordered basis")
    return result.particular


def transition_matrix(from_basis: ArrayLike, to_basis: ArrayLike,
                      *, tol: float = EPS) -> NDArray[np.float64]:
    """C converts coordinate columns: [v]_to = C @ [v]_from.

    Both ordered bases must span the SAME subspace (possibly dimension < ambient).
    """
    frm = as_matrix(from_basis); to = as_matrix(to_basis)
    if frm.shape != to.shape or not independent(frm, tol=tol) or not independent(to, tol=tol):
        raise ValueError("bases must have same shape and independent columns")
    c = np.column_stack([coordinates_in_basis(frm[:, i], to, tol=tol) for i in range(frm.shape[1])])
    if not np.allclose(to @ c, frm, atol=tol * 10, rtol=1e-8):
        raise ValueError("bases do not span the same subspace")
    return c


def extend_basis_to_ambient(ordered_vectors: ArrayLike, *, tol: float = EPS) -> NDArray[np.float64]:
    """Complete independent columns to a basis of R^n using canonical directions."""
    seed = as_matrix(ordered_vectors)
    n, k = seed.shape
    if k > n or not independent(seed, tol=tol):
        raise ValueError("initial vectors must be independent and fit in R^n")
    current = seed.copy()
    for col in np.eye(n).T:
        if current.shape[1] == n: break
        proposal = np.column_stack([current, col])
        if rank(proposal, tol=tol) > current.shape[1]: current = proposal
    if current.shape != (n, n) or not independent(current, tol=tol):
        raise ValueError("could not complete the basis")
    return current
