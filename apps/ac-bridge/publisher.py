"""
Start the collection on windows and publush a NDJSON via TCP for WSL.
"""

from __future__ import annotations

import argparse
import json
import logging
import socket
import time
import uuid

from shared_memory import ACSharedMemory
from telemetry_reader import TelemetryReader

LOG = logging.getLogger("ac-bridge")


class TcpPublisher:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None

    def __enter__(self) -> "TcpPublisher":
        self._socket = socket.create_connection((self.host, self.port), timeout=3)
        self._socket.settimeout(2)
        return self

    def send(self, payload: dict) -> None:
        raw = json.dumps(payload, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(raw) > 65536:
            raise ValueError("Frame size not allowed")
        assert self._socket is not None
        self._socket.sendall(raw)

    