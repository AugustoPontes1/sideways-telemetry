"""Planar/3D coordinate conversion with a DECLARED yaw convention.

Assume global X/Z is the horizontal plane, world +Z is forward at yaw=0,
positive yaw turns forward toward +X, and +X is the car's right when yaw=0.
This is a LABORATORY convention; AC heading/steering signs must be calibrated
against an actual straight-line drive before these functions analyze real data.
"""
from __future__ import annotations
import math
import numpy as np
from numpy.typing import ArrayLike, NDArray
from .vectors import as_vector
from .matrices import as_matrix

def rotation_2d(theta_rad: float) -> NDArray[np.float64]:
    """Standard counterclockwise rotation of XY column vectors."""
    if not math.isfinite(theta_rad): raise ValueError("invalid angle")
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, -s], [s, c]], dtype=float)

def rotation_about_world_y(theta_rad: float) -> NDArray[np.float64]:
    """Right-handed 3D rotation about +Y; XZ plane."""
    if not math.isfinite(theta_rad): raise ValueError("invalid angle")
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)

def xz_local_axes(yaw_rad: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return (right_axis_XZ, forward_axis_XZ), unit-length and orthogonal."""
    if not math.isfinite(yaw_rad): raise ValueError("invalid angle")
    s, c = math.sin(yaw_rad), math.cos(yaw_rad)
    right = np.array([c, -s]); forward = np.array([s, c])
    return right, forward

def xz_world_to_vehicle(velocity_world_xyz: ArrayLike, yaw_rad: float) -> NDArray[np.float64]:
    """Return [lateral-right, longitudinal-forward] m/s under declared convention."""
    x, y, z = as_vector(velocity_world_xyz, dim=3)
    right, forward = xz_local_axes(yaw_rad)
    xz = np.array([x, z])
    return np.array([xz @ right, xz @ forward])

def xz_vehicle_to_world(components_lateral_forward: ArrayLike, yaw_rad: float,
                        vertical_mps: float = 0.0) -> NDArray[np.float64]:
    local = as_vector(components_lateral_forward, dim=2)
    right, forward = xz_local_axes(yaw_rad)
    x, z = local[0]*right + local[1]*forward
    return np.array([x, vertical_mps, z], dtype=float)

def transform_points(matrix: ArrayLike, points: ArrayLike) -> NDArray[np.float64]:
    """Columns are points (vectors): transform @ points (no translation)."""
    transform = as_matrix(matrix); pts = as_matrix(points)
    if transform.shape[1] != pts.shape[0]: raise ValueError("incompatible dimensions")
    return transform @ pts

def transform_positions(matrix: ArrayLike, points: ArrayLike, offset: ArrayLike) -> NDArray[np.float64]:
    """Affine transform in world space: A@points + translation (NOT linear if offset ≠ 0)."""
    a = as_matrix(matrix); pts = as_matrix(points); t = as_vector(offset, dim=a.shape[0])
    if a.shape[1] != pts.shape[0]: raise ValueError("incompatible dimensions")
    return a @ pts + t[:, None]
