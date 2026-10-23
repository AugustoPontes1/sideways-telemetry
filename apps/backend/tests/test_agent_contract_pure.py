"""Valida a integração com o normalizer.py REAL do Telemetry Agent anterior."""
import importlib.util
import sys
from pathlib import Path

import pytest

from apps.backend.telemetry.validators import validate_batch
from apps.backend.tests.helpers import make_batch, make_sample


AGENT_FILE = Path(__file__).resolve().parents[2] / "telemetry-agent" / "normalizer.py"


def test_normalized_previous_agent_is_accepted():
    if not AGENT_FILE.is_file():
        pytest.skip("Telemetry Agent anterior não está junto ao backend")
    spec = importlib.util.spec_from_file_location("prior_normalizer", AGENT_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    original = make_sample()
    original["telemetry"].pop("speed_mps")  # AC Bridge ainda não transmite isso
    normalized = module.TelemetryNormalizer().normalize(original)
    assert normalized["telemetry"]["speed_mps"] == pytest.approx(56.0 / 3.6)

    batch = validate_batch(make_batch([normalized]), "wsl-assetto-agent")
    assert batch.samples[0].frame["rpm"] == 4500
    assert batch.samples[0].sequence == 0
