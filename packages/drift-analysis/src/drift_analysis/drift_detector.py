"""Detect *possible* sustained drifting from measured heading-vs-velocity.

Requires field calibration of the AC yaw convention. No collision/spin causal diagnoses.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from collections.abc import Mapping, Sequence
from typing import Any
from drift_math.trajectory import signed_sideslip_rad
from .common import frame_of, timestamp_s, vector3, float_field, sequence_of

@dataclass(frozen=True, slots=True)
class DriftInterval:
    start_s: float
    end_s: float
    start_sequence: int | None
    end_sequence: int | None
    mean_abs_angle_deg: float
    peak_abs_angle_deg: float
    direction_sign: int
    classification: str = "possible_sustained_sideslip"


def analyze_drift(samples: Sequence[Mapping[str, Any]], *, yaw_calibrated: bool = False,
                  min_speed_mps: float = 5.0, enter_deg: float = 15,
                  exit_deg: float = 10, min_duration_s: float = 0.3,
                  max_gap_s: float = 0.25) -> list[DriftInterval]:
    """Hysteresis: enter when abs(sideslip)>=enter; leave below exit or sign changes.

    Not a proof of drifting; angle and yaw sign must be checked with AC on track.
    """
    if not yaw_calibrated:
        raise ValueError("yaw not calibrated: verify Assetto Corsa heading axis/sign before detecting drift")
    if not (0 <= exit_deg < enter_deg < 180 and min_duration_s >= 0 and max_gap_s > 0):
        raise ValueError("invalid drift detection thresholds")
    if min_speed_mps <= 0: raise ValueError("min_speed_mps must be positive")
    intervals: list[DriftInterval] = []
    active: list[tuple[float, int | None, float]] = []
    last_time: float | None = None
    sign: int = 0

    def flush() -> None:
        nonlocal active, sign
        if active and active[-1][0] - active[0][0] >= min_duration_s:
            angles = [x[2] for x in active]
            intervals.append(DriftInterval(
                active[0][0], active[-1][0], active[0][1], active[-1][1],
                sum(abs(a) for a in angles)/len(angles), max(abs(a) for a in angles), sign,
            ))
        active = []; sign = 0

    for item in samples:
        t = timestamp_s(item)
        if last_time is not None and (t <= last_time or t-last_time > max_gap_s): flush()
        last_time = t
        angle = signed_sideslip_rad(vector3(item, "velocity_world_mps"),
                                    float_field(item, "heading_rad"), min_speed_mps=min_speed_mps)
        value = math.degrees(angle) if angle is not None else None
        new_sign = 1 if value is not None and value > 0 else -1
        if active and (value is None or abs(value) < exit_deg or new_sign != sign):
            flush()
        if value is None: continue
        if active:
            active.append((t, sequence_of(item), value))
        elif abs(value) >= enter_deg:
            active = [(t, sequence_of(item), value)]; sign = new_sign
    flush()
    return intervals
