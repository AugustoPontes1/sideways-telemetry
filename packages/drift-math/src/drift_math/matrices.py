"""Matrix operations and pedagogical Gauss-Jordan elimination.

Do not invert a matrix to solve Ax=b in real production numerical code: use np.linalg.solve/lstsq.
The iterative algorithm is deliberately explicit for the student's Aula 04/06/07/11.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import ArrayLike, NDArray

EPS = 1e-10

@dataclass(frozen=True, slots=True)
class RowOperation:
    description: str
    state: tuple[tuple[float, ...], ...]

@dataclass(frozen=True, slots=True)
class EchelonResult:
    matrix: NDArray[np.float64]
    pivot_columns: tuple[int, ...]
    steps: tuple[RowOperation, ...]

    @property
    def rank(self) -> int:
        return len(self.pivot_columns)

def as_matrix(values: ArrayLike) -> NDArray[np.float64]:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0 or not np.isfinite(matrix).all():
        raise ValueError("expected finite nonempty 2-D matrix")
    return matrix

def add(a: ArrayLike, b: ArrayLike) -> NDArray[np.float64]:
    aa = as_matrix(a); bb = as_matrix(b)
    if aa.shape != bb.shape: raise ValueError("matrix shapes must match")
    return aa + bb

def multiply(a: ArrayLike, b: ArrayLike) -> NDArray[np.float64]:
    aa = as_matrix(a); bb = np.asarray(b, dtype=float)
    if bb.ndim not in (1, 2) or not np.isfinite(bb).all() or aa.shape[1] != bb.shape[0]:
        raise ValueError("incompatible matrix multiplication dimensions")
    return aa @ bb

def transpose(a: ArrayLike) -> NDArray[np.float64]:
    return as_matrix(a).T.copy()

def _state(a: NDArray[np.float64]) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(x) for x in row) for row in a)

def rref(values: ArrayLike, *, tol: float = EPS, record_steps: bool = False) -> EchelonResult:
    """Reduced row-echelon form, partial pivoting, absolute tolerance.

    For ill-conditioned real systems, prefer np.linalg.lstsq / SVD.
    """
    if not 0 < tol < 1: raise ValueError("tol must be in (0,1)")
    a = as_matrix(values).copy()
    rows, cols = a.shape
    pivots: list[int] = []
    operations: list[RowOperation] = []

    def record(description: str) -> None:
        if record_steps: operations.append(RowOperation(description, _state(a)))

    r = 0
    for c in range(cols):
        if r >= rows: break
        best = r + int(np.argmax(np.abs(a[r:, c])))
        if abs(float(a[best, c])) <= tol:
            continue
        if best != r:
            a[[r, best], :] = a[[best, r], :]
            record(f"L{r+1} ↔ L{best+1}")
        pivot = float(a[r, c])
        a[r, :] /= pivot
        record(f"L{r+1} ← L{r+1} / {pivot:.6g}")
        for other in range(rows):
            if other == r: continue
            coefficient = float(a[other, c])
            if abs(coefficient) > tol:
                a[other, :] -= coefficient * a[r, :]
                record(f"L{other+1} ← L{other+1} − ({coefficient:.6g})L{r+1}")
        pivots.append(c)
        r += 1
    a[np.abs(a) < tol] = 0.0
    return EchelonResult(a, tuple(pivots), tuple(operations))

def rank(a: ArrayLike, *, tol: float = EPS) -> int:
    return rref(a, tol=tol).rank

def nullity(a: ArrayLike, *, tol: float = EPS) -> int:
    m = as_matrix(a); return m.shape[1] - rank(m, tol=tol)

def determinant(a: ArrayLike, *, tol: float = EPS) -> float:
    matrix = as_matrix(a).copy()
    n, cols = matrix.shape
    if n != cols: raise ValueError("determinant requires a square matrix")
    det = 1.0
    for c in range(n):
        best = c + int(np.argmax(np.abs(matrix[c:, c])))
        if abs(float(matrix[best, c])) <= tol: return 0.0
        if best != c:
            matrix[[c, best], :] = matrix[[best, c], :]
            det = -det
        pivot = float(matrix[c, c]); det *= pivot
        for row in range(c+1, n):
            multiplier = matrix[row, c] / pivot
            matrix[row, c:] -= multiplier * matrix[c, c:]
    return float(det)

def inverse(a: ArrayLike, *, tol: float = EPS) -> NDArray[np.float64]:
    original = as_matrix(a)
    n, cols = original.shape
    if n != cols: raise ValueError("inverse requires a square matrix")
    result = rref(np.hstack([original, np.eye(n)]), tol=tol)
    if result.pivot_columns[:n] != tuple(range(n)) or not np.allclose(result.matrix[:, :n], np.eye(n), atol=tol, rtol=0):
        raise ValueError("matrix is singular; inverse does not exist")
    return result.matrix[:, n:]
