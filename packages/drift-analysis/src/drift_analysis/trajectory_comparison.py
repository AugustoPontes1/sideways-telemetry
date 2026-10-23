"""Compare positions against RECORDED reference by normalized arc-length progress.

RPM is metadata and can be attached to the trace, but cannot identify an ideal drift line.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Any
import numpy as np
from drift_math.trajectory import xz_path, resample_by_distance
from .common import frame_of, float_field, vector3

@dataclass(frozen=True, slots=True)
class TrajectoryComparison:
    count: int
    mean_deviation_m: float
    max_deviation_m: float
    rmse_deviation_m: float
    p95_deviation_m: float
    actual_xz_m: tuple[tuple[float, float], ...]
    reference_xz_m: tuple[tuple[float, float], ...]
    per_point_deviation_m: tuple[float, ...]
    method: str = "normalized-arc-length (recorded reference)"
    reference_is_ideal: bool = False
    limitations: str = (
        "Progress-normalized matching assumes the same curve and traversal direction; "
        "it does not align time or RPM, and ignores grip/track edges. A recorded reference is not necessarily optimal."
    )


def _points(data: Sequence[Mapping[str, Any]]) -> np.ndarray:
    if not data: raise ValueError("empty trajectory")
    return np.asarray([vector3(s, "position_world_m") for s in data], dtype=float)


def _track(samples: Sequence[Mapping[str, Any]]) -> str | None:
    tracks = {frame_of(row).get("track") for row in samples if frame_of(row).get("track")}
    if len(tracks) > 1: raise ValueError("a trajectory contains multiple tracks")
    return next(iter(tracks), None)


def compare_trajectories(actual: Sequence[Mapping[str, Any]],
                         reference: Sequence[Mapping[str, Any]], *,
                         count: int = 100) -> TrajectoryComparison:
    a_track, r_track = _track(actual), _track(reference)
    if a_track and r_track and a_track != r_track:
        raise ValueError("cannot compare sessions on different tracks")
    pa, pr = xz_path(_points(actual)), xz_path(_points(reference))
    if len(pa) < 2 or len(pr) < 2: raise ValueError("need >=2 samples per trajectory")
    a = resample_by_distance(pa, count); r = resample_by_distance(pr, count)
    distances = np.linalg.norm(a-r, axis=1)
    return TrajectoryComparison(
        count, float(np.mean(distances)), float(np.max(distances)),
        float(np.sqrt(np.mean(distances**2))), float(np.percentile(distances,95)),
        tuple(map(tuple, a.tolist())), tuple(map(tuple, r.tolist())),
        tuple(float(d) for d in distances),
    )


def build_recorded_reference(samples: Sequence[Mapping[str, Any]], *, count: int = 200) -> dict[str, Any]:
    """Generate dash-ready points and speed/RPM by progress; NOT an optimized trajectory."""
    if not samples: raise ValueError("no samples")
    if count < 2: raise ValueError("count must be >=2")
    path = _points(samples)
    horiz = xz_path(path)
    distances = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(horiz, axis=0), axis=1))]
    if distances[-1] <= 1e-9: raise ValueError("reference path has no horizontal movement")
    mask = np.r_[True, np.diff(distances)>1e-9]
    progress = np.linspace(0, distances[-1], count)
    x = np.interp(progress, distances[mask], path[mask, 0])
    y = np.interp(progress, distances[mask], path[mask, 1])
    z = np.interp(progress, distances[mask], path[mask, 2])
    rpm = np.interp(progress, distances[mask], [float_field(s, "rpm") for s, keep in zip(samples, mask) if keep])
    speed = np.interp(progress, distances[mask], [float_field(s, "speed_kmh") for s, keep in zip(samples, mask) if keep])
    return {
        "type": "recorded_reference", "ideal": False, "track": _track(samples),
        "points": [{"position_world_m": [float(x[i]), float(y[i]), float(z[i])],
                    "rpm": float(rpm[i]), "speed_kmh": float(speed[i]),
                    "progress": i/(count-1)} for i in range(count)],
        "limitation": "A linha é a tentativa gravada; RPM não determina uma trajetória ótima.",
    }
