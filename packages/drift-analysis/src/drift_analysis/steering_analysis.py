"""Steering *input* events. Cannot infer a driver's intent or steering delay alone."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Any
from .common import float_field, sequence_of, timestamp_s

@dataclass(frozen=True, slots=True)
class SteeringEvent:
    kind: str
    time_s: float
    sequence: int | None
    steering_rad: float
    rate_rad_s: float
    note: str


def steering_events(samples: Sequence[Mapping[str, Any]], *, rate_threshold_rad_s: float = 2.0,
                    max_dt_s: float = 0.5, cooldown_s: float = 0.5,
                    deadband_rad: float = 0.04) -> list[SteeringEvent]:
    if rate_threshold_rad_s <= 0 or max_dt_s <= 0 or cooldown_s < 0 or deadband_rad < 0:
        raise ValueError("invalid steering thresholds")
    events: list[SteeringEvent] = []
    previous = None
    last_event = -float("inf")
    previous_sign = 0
    for sample in samples:
        t, angle = timestamp_s(sample), float_field(sample, "steer_angle_rad")
        sign = 1 if angle > deadband_rad else -1 if angle < -deadband_rad else 0
        if previous is not None:
            pt, pa = previous
            dt = t-pt
            if 0 < dt <= max_dt_s:
                rate = (angle-pa)/dt
                if sign and previous_sign and sign != previous_sign and t-last_event >= cooldown_s:
                    events.append(SteeringEvent(
                        "direction_reversal", t, sequence_of(sample), angle, rate,
                        "Steering crossed the deadband; compare with yaw and sideslip before interpreting.",
                    )); last_event = t
                elif abs(rate) >= rate_threshold_rad_s and t-last_event >= cooldown_s:
                    events.append(SteeringEvent(
                        "rapid_steering_input", t, sequence_of(sample), angle, rate,
                        "Rapid input; not evidence of a mistake without a reference run.",
                    )); last_event = t
        if sign: previous_sign = sign
        previous = t, angle
    return events
