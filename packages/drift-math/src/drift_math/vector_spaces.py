"""Finite-dimensional real vector spaces; separate examples from universal proofs."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .vectors import as_vector
from .matrices import as_matrix
from .subspaces import LinearSubspace

@dataclass(frozen=True, slots=True)
class EuclideanSpace:
    dimension: int

    def __post_init__(self) -> None:
        if type(self.dimension) is not int or self.dimension <= 0:
            raise ValueError("dimension must be a positive integer")

    def contains(self, v: ArrayLike) -> bool:
        try:
            as_vector(v, dim=self.dimension)
            return True
        except (TypeError, ValueError):
            return False

    def zero(self) -> NDArray[np.float64]:
        return np.zeros(self.dimension)

    def add(self, a: ArrayLike, b: ArrayLike) -> NDArray[np.float64]:
        return as_vector(a, dim=self.dimension) + as_vector(b, dim=self.dimension)

    def scale(self, k: float, a: ArrayLike) -> NDArray[np.float64]:
        if not np.isfinite(k): raise ValueError("scalar must be finite")
        return float(k) * as_vector(a, dim=self.dimension)

    def homogeneous_subspace(self, matrix: ArrayLike) -> LinearSubspace:
        a = as_matrix(matrix)
        if a.shape[1] != self.dimension: raise ValueError("incorrect number of constraint columns")
        return LinearSubspace.kernel(a)


def check_axioms_on_examples(vectors: list[ArrayLike], scalars: list[float],
                             *, tol: float = 1e-9) -> dict[str, bool]:
    """Numerical examples, NOT proof that an arbitrary set is a vector space.

    This only illustrates R^n's 8 axioms for specified finite sample inputs.
    """
    if len(vectors) < 3 or len(scalars) < 2: raise ValueError("need 3 vectors and 2 scalars")
    u, v, w = (as_vector(x) for x in vectors[:3])
    if not (u.shape == v.shape == w.shape): raise ValueError("vector sizes differ")
    a, b = float(scalars[0]), float(scalars[1])
    if not np.isfinite([a, b]).all(): raise ValueError("scalars must be finite")
    eq = lambda x, y: bool(np.allclose(x, y, atol=tol, rtol=tol))
    z = np.zeros_like(u)
    return {
        "associative": eq((u+v)+w, u+(v+w)),
        "commutative": eq(u+v, v+u),
        "additive_identity": eq(u+z, u),
        "additive_inverse": eq(u+(-u), z),
        "scalar_distributes_vector": eq(a*(u+v), a*u+a*v),
        "scalar_distributes_scalar": eq((a+b)*u, a*u+b*u),
        "scalar_associative": eq((a*b)*u, a*(b*u)),
        "scalar_identity": eq(1*u, u),
    }
