"""Synthetic messages compatible with the Telemetry Agent's normalizer.py."""
import time
import uuid


def make_sample(stream_id=None, sequence=0, *, speed=56.0, rpm=4500,
                position=None, velocity=None):
    stream_id = str(stream_id or uuid.UUID(int=101))
    return {
        "type": "telemetry",
        "stream_id": stream_id,
        "sequence": sequence,
        "received_at_unix_ns": time.time_ns(),
        "telemetry": {
            "schema_version": 1,
            "timestamp_unix_ns": time.time_ns(),
            "timestamp_monotonic_ns": time.monotonic_ns(),
            "physics_packet_id": sequence + 1,
            "graphics_packet_id": sequence + 1,
            "session_type": 4,
            "completed_laps": 0,
            "car": "test_car",
            "track": "test_track",
            "speed_kmh": speed,
            "speed_mps": speed / 3.6,
            "rpm": rpm,
            "gear": 2,
            "throttle": 0.75,
            "brake": 0.0,
            "clutch": 0.0,
            "steer_angle_rad": 0.25,
            "heading_rad": 0.15,
            "pitch_rad": 0.0,
            "roll_rad": 0.0,
            "position_world_m": position or [1.0, 0.0, 2.0],
            "velocity_world_mps": velocity or [3.0, 0.0, 4.0],
            "acceleration_g": [0.1, 0.0, 0.2],
            "angular_velocity_local_rad_s": [0.0, 0.1, 0.0],
            "wheel_slip_raw": [0.02, 0.02, 0.05, 0.05],
        },
    }


def make_batch(samples, batch_id=None):
    return {
        "type": "telemetry.batch",
        "schema_version": 1,
        "batch_id": str(batch_id or uuid.uuid4()),
        "agent_id": "wsl-assetto-agent",
        "samples": samples,
    }
