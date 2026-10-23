"""Vectors in R^n. Coordinates are numeric and must have matching dimensions."""
from __future__ import annotations
import math
from collections.abc import Sequence
import numpy as np
from numpy.typing import ArrayLike, NDArray

EPS = 1e-10

def as_vector(values: ArrayLike, *, dim: int | None = None) -> NDArray[np.float64]:
    v = np.asarray(values, dtype=float)
    if v.ndim != 1 or not v.size or (dim is not None and len(v) != dim) or not np.isfinite(v).all():
        raise ValueError(f"expected finite 1-D vector with dimension {dim or '>0'}")
    return v

def add(a: ArrayLike, b: ArrayLike) -> NDArray[np.float64]:
    va = as_vector(a); return va + as_vector(b, dim=va.size)

def subtract(a: ArrayLike, b: ArrayLike) -> NDArray[np.float64]:
    va = as_vector(a); return va - as_vector(b, dim=va.size)

def scale(k: float, v: ArrayLike) -> NDArray[np.float64]:
    if not math.isfinite(k): raise ValueError("scale must be finite")
    return float(k) * as_vector(v)

def dot(a: ArrayLike, b: ArrayLike) -> float:
    va = as_vector(a); return float(va @ as_vector(b, dim=va.size))

def norm(v: ArrayLike) -> float:
    return float(np.linalg.norm(as_vector(v)))

def unit(v: ArrayLike, *, tol: float = EPS) -> NDArray[np.float64]:
    a = as_vector(v); length = float(np.linalg.norm(a))
    if length <= tol: raise ValueError("zero vector has no direction")
    return a / length

def angle_between(a: ArrayLike, b: ArrayLike, *, degrees: bool = False) -> float:
    va = unit(a); vb = unit(as_vector(b, dim=va.size))
    angle = math.acos(float(np.clip(va @ vb, -1.0, 1.0)))
    return math.degrees(angle) if degrees else angle

def signed_angle_2d(a: ArrayLike, b: ArrayLike, *, degrees: bool = False) -> float:
    """Signed CCW angle from a to b, in a right-handed XY 2D plane."""
    va = unit(as_vector(a, dim=2)); vb = unit(as_vector(b, dim=2))
    angle = math.atan2(float(va[0] * vb[1] - va[1] * vb[0]), float(va @ vb))
    return math.degrees(angle) if degrees else angle

def projection(v: ArrayLike, onto: ArrayLike) -> NDArray[np.float64]:
    vec = as_vector(v); axis = as_vector(onto, dim=vec.size)
    divisor = float(axis @ axis)
    if divisor <= EPS * EPS: raise ValueError("cannot project onto zero vector")
    return float(vec @ axis) / divisor * axis
