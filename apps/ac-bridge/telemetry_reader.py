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
    ...