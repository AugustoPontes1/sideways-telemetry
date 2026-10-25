"""Run without installing dependencies: PYTHONPATH is extended to local src folders."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for relative in (
    "packages/telemetry-schema/src",
    "packages/drift-math/src",
    "packages/drift-analysis/src",
):
    sys.path.insert(0, str(ROOT / relative))
