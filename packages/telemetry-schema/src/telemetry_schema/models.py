"""v1 wire contract. Keys match TelemetryFrame.asdict() of the existing AC Bridge.

Keep this strictly separate from the ORM and from physical interpretation.
Only **documented original fields** belong to v1. Breaking changes => v2.
"""
from __future__ import annotations
from typing import Literal, NotRequired, TypedDict

Vector3 = tuple[float, float, float]
Vector4 = tuple[float, float, float, float]
Vector5 = tuple[float, float, float, float, float]

class TrackMap(TypedDict):
    source: str
    points: list[Vector3]
    image_url: NotRequired[str]
    map_config: NotRequired[dict[str, float]]

class CarVisual(TypedDict):
    id: str
    display_name: str
    brand: str
    asset_key: str
    source: str
    ui_metadata: bool
    model_format: str
    skin_id: NotRequired[str]

class TelemetryFrame(TypedDict):
    schema_version: Literal[1]
    timestamp_unix_ns: int
    timestamp_monotonic_ns: int
    physics_packet_id: int
    graphics_packet_id: int
    session_type: int
    completed_laps: int
    car: str
    track: str
    speed_kmh: float
    speed_mps: float
    rpm: int
    gear: int
    throttle: float
    brake: float
    clutch: float
    steer_angle_rad: float
    heading_rad: float
    pitch_rad: float
    roll_rad: float
    position_world_m: Vector3
    velocity_world_mps: Vector3
    acceleration_g: Vector3
    angular_velocity_local_rad_s: Vector3
    wheel_slip_raw: Vector4
    car_damage: NotRequired[Vector5]
    track_map: NotRequired[TrackMap]
    car_visual: NotRequired[CarVisual]

class SampleEnvelope(TypedDict):
    type: Literal["telemetry"]
    stream_id: str
    sequence: int
    received_at_unix_ns: int
    telemetry: TelemetryFrame

class BatchEnvelope(TypedDict):
    type: Literal["telemetry.batch"]
    schema_version: Literal[1]
    batch_id: str
    agent_id: str
    samples: list[SampleEnvelope]

class BatchAck(TypedDict):
    type: Literal["telemetry.ack"]
    batch_id: str
    accepted: int
