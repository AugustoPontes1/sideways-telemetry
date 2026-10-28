"""
Start the collection on windows and publush a NDJSON via TCP for WSL.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import time
import uuid

from shared_memory import ACSharedMemory
from car_metadata import find_car_directory_by_skin, load_car_metadata
from model_server import start_model_server
from session_config import load_active_content_ids
from telemetry_reader import TelemetryReader
from track_map import load_track_map

LOG = logging.getLogger("ac-bridge")
CONTENT_REFRESH_INTERVAL_S = 1.0
PLACEHOLDER_CONTENT_IDS = frozenset({"", "-", "0", "none", "unknown"})


def _usable_content_id(value: str) -> str | None:
    candidate = value.strip()
    return None if candidate.casefold() in PLACEHOLDER_CONTENT_IDS else candidate


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
        if self._socket is not None:
            self._socket.close()
            self._socket = None


def run(host: str, port: int, hz: int, ac_root: str | None,
        car_id_override: str | None, track_id_override: str | None) -> None:
    stream_id = str(uuid.uuid4())
    sequence = 0
    interval = 1 / hz
    start_model_server(ac_root, port=int(os.getenv("AC_MODEL_SERVER_PORT", "8766")))
    
    while True:
        try:
            with ACSharedMemory() as memory:
                reader = TelemetryReader(memory)
                with TcpPublisher(host, port) as publisher:
                    LOG.info("Stream %s transmitted for %s:%d to %d Hz", stream_id, host, port, hz)
                    next_tick = time.perf_counter()
                    configured_car: str | None = None
                    configured_skin: str | None = None
                    configured_track: str | None = None
                    layout_id: str | None = None
                    content_checked_at = 0.0
                    metadata_key: tuple[str, str, str, str] | None = None
                    car_visual = None
                    track_map = None
                    metadata_pending = False
                    while True:
                        frame = reader.read()
                        if frame is not None:
                            now = time.monotonic()
                            if now - content_checked_at >= CONTENT_REFRESH_INTERVAL_S:
                                configured_car, configured_skin, configured_track, layout_id = load_active_content_ids()
                                content_checked_at = now

                            shared_car = _usable_content_id(reader.car)
                            shared_track = _usable_content_id(reader.track)
                            car_id = car_id_override or shared_car or configured_car
                            if not car_id:
                                skin_car = find_car_directory_by_skin(ac_root, configured_skin or "")
                                car_id = skin_car.name if skin_car is not None else reader.car
                            track_id = track_id_override or shared_track or configured_track or reader.track
                            current_metadata_key = (car_id, configured_skin or "", track_id, layout_id or "")
                            if current_metadata_key != metadata_key:
                                metadata_key = current_metadata_key
                                LOG.info("Game content detected: %s%s / %s%s", car_id,
                                         f" / skin {configured_skin}" if configured_skin else "",
                                         track_id, f" / {layout_id}" if layout_id else "")
                                car_visual = load_car_metadata(ac_root, car_id, configured_skin)
                                if car_visual is None:
                                    LOG.warning("Car metadata unavailable for %s; frontend will use its adaptive fallback", car_id)
                                else:
                                    LOG.info("Car metadata loaded for %s (%s)", car_id, car_visual["display_name"])
                                track_map = load_track_map(ac_root, track_id, layout_id)
                                if track_map is None:
                                    LOG.warning("Track map unavailable for %s%s; frontend will use captured coordinates",
                                                track_id, f" ({layout_id})" if layout_id else "")
                                else:
                                    LOG.info("Track map loaded for %s%s from %s%s (%d points)", track_id,
                                             f" ({layout_id})" if layout_id else "",
                                             track_map["source"],
                                             " with map.ini" if track_map.get("map_config") else "",
                                             len(track_map["points"]))
                                metadata_pending = True

                            payload = frame.asdict()
                            if car_id != reader.car:
                                payload["car"] = car_id
                            if track_id != reader.track:
                                payload["track"] = track_id
                            if metadata_pending:
                                if car_visual is not None:
                                    payload["car_visual"] = car_visual
                                if track_map is not None:
                                    payload["track_map"] = track_map
                                metadata_pending = False
                            publisher.send(
                                {
                                    "type": "telemetry",
                                    "stream_id": stream_id,
                                    "sequence": sequence,
                                    "telemetry": payload,
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
    parser.add_argument("--ac-root", default=os.getenv("AC_ROOT"),
                        help="Assetto Corsa installation root (or set AC_ROOT)")
    parser.add_argument("--car-id", default=os.getenv("AC_CAR_ID"),
                        help="Override shared-memory car ID with content/cars folder ID")
    parser.add_argument("--track-id", default=os.getenv("AC_TRACK_ID"),
                        help="Override shared-memory track ID with content/tracks folder ID")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        run(args.host, args.port, args.hz, args.ac_root, args.car_id, args.track_id)
    except KeyboardInterrupt:
        LOG.info("Collection finished")


if __name__ == "__main__":
    main()
