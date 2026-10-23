"""Builders shared by test tools; real AC Bridge keeps producing the v1 envelope."""
from __future__ import annotations
import json
import uuid
from collections.abc import Iterable, Mapping
from typing import Any
from .validation import validate_batch, validate_sample

def encode_message(message: Mapping[str, Any]) -> str:
    return json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(",", ":"))

def new_batch(samples: Iterable[Mapping[str, Any]], agent_id: str,
              batch_id: str | None = None) -> dict[str, Any]:
    return validate_batch({
        "type": "telemetry.batch", "schema_version": 1,
        "batch_id": batch_id or str(uuid.uuid4()),
        "agent_id": agent_id, "samples": [validate_sample(s) for s in samples],
    })
