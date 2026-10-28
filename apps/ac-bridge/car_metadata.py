"""Read bounded metadata for stock and externally installed AC cars."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_paths import candidate_roots

MAX_UI_JSON_BYTES = 256 * 1024


def _car_directory(root: Path, car_id: str) -> Path | None:
    cars_root = root / "content" / "cars"
    if not cars_root.is_dir():
        return None
    direct = cars_root / car_id
    if direct.is_dir():
        return direct
    wanted = car_id.casefold()
    try:
        candidates = sorted(path for path in cars_root.iterdir() if path.is_dir())
    except OSError:
        return None
    return next((path for path in candidates if path.name.casefold() == wanted), None)


def find_car_directory(ac_root: str | None, car_id: str) -> Path | None:
    """Find an installed car folder without exposing arbitrary filesystem paths."""
    if not car_id or "/" in car_id or "\\" in car_id or car_id in {".", ".."}:
        return None
    for root in candidate_roots(ac_root):
        directory = _car_directory(root, car_id)
        if directory is not None:
            return directory
    return None


def find_skin_directory(car_directory: Path, skin_id: str) -> Path | None:
    """Find the active livery folder using Assetto Corsa's case-insensitive lookup."""
    if not skin_id or "/" in skin_id or "\\" in skin_id or skin_id in {".", ".."}:
        return None
    skins_root = car_directory / "skins"
    if not skins_root.is_dir():
        return None
    direct = skins_root / skin_id
    if direct.is_dir():
        return direct
    wanted = skin_id.casefold()
    try:
        candidates = sorted(path for path in skins_root.iterdir() if path.is_dir())
    except OSError:
        return None
    return next((path for path in candidates if path.name.casefold() == wanted), None)


def find_car_directory_by_skin(ac_root: str | None, skin_id: str) -> Path | None:
    """Find a car folder when AC exposes only a skin placeholder."""
    if not skin_id:
        return None
    matches: list[Path] = []
    for root in candidate_roots(ac_root):
        cars_root = root / "content" / "cars"
        try:
            car_directories = sorted(path for path in cars_root.iterdir() if path.is_dir())
        except OSError:
            continue
        for car_directory in car_directories:
            if find_skin_directory(car_directory, skin_id) is not None:
                matches.append(car_directory)
    unique: dict[str, Path] = {str(path).casefold(): path for path in matches}
    return next(iter(unique.values())) if len(unique) == 1 else None


def find_kn5_candidates(car_directory: Path) -> list[Path]:
    """Order render meshes from highest detail to safer fallback LOD files."""
    try:
        models = sorted(path for path in car_directory.glob("*.kn5") if path.is_file())
    except OSError:
        return []
    if not models:
        return []
    folder_name = car_directory.name.casefold()
    ordered: list[Path] = []
    exact = next((path for path in models if path.stem.casefold() == folder_name), None)
    if exact is not None:
        ordered.append(exact)
    for suffix in ("_lod_a", "_lod_b", "_lod_c"):
        ordered.extend(path for path in models if path.stem.casefold().endswith(suffix))
    ordered.extend(path for path in models if path.stem.casefold() != "collider")
    return list(dict.fromkeys(ordered))


def find_top_detail_kn5(car_directory: Path) -> Path | None:
    """Choose the car's highest-detail render mesh."""
    candidates = find_kn5_candidates(car_directory)
    return candidates[0] if candidates else None


def _text(value: Any, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        return None
    return value


def _read_ui_metadata(car_directory: Path) -> tuple[str | None, str | None, bool]:
    path = car_directory / "ui" / "ui_car.json"
    try:
        if path.stat().st_size > MAX_UI_JSON_BYTES:
            return None, None, False
        with path.open("r", encoding="utf-8-sig") as stream:
            value = json.load(stream)
    except (OSError, UnicodeDecodeError, ValueError):
        return None, None, False
    if not isinstance(value, dict):
        return None, None, False
    name = _text(value.get("name"), 160)
    brand = _text(value.get("brand"), 80)
    return name, brand, True


def _has_kn5(car_directory: Path) -> bool:
    try:
        return any(path.is_file() for path in car_directory.glob("*.kn5"))
    except OSError:
        return False


def load_car_metadata(ac_root: str | None, car_id: str, skin_id: str | None = None) -> dict[str, Any] | None:
    """Return metadata for any car folder, including third-party mod folders.

    AC shared memory exposes the car identifier but not its model mesh or skin.
    The folder lookup lets the rest of the pipeline distinguish an installed
    content asset and display its user-facing name without trusting file paths.
    """
    if not car_id:
        return None
    directory = find_car_directory(ac_root, car_id)
    if directory is None:
        return None
    display_name, brand, ui_metadata = _read_ui_metadata(directory)
    skin_directory = find_skin_directory(directory, skin_id or "")
    return {
        "id": car_id,
        "display_name": display_name or car_id,
        "brand": brand or "",
        "asset_key": car_id,
        "source": "content/cars",
        "ui_metadata": ui_metadata,
        "model_format": "kn5" if _has_kn5(directory) else "",
        "skin_id": skin_directory.name if skin_directory is not None else (skin_id or ""),
    }
