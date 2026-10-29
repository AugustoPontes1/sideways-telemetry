"""Validation and normalization of NDJSON samples produced by AC Bridge.

Does not calculate advanced physics: drift angle and local axes depend on
validating coordinate conventions against the actual game.
"""
from __future__ import annotations

import math
import re
import time
import uuid
from collections.abc import Mapping


class InvalidTelemetry(ValueError):
    """Message incompatible with the Windows bridge contract."""


MAX_TRACK_MAP_POINTS = 1200
MAX_CAR_VISUAL_TEXT = 160
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


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


def _track_map(data: Mapping) -> dict | None:
    value = data.get("track_map")
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise InvalidTelemetry("track_map: esperado objeto")
    source = _text(value, "source", 64)
    image_url = value.get("image_url")
    if image_url is not None:
        image_url = _text(value, "image_url", 512)
        if not image_url.startswith("/track-maps/"):
            raise InvalidTelemetry("track_map.image_url: asset local esperado")
    points = value.get("points")
    if not isinstance(points, list) or len(points) > MAX_TRACK_MAP_POINTS:
        raise InvalidTelemetry(f"track_map.points: esperado de 0 até {MAX_TRACK_MAP_POINTS} pontos")
    if len(points) < 2 and image_url is None:
        raise InvalidTelemetry("track_map: esperado pelo menos 2 pontos ou image_url")
    normalized_points = [_vector({"point": point}, "point", 3) for point in points]
    result = {"source": source, "points": normalized_points}
    if image_url is not None:
        result["image_url"] = image_url
    map_config = value.get("map_config")
    if map_config is not None:
        if not isinstance(map_config, Mapping):
            raise InvalidTelemetry("track_map.map_config: esperado objeto")
        config = {}
        for name in ("width", "height", "offset_x", "offset_z", "scale_factor"):
            raw = map_config.get(name)
            if type(raw) not in (int, float) or not math.isfinite(raw):
                raise InvalidTelemetry(f"track_map.map_config.{name}: esperado número finito")
            config[name] = float(raw)
        if config["width"] <= 0 or config["height"] <= 0:
            raise InvalidTelemetry("track_map.map_config: largura e altura devem ser positivas")
        result["map_config"] = config
    return result


def _car_visual(data: Mapping) -> dict | None:
    value = data.get("car_visual")
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise InvalidTelemetry("car_visual: esperado objeto")
    car_id = _text(value, "id", MAX_CAR_VISUAL_TEXT)
    display_name = _text(value, "display_name", MAX_CAR_VISUAL_TEXT)
    brand = _text(value, "brand", 80)
    asset_key = _text(value, "asset_key", MAX_CAR_VISUAL_TEXT)
    source = _text(value, "source", 64)
    model_format = _text(value, "model_format", 16)
    skin_id = value.get("skin_id", "")
    if not isinstance(skin_id, str) or len(skin_id) > MAX_CAR_VISUAL_TEXT or any(ord(ch) < 32 for ch in skin_id):
        raise InvalidTelemetry("car_visual.skin_id: texto inválido")
    color_hex = value.get("color_hex", "")
    if not isinstance(color_hex, str) or color_hex and not HEX_COLOR_RE.fullmatch(color_hex):
        raise InvalidTelemetry("car_visual.color_hex: cor hexadecimal inválida")
    ui_metadata = value.get("ui_metadata")
    if type(ui_metadata) is not bool:
        raise InvalidTelemetry("car_visual.ui_metadata: esperado booleano")
    return {
        "id": car_id,
        "display_name": display_name,
        "brand": brand,
        "asset_key": asset_key,
        "source": source,
        "ui_metadata": ui_metadata,
        "model_format": model_format,
        "skin_id": skin_id,
        "color_hex": color_hex,
    }


class TelemetryNormalizer:
    """Ensure schema v1, explicit units, and deduplication identifiers."""

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
            "car_damage": _vector(frame, "car_damage", 5) if "car_damage" in frame else [0.0] * 5,
        }
        track_map = _track_map(frame)
        if track_map is not None:
            normalized["track_map"] = track_map
        car_visual = _car_visual(frame)
        if car_visual is not None:
            normalized["car_visual"] = car_visual
        if any(value < 0 for value in normalized["car_damage"]):
            raise InvalidTelemetry("car_damage: valor negativo")
        for name in ("throttle", "brake", "clutch"):
            normalized[name] = min(normalized[name], 1.0)

        # Convert units unambiguously without interpreting yaw/heading yet.
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
