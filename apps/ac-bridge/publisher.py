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

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._socket is None:
            self._socket.close()
            self._socket = None


def run(host: str, port: int, hz: int) -> None:
    stream_id = str(uuid.uuid4())
    sequence = 0
    interval = 1 / hz
    
    while True:
        try:
            with ACSharedMemory() as memory:
                reader = TelemetryReader(memory)
                LOG.info("Game detected: %s / %s", reader.car, reader.track)
                with TcpPublisher(host, port) as publisher:
                    LOG.info("Transmitted for %s:%d to %d Hz", host, port, hz)
                    next_tick = time.perf_counter()
                    while True:
                        frame = reader.read()
                        if frame is not None:
                            publisher.send(
                                {
                                    "type": "telemetry",
                                    "stream_id": stream_id,
                                    "sequence": sequence,
                                    "telemetry": frame.asdict(),
                                }
                            )
                            sequence += 1
                        next_tick += interval
                        delay = next_tick - time.perf_counter()
                        if delay > 0:
                            time.sleep(delay)
                        else:
                            # Avoid showing all the samples at the same time to avoid delays
                            next_tick = time.perf_counter()
                    
        except (FileNotFoundError, ConnectionError, TimeoutError, OSError) as error:
            LOG.warning("Unavailable bridge (%s). Attempts in 2 seconds...", error)
            time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Asseto Corsa -> WSL telemetry bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Reachable WSL Address for Windows")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--hz", type=int, default=50, choices=range(1, 101), metavar="1..100")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s% (levelname)s %(message)s")
    try:
        run(args.host, args.port, args.hz)
    except KeyboardInterrupt:
        LOG.info("Collection finished")


if __name__ == "__main__":
    main()