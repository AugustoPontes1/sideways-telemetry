from __future__ import annotations
import copy
import importlib.util
import sys
import time
import uuid
from pathlib import Path
import pytest
from telemetry_schema import SchemaError, validate_frame, validate_sample, validate_batch, validate_ack, new_batch


def fixture_sample(sequence=0):
    now = time.time_ns()
    frame = {
        "schema_version": 1, "timestamp_unix_ns": now, "timestamp_monotonic_ns": time.monotonic_ns(),
        "physics_packet_id": 2, "graphics_packet_id": 2, "session_type": 4, "completed_laps": 0,
        "car": "suzuki_cappuccino", "track": "test_track", "speed_kmh": 72.0, "speed_mps": 20.0,
        "rpm": 5100, "gear": 2, "throttle": 0.7, "brake": 0, "clutch": 0,
        "steer_angle_rad": .2, "heading_rad": .1, "pitch_rad": 0, "roll_rad": 0,
        "position_world_m": [1, 0, 2], "velocity_world_mps": [0, 0, 20],
        "acceleration_g": [0, 0, 0], "angular_velocity_local_rad_s": [0, 0, 0],
        "wheel_slip_raw": [0, 0, 0, 0],
    }
    return {"type": "telemetry", "stream_id": str(uuid.UUID(int=1)), "sequence": sequence,
            "received_at_unix_ns": now, "telemetry": frame}


def test_sample_matches_existing_v1_contract():
    sample = validate_sample(fixture_sample())
    assert sample["telemetry"]["speed_mps"] == 20
    assert sample["telemetry"]["position_world_m"] == [1, 0, 2]
    assert isinstance(sample["sequence"], int)


def test_compatibility_with_django_pure_validator():
    # Import only Django-free validator from original backend, no Django runtime needed.
    base = Path(__file__).resolve().parents[1] / "backend/telemetry/validators.py"
    spec = importlib.util.spec_from_file_location("existing_v1_validator_for_test", base)
    import types
    namespace = types.ModuleType("existing_v1_validator_for_test")
    sys.modules[namespace.__name__] = namespace
    spec.loader.exec_module(namespace)  # type: ignore[union-attr]
    sample = fixture_sample()
    batch = new_batch([sample], "wsl-assetto-agent")
    validated = namespace.validate_batch(batch, "wsl-assetto-agent")
    assert len(validated.samples) == 1
    assert validated.samples[0].frame["rpm"] == sample["telemetry"]["rpm"]


def test_no_bool_in_numeric_fields():
    sample = fixture_sample(); sample["telemetry"]["throttle"] = True
    with pytest.raises(SchemaError): validate_sample(sample)


def test_reject_nonfinite_and_wrong_units():
    sample = fixture_sample(); sample["telemetry"]["rpm"] = float("nan")
    with pytest.raises(SchemaError): validate_sample(sample)
    sample = fixture_sample(); sample["telemetry"]["speed_mps"] = 50
    with pytest.raises(SchemaError, match="inconsistent"): validate_sample(sample)


def test_duplicate_and_oversized_batch_rejected():
    sample = fixture_sample()
    with pytest.raises(SchemaError, match="duplicate"):
        new_batch([sample, sample], "wsl-assetto-agent")
    with pytest.raises(SchemaError, match="1..100"):
        new_batch([fixture_sample(i) for i in range(101)], "wsl-assetto-agent")


def test_ack_only_accepts_full_matching_batch():
    batch_id = str(uuid.uuid4())
    ack = {"type":"telemetry.ack", "batch_id":batch_id, "accepted":3}
    assert validate_ack(ack, batch_id=batch_id, sample_count=3)["accepted"] == 3
    with pytest.raises(SchemaError): validate_ack(ack, batch_id=batch_id, sample_count=2)
    with pytest.raises(SchemaError): validate_ack({**ack, "accepted":True},batch_id=batch_id,sample_count=3)


def test_packaged_json_schema_is_available():
    from telemetry_schema import load_json_schema_v1
    schema = load_json_schema_v1()
    assert schema["$defs"]["Batch"]["properties"]["type"]["const"] == "telemetry.batch"
    assert "wheel_slip_raw" in schema["$defs"]["TelemetryFrame"]["properties"]


def test_original_wsl_normalizer_to_shared_schema_to_django_validator():
    # Pure Python chain, using *existing actual modules* from v3 package.
    from importlib.util import module_from_spec, spec_from_file_location
    base = Path(__file__).resolve().parents[1]
    file = base / 'telemetry-agent/normalizer.py'
    spec = spec_from_file_location('actual_wsl_normalizer', file)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    bridge_message = fixture_sample(sequence=7)
    bridge_message['telemetry'].pop('speed_mps')  # raw AC Bridge has no speed_mps
    normalized = mod.TelemetryNormalizer().normalize(bridge_message)
    result = validate_sample(normalized)
    batch = new_batch([result], agent_id='wsl-assetto-agent')
    validated = validate_batch(batch, expected_agent_id='wsl-assetto-agent')
    assert validated['samples'][0]['sequence'] == 7
    assert validated['samples'][0]['telemetry']['speed_mps'] == 20
