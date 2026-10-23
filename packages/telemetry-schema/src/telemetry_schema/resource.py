"""Optional JSON Schema distribution for TS/front-end tooling and protocol docs."""
from __future__ import annotations
import json
from importlib.resources import files

def load_json_schema_v1() -> dict:
    """Schema describes shapes; only Python validators enforce cross-field invariants."""
    source = files("telemetry_schema").joinpath("schemas/telemetry-v1.schema.json")
    return json.loads(source.read_text(encoding="utf-8"))
