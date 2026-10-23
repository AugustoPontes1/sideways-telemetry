"""Throttle and gear event candidates; no unsupported diagnosis of grip or engine power."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from typing import Any
from .common import float_field, frame_of, sequence_of, timestamp_s

@dataclass(frozen=True, slots=True)
class PowertrainEvent:
    kind: str
    time_s: float
    sequence: int | None
    throttle: float
    rpm: int
    gear: int
    note: str


def throttle_events(samples: Sequence[Mapping[str, Any]], *,
                    tip_in_per_s: float = 1.5, lift_off_per_s: float = 1.5,
                    rpm_drop_per_s: float = 3500,
                    max_dt_s: float = 0.5, cooldown_s: float = 0.3) -> list[PowertrainEvent]:
    if min(tip_in_per_s, lift_off_per_s, rpm_drop_per_s, max_dt_s) <= 0 or cooldown_s < 0:
        raise ValueError("invalid event thresholds")
    events: list[PowertrainEvent] = []
    prev = None
    last_by_kind: dict[str, float] = {}
    for sample in samples:
        t = timestamp_s(sample)
        throttle = float_field(sample, "throttle")
        rpm = int(float_field(sample, "rpm"))
        gear = int(float_field(sample, "gear"))
        if not 0 <= throttle <= 1 or not 0 <= rpm <= 30000 or not -1 <= gear <= 20:
            raise ValueError("invalid throttle/rpm/gear values")
        if prev is not None:
            pt, pg, prpm, pgear = prev
            dt = t - pt
            if 0 < dt <= max_dt_s:
                kinds = []
                rate = (throttle-pg)/dt
                if rate >= tip_in_per_s: kinds.append("rapid_throttle_tip_in")
                if rate <= -lift_off_per_s: kinds.append("rapid_throttle_lift_off")
                if gear != pgear: kinds.append("gear_change")
                if (prpm-rpm)/dt >= rpm_drop_per_s: kinds.append("rapid_rpm_drop")
                for kind in kinds:
                    if t-last_by_kind.get(kind, -float("inf")) < cooldown_s: continue
                    events.append(PowertrainEvent(kind, t, sequence_of(sample), throttle, rpm, gear,
                        "Investigate along with vehicle speed, traction, gear and engine response."))
                    last_by_kind[kind] = t
        prev = t, throttle, rpm, gear
    return events
