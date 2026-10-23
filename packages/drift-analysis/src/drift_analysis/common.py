"""Canonical adapters for normalized WSL frames, batch samples and REST serializers."""
from __future__ import annotations
from datetime import datetime, timezone
import math
from typing import Any, Mapping


def frame_of(sample: Mapping[str, Any]) -> Mapping[str, Any]:
    frame = sample.get("telemetry", sample.get("payload", sample))
    if not isinstance(frame, Mapping): raise ValueError("telemetry must be a mapping")
    return frame

def timestamp_s(sample: Mapping[str, Any]) -> float:
    frame = frame_of(sample)
    stamp = frame.get("timestamp_unix_ns")
    if type(stamp) is int and stamp > 0:
        return stamp / 1e9
    stamp = sample.get("sampled_at", frame.get("sampled_at"))
    if isinstance(stamp, str):
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None: raise ValueError("sampled_at must specify a timezone")
        return parsed.timestamp()
    if isinstance(stamp, datetime):
        if stamp.tzinfo is None: raise ValueError("sampled_at must specify timezone")
        return stamp.timestamp()
    raise ValueError("missing timestamp_unix_ns or sampled_at")

def float_field(sample: Mapping[str, Any], key: str, *, default: float | None = None) -> float:
    frame = frame_of(sample)
    value = frame.get(key, default)
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    return float(value)

def vector3(sample: Mapping[str, Any], key: str) -> tuple[float, float, float]:
    frame = frame_of(sample)
    values = frame.get(key)
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError(f"{key} must have three components")
    if any(type(v) not in (float, int) or not math.isfinite(v) for v in values):
        raise ValueError(f"{key} must contain finite numbers")
    return float(values[0]), float(values[1]), float(values[2])

def sequence_of(sample: Mapping[str, Any]) -> int | None:
    val = sample.get("sequence")
    return val if type(val) is int else None
