"""Serve converted car meshes and installed track-map assets to the frontend."""
from __future__ import annotations

import hashlib
import http.server
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from threading import Lock, Thread
from urllib.parse import parse_qs, unquote, urlsplit

from car_metadata import find_car_directory, find_direct_model_asset, find_kn5_candidates, find_skin_directory
from track_map import find_track_map_image

LOG = logging.getLogger("ac-bridge.models")
MODEL_ROUTE = "/car-models/"
TRACK_MAP_ROUTE = "/track-maps/"
MAX_MODEL_BYTES = 128 * 1024 * 1024
MAX_TRACK_MAP_BYTES = 16 * 1024 * 1024
MODEL_FAILURE_RETRY_SECONDS = 300


def _http_error_detail(error: object) -> str:
    detail = " ".join(str(error).split())
    return detail[:240] or "asset unavailable"


class ModelConversionError(RuntimeError):
    pass


class ModelAssetService:
    def __init__(self, ac_root: str | None, cache_dir: Path | None = None):
        self.ac_root = ac_root
        self.cache_dir = cache_dir or Path(
            os.getenv("AC_MODEL_CACHE", Path.home() / ".cache" / "drift-telemetry" / "car-models")
        )
        self._locks: dict[str, Lock] = {}
        self._locks_guard = Lock()
        self._failed_models: dict[tuple[str, str], tuple[float, str]] = {}

    def _cache_path(self, car_id: str, skin_id: str) -> Path:
        digest = hashlib.sha256(f"{car_id}\0{skin_id}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.glb"

    def _lock_for(self, car_id: str) -> Lock:
        with self._locks_guard:
            return self._locks.setdefault(car_id, Lock())

    def _converter_command(self) -> list[str]:
        configured = os.getenv("KN5_TO_GLTF_COMMAND", "").strip()
        if configured:
            return shlex.split(configured, posix=os.name != "nt")
        return [sys.executable, "-m", "acgltf.convert"]

    def get_model(self, car_id: str, skin_id: str = "") -> Path:
        if not car_id or "/" in car_id or "\\" in car_id or car_id in {".", ".."}:
            raise ModelConversionError("invalid car identifier")
        if "/" in skin_id or "\\" in skin_id or skin_id in {".", ".."}:
            raise ModelConversionError("invalid skin identifier")
        cached = self._cache_path(car_id, skin_id)
        if cached.is_file() and cached.stat().st_size <= MAX_MODEL_BYTES:
            return cached

        with self._lock_for(car_id):
            if cached.is_file() and cached.stat().st_size <= MAX_MODEL_BYTES:
                return cached
            failure_key = (car_id, skin_id)
            previous_failure = self._failed_models.get(failure_key)
            if previous_failure and time.monotonic() - previous_failure[0] < MODEL_FAILURE_RETRY_SECONDS:
                raise ModelConversionError(previous_failure[1])
            car_directory = find_car_directory(self.ac_root, car_id)
            if car_directory is None:
                raise ModelConversionError(f"car folder not found: {car_id}")
            direct_model = find_direct_model_asset(car_directory)
            if direct_model is not None:
                if direct_model.stat().st_size > MAX_MODEL_BYTES:
                    raise ModelConversionError("installed GLB model exceeds the size limit")
                temporary_cache = cached.with_suffix(".tmp")
                shutil.copyfile(direct_model, temporary_cache)
                os.replace(temporary_cache, cached)
                LOG.info("Using installed GLB %s for %s", direct_model, car_id)
                return cached
            kn5_candidates = find_kn5_candidates(car_directory)
            if not kn5_candidates:
                raise ModelConversionError(f"render KN5 not found: {car_directory}")
            skin_directory = find_skin_directory(car_directory, skin_id) if skin_id else None
            resolved_skin = skin_directory.name if skin_directory is not None else ""
            if skin_id and not resolved_skin:
                LOG.warning("Active skin %s was not found for %s; using the converter default", skin_id, car_id)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            failures: list[str] = []
            with tempfile.TemporaryDirectory(prefix="kn5-", dir=self.cache_dir) as temporary:
                output_dir = Path(temporary)
                for kn5_path in kn5_candidates:
                    generated = output_dir / "car.glb"
                    generated.unlink(missing_ok=True)
                    command = self._converter_command() + [
                        str(kn5_path), str(output_dir), "--name", "car", "--glb",
                    ]
                    if resolved_skin:
                        command.extend(["--skin", resolved_skin])
                    try:
                        result = subprocess.run(
                            command,
                            capture_output=True,
                            text=True,
                            timeout=120,
                            check=False,
                            cwd=str(Path(sys.executable).resolve().parent),
                        )
                    except (OSError, subprocess.TimeoutExpired) as error:
                        failures.append(f"{kn5_path.name}: converter unavailable: {error}")
                        continue
                    if result.returncode != 0:
                        output = result.stderr or result.stdout
                        lines = [line.strip() for line in output.splitlines() if line.strip()]
                        detail = " ".join(lines[-3:])[-500:]
                        failures.append(f"{kn5_path.name}: conversion failed: {detail}")
                        continue
                    if not generated.is_file():
                        failures.append(f"{kn5_path.name}: converter did not produce car.glb")
                        continue
                    if generated.stat().st_size > MAX_MODEL_BYTES:
                        failures.append(f"{kn5_path.name}: converted model exceeds the size limit")
                        continue
                    temporary_cache = cached.with_suffix(".tmp")
                    shutil.copyfile(generated, temporary_cache)
                    os.replace(temporary_cache, cached)
                    self._failed_models.pop(failure_key, None)
                    LOG.info("Converted %s with skin %s to %s", kn5_path, skin_id or "default", cached)
                    return cached
            detail = "; ".join(failures)[-1000:]
            self._failed_models[failure_key] = (time.monotonic(), detail or "KN5 conversion failed")
            raise ModelConversionError(detail or "KN5 conversion failed")

    def get_track_map(self, track_id: str, layout_id: str = "") -> Path:
        if not track_id or "/" in track_id or "\\" in track_id or track_id in {".", ".."}:
            raise ModelConversionError("invalid track identifier")
        if "/" in layout_id or "\\" in layout_id or layout_id in {".", ".."}:
            raise ModelConversionError("invalid layout identifier")
        image = find_track_map_image(self.ac_root, track_id, layout_id or None)
        if image is None:
            raise ModelConversionError(f"track map not found: {track_id}")
        if image.stat().st_size > MAX_TRACK_MAP_BYTES:
            raise ModelConversionError("track map exceeds the size limit")
        return image


def _handler_for(service: ModelAssetService) -> type[http.server.BaseHTTPRequestHandler]:
    class ModelRequestHandler(http.server.BaseHTTPRequestHandler):
        def _send_not_found(self, error: object) -> None:
            self.send_error(http.server.HTTPStatus.NOT_FOUND, _http_error_detail(error))

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            if path.startswith(TRACK_MAP_ROUTE):
                suffix = next(
                    (value for value in (".png", ".jpg", ".jpeg") if path.endswith(value)),
                    None,
                )
                if suffix is None:
                    self.send_error(http.server.HTTPStatus.NOT_FOUND)
                    return
                track_id = unquote(path[len(TRACK_MAP_ROUTE):-len(suffix)])
                layout_id = query.get("layout", [""])[0]
                try:
                    image_path = service.get_track_map(track_id, layout_id)
                except (ModelConversionError, OSError) as error:
                    detail = _http_error_detail(error)
                    LOG.warning("Unable to serve track map for %s: %s", track_id, detail)
                    self._send_not_found(detail)
                    return
                content_type = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                }[suffix]
                self.send_response(http.server.HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(image_path.stat().st_size))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                try:
                    with image_path.open("rb") as stream:
                        shutil.copyfileobj(stream, self.wfile)
                except (BrokenPipeError, ConnectionResetError):
                    return
                return
            if not path.startswith(MODEL_ROUTE) or not path.endswith(".glb"):
                self.send_error(http.server.HTTPStatus.NOT_FOUND)
                return
            car_id = unquote(path[len(MODEL_ROUTE):-4])
            skin_id = query.get("skin", [""])[0]
            try:
                model_path = service.get_model(car_id, skin_id)
            except ModelConversionError as error:
                detail = _http_error_detail(error)
                LOG.warning("Unable to serve model for %s: %s", car_id, detail)
                self._send_not_found(detail)
                return
            self.send_response(http.server.HTTPStatus.OK)
            self.send_header("Content-Type", "model/gltf-binary")
            self.send_header("Content-Length", str(model_path.stat().st_size))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            try:
                with model_path.open("rb") as stream:
                    shutil.copyfileobj(stream, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                return

        def log_message(self, format: str, *args: object) -> None:
            LOG.debug("model server: " + format, *args)

    return ModelRequestHandler


def start_model_server(ac_root: str | None, host: str = "127.0.0.1", port: int = 8766):
    if port <= 0:
        return None
    service = ModelAssetService(ac_root)
    try:
        server = http.server.ThreadingHTTPServer((host, port), _handler_for(service))
    except OSError as error:
        LOG.warning("Car model server unavailable on %s:%d: %s", host, port, error)
        return None
    Thread(target=server.serve_forever, name="car-model-server", daemon=True).start()
    LOG.info("Car model server listening on http://%s:%d", host, port)
    return server
