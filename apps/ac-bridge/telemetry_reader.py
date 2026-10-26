"""Transform binary structures from Asseto Corsa in typed data for the network"""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

from shared_memory import ACSharedMemory, utf16_text

AC_LIVE = 2 # 0=OFF, 1=REPLAY, 2=LIVE, 3=PAUSE


class TelemetryStalledError(ConnectionError):
    """The game stopped updating the physics counter"""


@dataclass(frozen=True, slots=True)
class TelemetryFrame:
    schema_version: int
    timestamp_unix_ns: int
    timestamp_monotonic_ns: int
    physics_packet_id: int
    graphics_packet_id: int
    session_type: int
    completed_laps: int
    car: str
    track: str
    speed_kmh: float
    rpm: int
    gear: int  # normalized: -1=reverse, 0=neutral, 1=first...
    throttle: float
    brake: float
    clutch: float
    steer_angle_rad: float
    heading_rad: float
    pitch_rad: float
    roll_rad: float
    position_world_m: tuple[float, float, float]
    velocity_world_mps: tuple[float, float, float]
    acceleration_g: tuple[float, float, float]
    angular_velocity_local_rad_s: tuple[float, float, float]
    wheel_slip_raw: tuple[float, float, float, float]

    def asdict(self) -> dict:
        return asdict(self)


class TelemetryReader:
    def __init__(self, source: ACSharedMemory):
        self.source = source
        static = source.read_static()
        self.car = utf16_text(static.carModel)
        self.track = utf16_text(static.track)
        self._previous_packet: int | None = None
        self._last_update_at = time.monotonic()

    def read(self) -> TelemetryFrame | None:
        snapshot = self.source.read()
        if snapshot is None:
            return None
        p, g = snapshot
        if g.status != AC_LIVE:
            self._previous_packet = None
            return None
        if p.packetId <= 0:
            return None
        if p.packetId == self._previous_packet:
            if time.monotonic() - self._last_update_at > 5:
                raise TelemetryStalledError("No new Asseto Corsa packages for 5 seconds")
            return None

        values = (
            p.speedKmh, p.gas, p.brake, p.clutch, p.steerAngle,
            p.heading, p.pitch, p.roll,
            *p.velocity, *p.accG, *p.localAngularVel, *g.carCoordinates, *p.wheelSlip,
        )
        if not all(math.isfinite(v) for v in values):
            return None
        if not (0 <= p.gas <= 1.01 and 0 <= p.brake <= 1.01 and
                0 <= p.clutch <= 1.01 and abs(p.speedKmh) <= 600 and 
                0 <= p.rpms < 30000):
            return None

        self._previous_packet = p.packetId
        self._last_update_at = time.monotonic()
        return TelemetryFrame(
            schema_version=1,
            timestamp_unix_ns=time.time_ns(),
            timestamp_monotonic_ns=time.perf_counter_ns(),
            physics_packet_id=p.packetId,
            graphics_packet_id=g.packetId,
            session_type=g.session,
            completed_laps=g.completedLaps,
            car=self.car,
            track=self.track,
            speed_kmh=float(p.speedKmh),
            rpm=p.rpms,
            gear=p.gear - 1,
            throttle=float(p.gas),
            brake=float(p.brake),
            clutch=float(p.clutch),
            steer_angle_rad=float(p.steerAngle),
            heading_rad=float(p.heading),
            pitch_rad=float(p.pitch),
            roll_rad=float(p.roll),
            position_world_m=tuple(float(x) for x in g.carCoordinates),
            velocity_world_mps=tuple(float(x) for x in p.velocity),
            acceleration_g=tuple(float(x) for x in p.accG),
            angular_velocity_local_rad_s=tuple(float(x) for x in p.localAngularVel),
            wheel_slip_raw=tuple(float(x) for x in p.wheelSlip),            
        )
