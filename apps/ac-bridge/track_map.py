"""Read Assetto Corsa AI lines and installed overview images for a track."""
from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import Any
from urllib.parse import quote

from content_paths import candidate_roots

MAX_TRACK_POINTS = 1200
AI_HEADER = struct.Struct("<4i")
AI_POINT = struct.Struct("<4fi")
AI_FILENAMES = ("fast_lane.ai", "ideal_line.ai")
MAP_FILENAMES = ("map.png", "map.jpg", "map.jpeg", "outline.png")


def _name_key(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _matching_child(
    directory: Path,
    name: str,
    *,
    want_directory: bool | None = None,
) -> Path | None:
    """Find a child without relying on the host filesystem's case rules."""
    direct = directory / name
    if direct.exists() and (want_directory is None or direct.is_dir() == want_directory):
        return direct
    if not directory.is_dir():
        return None
    wanted = name.casefold()
    try:
        children = sorted(directory.iterdir(), key=lambda path: path.name.casefold())
    except OSError:
        return None
    for child in children:
        if child.name.casefold() == wanted and (
            want_directory is None or child.is_dir() == want_directory
        ):
            return child
    return None


def _track_ai_candidates(track_dir: Path, layout_name: str | None = None) -> list[Path]:
    """Return likely complete-track AI lines, including modded layouts."""
    if not track_dir.is_dir():
        return []

    candidates: list[Path] = []
    seen: set[str] = set()

    def add(path: Path | None) -> None:
        if path is None or not path.is_file():
            return
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            candidates.append(path)

    layout_dirs: list[Path] = []
    if layout_name:
        layout_dir = _matching_child(track_dir, layout_name, want_directory=True)
        if layout_dir is not None:
            layout_dirs.append(layout_dir)

    for directory in layout_dirs + [track_dir]:
        ai_dir = _matching_child(directory, "ai", want_directory=True)
        if ai_dir is None:
            continue
        for filename in AI_FILENAMES:
            add(_matching_child(ai_dir, filename, want_directory=False))

    try:
        layout_candidates = sorted(
            (child for child in track_dir.iterdir() if child.is_dir()),
            key=lambda path: path.name.casefold(),
        )
    except OSError:
        layout_candidates = []
    for layout_dir in layout_candidates:
        ai_dir = _matching_child(layout_dir, "ai", want_directory=True)
        if ai_dir is None:
            continue
        for filename in AI_FILENAMES:
            add(_matching_child(ai_dir, filename, want_directory=False))

    try:
        nested = sorted(
            (
                path
                for path in track_dir.rglob("*")
                if path.is_file() and path.name.casefold() in AI_FILENAMES
            ),
            key=lambda path: (path.name.casefold(), str(path).casefold()),
        )
    except OSError:
        nested = []
    for path in nested:
        add(path)

    return candidates


def _track_ai_file(track_dir: Path, layout_name: str | None = None) -> Path | None:
    candidates = _track_ai_candidates(track_dir, layout_name)
    return candidates[0] if candidates else None


def _track_directory(tracks_root: Path, track_name: str) -> Path | None:
    direct = _matching_child(tracks_root, track_name, want_directory=True)
    if direct is not None:
        return direct
    if not tracks_root.is_dir():
        return None
    wanted = track_name.casefold()
    wanted_key = _name_key(track_name)
    try:
        candidates = sorted(
            (path for path in tracks_root.iterdir() if path.is_dir()),
            key=lambda path: path.name.casefold(),
        )
    except OSError:
        return None
    for track_dir in candidates:
        name = track_dir.name.casefold()
        key = _name_key(track_dir.name)
        if name == wanted or (wanted_key and (wanted_key in key or key in wanted_key)):
            return track_dir
    return None


def _track_asset_file(
    track_dir: Path,
    filenames: tuple[str, ...],
    layout_name: str | None = None,
) -> Path | None:
    layout_dir = _matching_child(track_dir, layout_name, want_directory=True) if layout_name else None
    directories: list[Path] = []
    if layout_dir is not None:
        directories.append(layout_dir)
    directories.append(track_dir)
    try:
        directories.extend(
            sorted(
                (path for path in track_dir.iterdir() if path.is_dir()),
                key=lambda path: path.name.casefold(),
            )
        )
    except OSError:
        pass
    seen: set[str] = set()
    for directory in directories:
        key = str(directory).casefold()
        if key in seen:
            continue
        seen.add(key)
        for filename in filenames:
            path = _matching_child(directory, filename, want_directory=False)
            if path is not None:
                return path
    try:
        nested = sorted(
            (
                path
                for path in track_dir.rglob("*")
                if path.is_file() and path.name.casefold() in MAP_FILENAMES
            ),
            key=lambda path: (path.name.casefold(), str(path).casefold()),
        )
    except OSError:
        nested = []
    return nested[0] if nested else None


def find_track_map_image(
    ac_root: str | None,
    track_name: str,
    layout_name: str | None = None,
) -> Path | None:
    for root in candidate_roots(ac_root):
        track_dir = _track_directory(root / "content" / "tracks", track_name)
        if track_dir is None:
            continue
        image = _track_asset_file(track_dir, MAP_FILENAMES, layout_name)
        if image is not None:
            return image
    return None


def _map_image_url(track_dir: Path, layout_name: str | None, image: Path) -> str:
    track_id = quote(track_dir.name, safe="")
    suffix = image.suffix.casefold()
    query = f"?layout={quote(layout_name, safe='')}" if layout_name else ""
    return f"/track-maps/{track_id}{suffix}{query}"


def _map_config_file(track_dir: Path, layout_name: str | None, image: Path) -> Path | None:
    layout_dir = _matching_child(track_dir, layout_name, want_directory=True) if layout_name else None
    candidates: list[Path] = []
    if layout_dir is not None:
        candidates.append(layout_dir / "data" / "map.ini")
    candidates.extend([
        image.parent / "data" / "map.ini",
        image.parent.parent / "data" / "map.ini",
        track_dir / "data" / "map.ini",
    ])
    try:
        candidates.extend(
            path for path in track_dir.rglob("map.ini") if path.is_file()
        )
    except OSError:
        pass
    seen: set[str] = set()
    for path in candidates:
        key = str(path).casefold()
        if key not in seen and path.is_file():
            seen.add(key)
            return path
    return None


def _read_map_config(path: Path | None) -> dict[str, float] | None:
    if path is None:
        return None
    values: dict[str, float] = {}
    section = ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        content = line.split(";", 1)[0].split("#", 1)[0].strip()
        if not content:
            continue
        if content.startswith("[") and content.endswith("]"):
            section = content[1:-1].strip().casefold()
            continue
        if section != "parameters" or "=" not in content:
            continue
        key, raw_value = (part.strip() for part in content.split("=", 1))
        try:
            value = float(raw_value)
        except ValueError:
            continue
        if math.isfinite(value):
            values[key.casefold()] = value
    width = values.get("width")
    height = values.get("height")
    if width is None or height is None or width <= 0 or height <= 0:
        return None
    offset_z = values.get("z_offset", values.get("y_offset", 0.0))
    return {
        "width": width,
        "height": height,
        "offset_x": values.get("x_offset", 0.0),
        "offset_z": offset_z,
        "scale_factor": values.get("scale_factor", 1.0),
    }


def _track_file(root: Path, track_name: str, layout_name: str | None = None) -> Path | None:
    track_dir = _track_directory(root / "content" / "tracks", track_name)
    return _track_ai_file(track_dir, layout_name) if track_dir is not None else None


def _downsample(points: list[list[float]]) -> list[list[float]]:
    if len(points) <= MAX_TRACK_POINTS:
        return points
    stride = math.ceil(len(points) / MAX_TRACK_POINTS)
    reduced = points[::stride]
    if reduced[-1] != points[-1]:
        reduced.append(points[-1])
    return reduced[:MAX_TRACK_POINTS]


def _read_ai_line(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("rb") as stream:
            header = stream.read(AI_HEADER.size)
            if len(header) != AI_HEADER.size:
                return None
            _version, count, _lap_time, _sample_count = AI_HEADER.unpack(header)
            if not 2 <= count <= 100_000:
                return None
            points: list[list[float]] = []
            for _ in range(count):
                raw = stream.read(AI_POINT.size)
                if len(raw) != AI_POINT.size:
                    return None
                x, y, z, _length, _node_id = AI_POINT.unpack(raw)
                if not all(math.isfinite(value) and abs(value) <= 1e6 for value in (x, y, z)):
                    return None
                points.append([round(float(x), 3), round(float(y), 3), round(float(z), 3)])
    except (OSError, struct.error):
        return None
    if math.dist(points[0], points[-1]) <= 50:
        points.append(points[0])
    return {"source": path.name, "points": _downsample(points)}


def load_track_map(ac_root: str | None, track_name: str,
                   layout_name: str | None = None) -> dict[str, Any] | None:
    """Return an AI centerline or the installed overview image for the track."""
    if not track_name:
        return None
    for root in candidate_roots(ac_root):
        track_dir = _track_directory(root / "content" / "tracks", track_name)
        if track_dir is None:
            continue
        path = _track_ai_file(track_dir, layout_name)
        if path is not None:
            result = _read_ai_line(path)
            if result is not None:
                image = _track_asset_file(track_dir, MAP_FILENAMES, layout_name)
                if image is not None:
                    result["image_url"] = _map_image_url(track_dir, layout_name, image)
                    map_config = _read_map_config(_map_config_file(track_dir, layout_name, image))
                    if map_config is not None:
                        result["map_config"] = map_config
                return result
        image = _track_asset_file(track_dir, MAP_FILENAMES, layout_name)
        if image is not None:
            map_config = _read_map_config(_map_config_file(track_dir, layout_name, image))
            result = {
                "source": image.name,
                "points": [],
                "image_url": _map_image_url(track_dir, layout_name, image),
            }
            if map_config is not None:
                result["map_config"] = map_config
            return result
    return None
