import copy
import uuid

import pytest

from telemetry.validators import InvalidBatch, validate_batch
from tests.helpers import make_batch, make_sample


def test_valid_agent_batch_and_speed_normalization():
    batch = validate_batch(make_batch([make_sample(sequence=0)]), "wsl-assetto-agent")
    assert len(batch.samples) == 1
    assert batch.samples[0].frame["speed_mps"] == pytest.approx(56 / 3.6)
    assert isinstance(batch.samples[0].stream_id, uuid.UUID)


def test_reject_agent_id_spoofing():
    with pytest.raises(InvalidBatch, match="agent_id"):
        validate_batch(make_batch([make_sample()]), "other-agent")


def test_reject_nan_and_inconsistent_units():
    sample = make_sample()
    sample["telemetry"]["speed_mps"] = float("nan")
    with pytest.raises(InvalidBatch):
        validate_batch(make_batch([sample]), "wsl-assetto-agent")
    sample["telemetry"]["speed_mps"] = 99.0
    with pytest.raises(InvalidBatch):
        validate_batch(make_batch([sample]), "wsl-assetto-agent")


def test_same_key_different_value_in_same_batch_rejected():
    sample = make_sample()
    changed = copy.deepcopy(sample)
    changed["telemetry"]["rpm"] = sample["telemetry"]["rpm"] + 100
    with pytest.raises(InvalidBatch, match="divergentes"):
        validate_batch(make_batch([sample, changed]), "wsl-assetto-agent")


def test_bad_type_and_missing_fields_rejected():
    sample = make_sample()
    sample["sequence"] = True
    with pytest.raises(InvalidBatch):
        validate_batch(make_batch([sample]), "wsl-assetto-agent")
    sample = make_sample()
    del sample["telemetry"]["position_world_m"]
    with pytest.raises(InvalidBatch):
        validate_batch(make_batch([sample]), "wsl-assetto-agent")
