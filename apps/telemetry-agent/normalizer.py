"""Validação e normalização das amostras NDJSON produzidas pelo AC Bridge.

Não calcula física avançada: ângulo de drift e eixos locais dependem de
validação de convenções de coordenadas com o jogo real.
"""
from __future__ import annotations

import math
import time
import uuid
from collections.abc import Mapping


class InvalidTelemetry(ValueError):
    """Mensagem incompatível com o contrato da ponte Windows."""


def _integer(data: Mapping, key: str, *, minimum: int = 0, maximum: int = 2**63 - 1) -> int:
    value = data.get(key)
    if type(value) is not int or not minimum <= value <= maximum:
        raise InvalidTelemetry(f"{key}: esperado inteiro entre {minimum} e {maximum}")
    return value


def _number(data: Mapping, key: str, *, minimum: float = -1e12,
            maximum: float = 1e12) -> float:
    value = data.get(key)
    if type(value) not in (float, int) or not math.isfinite(value):
        raise InvalidTelemetry(f"{key}: esperado número finito")
    if not minimum <= value <= maximum:
        raise InvalidTelemetry(f"{key}: fora do intervalo permitido")
    return float(value)


def _vector(data: Mapping, key: str, size: int) -> list[float]:
    value = data.get(key)
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise InvalidTelemetry(f"{key}: esperado vetor de {size} componentes")
    result: list[float] = []
    for coordinate in value:
        if type(coordinate) not in (float, int) or not math.isfinite(coordinate):
            raise InvalidTelemetry(f"{key}: coordenada não numérica ou não finita")
        if abs(coordinate) > 1e9:
            raise InvalidTelemetry(f"{key}: coordenada fora do intervalo")
        result.append(float(coordinate))
    return result


def _text(data: Mapping, key: str, max_length: int = 160) -> str:
    value = data.get(key)
    if not isinstance(value, str) or len(value) > max_length:
        raise InvalidTelemetry(f"{key}: texto inválido")
    return value


class TelemetryNormalizer:
    """Garante schema v1, unidades explícitas e identificadores de deduplicação."""

    def normalize(self, message: Mapping, received_at_unix_ns: int | None = None) -> dict:
        if not isinstance(message, Mapping) or message.get("type") != "telemetry":
            raise InvalidTelemetry("type deve ser 'telemetry'")

        stream_raw = message.get("stream_id")
        if not isinstance(stream_raw, str) or len(stream_raw) > 64:
            raise InvalidTelemetry("stream_id ausente ou inválido")
        try:
            stream_id = str(uuid.UUID(stream_raw))
        except (ValueError, AttributeError) as exc:
            raise InvalidTelemetry("stream_id deve ser UUID") from exc
        sequence = _integer(message, "sequence")

        frame = message.get("telemetry")
        if not isinstance(frame, Mapping):
            raise InvalidTelemetry("telemetry deve ser um objeto")
        if _integer(frame, "schema_version") != 1:
            raise InvalidTelemetry("schema_version diferente de 1")

        # Campos exatamente correspondentes a TelemetryFrame do ac-bridge v1.
        normalized = {
            "schema_version": 1,
            "timestamp_unix_ns": _integer(frame, "timestamp_unix_ns", minimum=1),
            "timestamp_monotonic_ns": _integer(frame, "timestamp_monotonic_ns", minimum=1),
            "physics_packet_id": _integer(frame, "physics_packet_id", minimum=1),
            "graphics_packet_id": _integer(frame, "graphics_packet_id"),
            "session_type": _integer(frame, "session_type", minimum=-1, maximum=100),
            "completed_laps": _integer(frame, "completed_laps", maximum=1_000_000),
            "car": _text(frame, "car"),
            "track": _text(frame, "track"),
            "speed_kmh": _number(frame, "speed_kmh", minimum=-600, maximum=600),
            "rpm": _integer(frame, "rpm", maximum=30_000),
            "gear": _integer(frame, "gear", minimum=-1, maximum=20),
            "throttle": _number(frame, "throttle", minimum=0, maximum=1.01),
            "brake": _number(frame, "brake", minimum=0, maximum=1.01),
            "clutch": _number(frame, "clutch", minimum=0, maximum=1.01),
            "steer_angle_rad": _number(frame, "steer_angle_rad", minimum=-30, maximum=30),
            "heading_rad": _number(frame, "heading_rad", minimum=-30, maximum=30),
            "pitch_rad": _number(frame, "pitch_rad", minimum=-30, maximum=30),
            "roll_rad": _number(frame, "roll_rad", minimum=-30, maximum=30),
            "position_world_m": _vector(frame, "position_world_m", 3),
            "velocity_world_mps": _vector(frame, "velocity_world_mps", 3),
            "acceleration_g": _vector(frame, "acceleration_g", 3),
            "angular_velocity_local_rad_s": _vector(frame, "angular_velocity_local_rad_s", 3),
            "wheel_slip_raw": _vector(frame, "wheel_slip_raw", 4),
        }
        for name in ("throttle", "brake", "clutch"):
            normalized[name] = min(normalized[name], 1.0)

        # Conversão de unidade inequívoca, sem interpretar ainda yaw/heading.
        normalized["speed_mps"] = normalized["speed_kmh"] / 3.6
        received_ns = time.time_ns() if received_at_unix_ns is None else received_at_unix_ns
        if type(received_ns) is not int or received_ns <= 0:
            raise InvalidTelemetry("received_at_unix_ns inválido")
        return {
            "type": "telemetry",
            "stream_id": stream_id,
            "sequence": sequence,
            "received_at_unix_ns": received_ns,
            "telemetry": normalized,
        }
