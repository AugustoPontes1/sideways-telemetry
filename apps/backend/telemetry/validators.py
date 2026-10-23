"""Contrato estrito do Telemetry Agent v1; sem importar Django (testável isoladamente)."""
from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

MAX_BATCH_BYTES = 1_048_576
MAX_SAMPLES = 100
MAX_TIMESTAMP_NS = 4_102_444_800_000_000_000  # 2100-01-01 UTC
MIN_TIMESTAMP_NS = 946_684_800_000_000_000  # 2000-01-01 UTC


class InvalidBatch(ValueError):
    """Lote malformado; NÃO confirmar via ACK."""


def checked_int(data: Mapping, key: str, lo: int = 0, hi: int = 2**63 - 1) -> int:
    v = data.get(key)
    if type(v) is not int or not lo <= v <= hi:
        raise InvalidBatch(f"{key}: inteiro obrigatório em {lo}..{hi}")
    return v


def checked_float(data: Mapping, key: str, lo: float = -1e12, hi: float = 1e12) -> float:
    v = data.get(key)
    if type(v) not in (int, float) or not math.isfinite(v) or not lo <= v <= hi:
        raise InvalidBatch(f"{key}: número finito fora do intervalo permitido")
    return float(v)


def checked_string(data: Mapping, key: str, limit: int = 160) -> str:
    v = data.get(key)
    if not isinstance(v, str) or len(v) > limit or any(ord(ch) < 32 for ch in v):
        raise InvalidBatch(f"{key}: texto inválido")
    return v


def checked_vector(data: Mapping, key: str, size: int) -> list[float]:
    v = data.get(key)
    if not isinstance(v, list) or len(v) != size:
        raise InvalidBatch(f"{key}: esperado vetor numérico com {size} entradas")
    result = []
    for n in v:
        if type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 1e9:
            raise InvalidBatch(f"{key}: componente inválido")
        result.append(float(n))
    return result


def checked_uuid(value: Any, name: str) -> uuid.UUID:
    if type(value) is not str or len(value) > 64:
        raise InvalidBatch(f"{name}: UUID textual inválido")
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise InvalidBatch(f"{name}: UUID inválido") from exc


def ns_to_datetime(timestamp_ns: int) -> datetime:
    """Converte epoch-ns preservando microssegundos e sem aritmética float."""
    seconds, nano = divmod(timestamp_ns, 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(
        microsecond=nano // 1000,
    )


@dataclass(frozen=True, slots=True)
class ValidatedSample:
    stream_id: uuid.UUID
    sequence: int
    received_at_ns: int
    frame: dict[str, Any]
    frame_hash: str

    @property
    def sampled_at(self) -> datetime:
        return ns_to_datetime(self.frame["timestamp_unix_ns"])

    @property
    def received_at(self) -> datetime:
        return ns_to_datetime(self.received_at_ns)


@dataclass(frozen=True, slots=True)
class ValidatedBatch:
    batch_id: uuid.UUID
    agent_id: str
    samples: tuple[ValidatedSample, ...]


def validate_sample(item: Any) -> ValidatedSample:
    if not isinstance(item, dict) or item.get("type") != "telemetry":
        raise InvalidBatch("Amostra deve ter type='telemetry'")
    stream_id = checked_uuid(item.get("stream_id"), "stream_id")
    sequence = checked_int(item, "sequence")
    received_ns = checked_int(item, "received_at_unix_ns", MIN_TIMESTAMP_NS, MAX_TIMESTAMP_NS)

    source = item.get("telemetry")
    if not isinstance(source, dict):
        raise InvalidBatch("telemetry precisa ser um objeto")
    if checked_int(source, "schema_version") != 1:
        raise InvalidBatch("telemetry.schema_version incompatível")

    frame = {
        "schema_version": 1,
        "timestamp_unix_ns": checked_int(source, "timestamp_unix_ns", MIN_TIMESTAMP_NS, MAX_TIMESTAMP_NS),
        "timestamp_monotonic_ns": checked_int(source, "timestamp_monotonic_ns", 1),
        "physics_packet_id": checked_int(source, "physics_packet_id", 1),
        "graphics_packet_id": checked_int(source, "graphics_packet_id"),
        "session_type": checked_int(source, "session_type", -1, 100),
        "completed_laps": checked_int(source, "completed_laps", 0, 1_000_000),
        "car": checked_string(source, "car"),
        "track": checked_string(source, "track"),
        "speed_kmh": checked_float(source, "speed_kmh", -600, 600),
        "rpm": checked_int(source, "rpm", 0, 30_000),
        "gear": checked_int(source, "gear", -1, 20),
        "throttle": checked_float(source, "throttle", 0, 1.0),
        "brake": checked_float(source, "brake", 0, 1.0),
        "clutch": checked_float(source, "clutch", 0, 1.0),
        "steer_angle_rad": checked_float(source, "steer_angle_rad", -30, 30),
        "heading_rad": checked_float(source, "heading_rad", -30, 30),
        "pitch_rad": checked_float(source, "pitch_rad", -30, 30),
        "roll_rad": checked_float(source, "roll_rad", -30, 30),
        "position_world_m": checked_vector(source, "position_world_m", 3),
        "velocity_world_mps": checked_vector(source, "velocity_world_mps", 3),
        "acceleration_g": checked_vector(source, "acceleration_g", 3),
        "angular_velocity_local_rad_s": checked_vector(source, "angular_velocity_local_rad_s", 3),
        "wheel_slip_raw": checked_vector(source, "wheel_slip_raw", 4),
    }
    speed_mps = checked_float(source, "speed_mps", -600 / 3.6, 600 / 3.6)
    if not math.isclose(speed_mps, frame["speed_kmh"] / 3.6, rel_tol=1e-5, abs_tol=1e-3):
        raise InvalidBatch("speed_mps não corresponde à velocidade em km/h")
    frame["speed_mps"] = frame["speed_kmh"] / 3.6
    digest = hashlib.sha256(json.dumps(
        frame, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    return ValidatedSample(stream_id, sequence, received_ns, frame, digest)


def validate_batch(message: Any, expected_agent_id: str) -> ValidatedBatch:
    if not isinstance(message, dict) or message.get("type") != "telemetry.batch":
        raise InvalidBatch("type deve ser telemetry.batch")
    if checked_int(message, "schema_version") != 1:
        raise InvalidBatch("schema_version do lote incompatível")
    batch_id = checked_uuid(message.get("batch_id"), "batch_id")
    agent_id = checked_string(message, "agent_id", 100)
    if not agent_id or agent_id != expected_agent_id:
        raise InvalidBatch("agent_id não autorizado para este token")
    raw_samples = message.get("samples")
    if not isinstance(raw_samples, list) or not 1 <= len(raw_samples) <= MAX_SAMPLES:
        raise InvalidBatch(f"samples exige de 1 até {MAX_SAMPLES} amostras")
    samples = tuple(validate_sample(item) for item in raw_samples)
    observed: dict[tuple[uuid.UUID, int], str] = {}
    for sample in samples:
        key = sample.stream_id, sample.sequence
        existing_hash = observed.setdefault(key, sample.frame_hash)
        if existing_hash != sample.frame_hash:
            raise InvalidBatch("Mesmo stream_id/sequence possui telemetrias divergentes")
    return ValidatedBatch(batch_id, agent_id, samples)
