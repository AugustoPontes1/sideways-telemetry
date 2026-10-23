"""Validate inbound/outbound objects. No network I/O or implicit unit conversions.

Compatible with the original Telemetry Agent normalizer and Django v1 validator.
Vectors are arrays in JSON; tuples are also accepted in Python and normalized to lists.
"""
from __future__ import annotations
import json
import math
import uuid
from collections.abc import Mapping, Sequence
from typing import Any

MAX_BATCH_BYTES = 1_048_576
MAX_SAMPLES = 100
MIN_EPOCH_NS = 946_684_800_000_000_000  # 2000-01-01
MAX_EPOCH_NS = 4_102_444_800_000_000_000  # 2100-01-01

class SchemaError(ValueError):
    """Invalid or incompatible telemetry protocol payload."""

def _integer(o: Mapping[str, Any], name: str, minimum: int, maximum: int = 2**63 - 1) -> int:
    value = o.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise SchemaError(f"{name}: expected integer in {minimum}..{maximum}")
    return value

def _real(o: Mapping[str, Any], name: str, minimum: float = -1e12,
          maximum: float = 1e12) -> float:
    value = o.get(name)
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise SchemaError(f"{name}: expected finite number in {minimum}..{maximum}")
    return float(value)

def _str(o: Mapping[str, Any], name: str, limit: int = 160) -> str:
    value = o.get(name)
    if not isinstance(value, str) or len(value) > limit or any(ord(ch) < 32 for ch in value):
        raise SchemaError(f"{name}: invalid text")
    return value

def _uuid(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise SchemaError(f"{name}: expected UUID string")
    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise SchemaError(f"{name}: invalid UUID") from exc

def _vector(o: Mapping[str, Any], name: str, n: int) -> list[float]:
    value = o.get(name)
    if isinstance(value, (str, bytes)) or not isinstance(value, (tuple, list)) or len(value) != n:
        raise SchemaError(f"{name}: expected {n} components")
    if any(type(x) not in (int, float) or not math.isfinite(x) or abs(x) > 1e9 for x in value):
        raise SchemaError(f"{name}: invalid components")
    return [float(x) for x in value]

def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaError(f"{name}: expected object")
    return value

def validate_frame(payload: Any) -> dict[str, Any]:
    """Return a clean v1 dict ready for JSON. Reject surprising units/NaN."""
    f = _mapping(payload, "telemetry")
    if _integer(f, "schema_version", 1, 1) != 1:
        raise SchemaError("only telemetry schema_version=1 supported")
    result: dict[str, Any] = {
        "schema_version": 1,
        "timestamp_unix_ns": _integer(f, "timestamp_unix_ns", MIN_EPOCH_NS, MAX_EPOCH_NS),
        "timestamp_monotonic_ns": _integer(f, "timestamp_monotonic_ns", 1),
        "physics_packet_id": _integer(f, "physics_packet_id", 1),
        "graphics_packet_id": _integer(f, "graphics_packet_id", 0),
        "session_type": _integer(f, "session_type", -1, 100),
        "completed_laps": _integer(f, "completed_laps", 0, 1_000_000),
        "car": _str(f, "car"),
        "track": _str(f, "track"),
        "speed_kmh": _real(f, "speed_kmh", -600, 600),
        "rpm": _integer(f, "rpm", 0, 30_000),
        "gear": _integer(f, "gear", -1, 20),
        "throttle": _real(f, "throttle", 0, 1),
        "brake": _real(f, "brake", 0, 1),
        "clutch": _real(f, "clutch", 0, 1),
        "steer_angle_rad": _real(f, "steer_angle_rad", -30, 30),
        "heading_rad": _real(f, "heading_rad", -30, 30),
        "pitch_rad": _real(f, "pitch_rad", -30, 30),
        "roll_rad": _real(f, "roll_rad", -30, 30),
        "position_world_m": _vector(f, "position_world_m", 3),
        "velocity_world_mps": _vector(f, "velocity_world_mps", 3),
        "acceleration_g": _vector(f, "acceleration_g", 3),
        "angular_velocity_local_rad_s": _vector(f, "angular_velocity_local_rad_s", 3),
        "wheel_slip_raw": _vector(f, "wheel_slip_raw", 4),
    }
    speed_mps = _real(f, "speed_mps", -600 / 3.6, 600 / 3.6)
    if not math.isclose(speed_mps, result["speed_kmh"] / 3.6, abs_tol=1e-3, rel_tol=1e-5):
        raise SchemaError("speed_mps and speed_kmh are inconsistent")
    result["speed_mps"] = result["speed_kmh"] / 3.6
    return result

def validate_sample(payload: Any) -> dict[str, Any]:
    item = _mapping(payload, "sample")
    if item.get("type") != "telemetry":
        raise SchemaError("sample.type must be 'telemetry'")
    return {
        "type": "telemetry",
        "stream_id": _uuid(item.get("stream_id"), "stream_id"),
        "sequence": _integer(item, "sequence", 0),
        "received_at_unix_ns": _integer(item, "received_at_unix_ns", MIN_EPOCH_NS, MAX_EPOCH_NS),
        "telemetry": validate_frame(item.get("telemetry")),
    }

def validate_batch(payload: Any, *, expected_agent_id: str | None = None) -> dict[str, Any]:
    item = _mapping(payload, "batch")
    if item.get("type") != "telemetry.batch" or _integer(item, "schema_version", 1, 1) != 1:
        raise SchemaError("expected telemetry.batch schema_version=1")
    agent_id = _str(item, "agent_id", 100)
    if not agent_id or (expected_agent_id is not None and agent_id != expected_agent_id):
        raise SchemaError("agent_id invalid or unexpected")
    samples = item.get("samples")
    if not isinstance(samples, list) or not 1 <= len(samples) <= MAX_SAMPLES:
        raise SchemaError("samples: expected 1..100 items")
    seen: set[tuple[str, int]] = set()
    valid = []
    for payload_sample in samples:
        sample = validate_sample(payload_sample)
        key = sample["stream_id"], sample["sequence"]
        if key in seen:
            raise SchemaError("duplicate stream_id/sequence within batch")
        seen.add(key)
        valid.append(sample)
    result = {
        "type": "telemetry.batch",
        "schema_version": 1,
        "batch_id": _uuid(item.get("batch_id"), "batch_id"),
        "agent_id": agent_id,
        "samples": valid,
    }
    if len(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")) > MAX_BATCH_BYTES:
        raise SchemaError("batch exceeds 1 MiB")
    return result

def validate_ack(payload: Any, *, batch_id: str, sample_count: int) -> dict[str, Any]:
    message = _mapping(payload, "ack")
    if (message.get("type") != "telemetry.ack" or
            _uuid(message.get("batch_id"), "batch_id") != _uuid(batch_id, "batch_id") or
            type(message.get("accepted")) is not int or message["accepted"] != sample_count):
        raise SchemaError("ack is for a different or partially confirmed batch")
    return {"type": "telemetry.ack", "batch_id": _uuid(batch_id, "batch_id"), "accepted": sample_count}
