"""Provably linear subspaces defined by generators or homogeneous constraints.

The sampled positions of a drifting car form a finite set, NOT generally a vector subspace.
A moving vehicle's full feasible states are nonlinear and should not be mislabeled.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .matrices import as_matrix, EPS
from .basis import extract_basis
from .linear_systems import nullspace, solve
from .vectors import as_vector

@dataclass(frozen=True)
class LinearSubspace:
    """Basis vectors stored as columns; zero-dimensional basis has shape (n,0)."""
    basis: NDArray[np.float64]

    @classmethod
    def generated_by(cls, generators: ArrayLike, *, tol: float = EPS) -> "LinearSubspace":
        return cls(extract_basis(generators, tol=tol))

    @classmethod
    def kernel(cls, constraints: ArrayLike, *, tol: float = EPS) -> "LinearSubspace":
        """Homogeneous constraint Ax = 0 always defines a subspace."""
        return cls(nullspace(constraints, tol=tol))

    @property
    def ambient_dimension(self) -> int:
        return self.basis.shape[0]

    @property
    def dimension(self) -> int:
        return self.basis.shape[1]

    def contains(self, vector: ArrayLike, *, tol: float = EPS) -> bool:
        v = as_vector(vector, dim=self.ambient_dimension)
        if self.dimension == 0: return bool(np.linalg.norm(v) <= tol)
        result = solve(self.basis, v, tol=tol)
        return result.kind != "inconsistent"

    def sum_with(self, other: "LinearSubspace", *, tol: float = EPS) -> "LinearSubspace":
        if self.ambient_dimension != other.ambient_dimension: raise ValueError("ambient dimensions differ")
        cols = np.column_stack([self.basis, other.basis])
        if cols.shape[1] == 0: return LinearSubspace(np.zeros((self.ambient_dimension, 0)))
        return LinearSubspace.generated_by(cols, tol=tol)

    def intersect(self, other: "LinearSubspace", *, tol: float = EPS) -> "LinearSubspace":
        """Find U∩V from solutions of U*a = V*b, then extract independent U*a."""
        if self.ambient_dimension != other.ambient_dimension: raise ValueError("ambient dimensions differ")
        n = self.ambient_dimension
        if self.dimension == 0 or other.dimension == 0:
            return LinearSubspace(np.zeros((n, 0)))
        joint = np.column_stack([self.basis, -other.basis])
        kernel_of_joint = nullspace(joint, tol=tol)
        vectors = self.basis @ kernel_of_joint[:self.dimension, :]
        if vectors.shape[1] == 0: return LinearSubspace(np.zeros((n, 0)))
        return LinearSubspace.generated_by(vectors, tol=tol)


def is_homogeneous_constraint_subspace(a: ArrayLike) -> bool:
    """Mathematical theorem, not a sample-based numerical proof: kernel(A) is a subspace."""
    as_matrix(a)
    return True


def affine_constraint_contains(a: ArrayLike, b: ArrayLike, vector: ArrayLike,
                               *, tol: float = EPS) -> bool:
    """Membership test for Ax=b. If b != 0, generally an affine set, not a subspace."""
    aa = as_matrix(a); bb = as_vector(b, dim=aa.shape[0]); x = as_vector(vector, dim=aa.shape[1])
    return bool(np.linalg.norm(aa @ x - bb) <= tol)
