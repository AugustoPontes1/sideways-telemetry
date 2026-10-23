"""Geometric trajectories (XYZ from AC), arc-length tools and sideslip.

A reference trace is a RECORDED reference; there is no RPM-only ideal path.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .vectors import as_vector
from .transformations import xz_local_axes

@dataclass(frozen=True)
class ClosestPoint:
    distance_m: float
    position_xz_m: tuple[float, float]
    segment_index: int
    segment_fraction: float
    signed_offset_m: float  # +left of reference segment in mathematical X/Z drawing


def xz_path(world_xyz: ArrayLike) -> NDArray[np.float64]:
    points = np.asarray(world_xyz, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) == 0 or not np.isfinite(points).all():
        raise ValueError("expected finite Nx3 world coordinates")
    return points[:, [0, 2]]


def cumulative_length(path_xz: ArrayLike) -> NDArray[np.float64]:
    pts = _path2(path_xz)
    return np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]


def _path2(values: ArrayLike) -> NDArray[np.float64]:
    pts = np.asarray(values, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) == 0 or not np.isfinite(pts).all():
        raise ValueError("expected finite Nx2 horizontal path")
    return pts


def resample_by_distance(path_xz: ArrayLike, count: int) -> NDArray[np.float64]:
    """Arc-length interpolation. Useful to compare corresponding progress along two loops.

    It does not validate same corners, speed, timing or physical feasibility.
    """
    if type(count) is not int or count < 2: raise ValueError("count must be integer >= 2")
    pts = _path2(path_xz)
    cumulative = cumulative_length(pts)
    total = cumulative[-1]
    if total <= 1e-12: return np.repeat(pts[[0], :], count, axis=0)
    # Deduplicate stationary segments for interpolation, preserving final endpoint.
    select = np.r_[True, np.diff(cumulative) > 1e-12]
    arc = cumulative[select]
    coords = pts[select, :]
    t = np.linspace(0, total, count)
    return np.column_stack([np.interp(t, arc, coords[:, 0]), np.interp(t, arc, coords[:, 1])])


def closest_on_polyline(position_xz: ArrayLike, reference_xz: ArrayLike) -> ClosestPoint:
    p = as_vector(position_xz, dim=2); pts = _path2(reference_xz)
    if len(pts) == 1:
        return ClosestPoint(float(np.linalg.norm(p-pts[0])), tuple(pts[0]), 0, 0.0, 0.0)
    best: ClosestPoint | None = None
    for i in range(len(pts)-1):
        a, b = pts[i], pts[i+1]
        ab = b - a; length2 = float(ab @ ab)
        u = float(np.clip(((p-a) @ ab)/length2, 0, 1)) if length2 > 1e-12 else 0.0
        nearest = a + u*ab
        delta = p-nearest
        dist = float(np.linalg.norm(delta))
        cross = float(ab[0]*delta[1] - ab[1]*delta[0])
        signed = math.copysign(dist, cross) if abs(cross) > 1e-12 else 0.0
        candidate = ClosestPoint(dist, (float(nearest[0]), float(nearest[1])), i, u, signed)
        if best is None or dist < best.distance_m: best = candidate
    assert best is not None
    return best


def signed_sideslip_rad(velocity_world_xyz: ArrayLike, yaw_rad: float,
                        *, min_speed_mps: float = 2.0) -> float | None:
    """Signed angle from car-forward to velocity in XZ; positive toward car-right.

    Return None when below min speed, since heading-vs-motion is unstable near stop.
    The yaw must already be calibrated to the declared vehicle coordinate convention.
    """
    v = as_vector(velocity_world_xyz, dim=3)
    speed = math.hypot(v[0], v[2])
    if not math.isfinite(min_speed_mps) or min_speed_mps <= 0: raise ValueError("invalid speed threshold")
    if speed < min_speed_mps: return None
    right, forward = xz_local_axes(yaw_rad)
    planar = np.array([v[0], v[2]])
    lateral, longitudinal = float(planar @ right), float(planar @ forward)
    return math.atan2(lateral, longitudinal)
