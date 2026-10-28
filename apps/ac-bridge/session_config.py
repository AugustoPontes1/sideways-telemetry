"""Read the active car and track IDs from the local AC launch configuration."""
from __future__ import annotations

import os
import re
from pathlib import Path


SECTION = re.compile(r"^\s*\[([^]]+)\]")
ENTRY = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$")
MAX_CONFIG_BYTES = 128 * 1024
PLACEHOLDER_CONTENT_IDS = frozenset({"", "-", "0", "none", "unknown"})


def _documents_roots() -> list[Path]:
    roots: list[Path] = []
    configured = os.getenv("AC_DOCUMENTS")
    if configured:
        roots.append(Path(configured).expanduser())
    for variable in ("USERPROFILE", "HOMEDRIVE"):
        value = os.getenv(variable)
        if value:
            roots.append(Path(value).expanduser())
    home_path = os.getenv("HOMEPATH")
    home_drive = os.getenv("HOMEDRIVE")
    if home_drive and home_path:
        roots.append(Path(f"{home_drive}{home_path}"))
    roots.append(Path.home())

    candidates: list[Path] = []
    for root in roots:
        if root.name.casefold() == "assetto corsa":
            candidates.append(root)
        else:
            for documents_name in ("Documents", "Documentos", "My Documents"):
                candidates.append(root / documents_name / "Assetto Corsa")
                candidates.append(root / "OneDrive" / documents_name / "Assetto Corsa")
            try:
                candidates.extend(
                    directory / documents_name / "Assetto Corsa"
                    for directory in root.glob("OneDrive*")
                    if directory.is_dir()
                    for documents_name in ("Documents", "Documentos", "My Documents")
                )
            except OSError:
                pass
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _content_id(value: str) -> str | None:
    value = value.strip().strip('"')
    if not value or value.casefold() in PLACEHOLDER_CONTENT_IDS or len(value) > 160 or value in {".", ".."}:
        return None
    if "/" in value or "\\" in value:
        return None
    return value


def _read_race_ini(path: Path) -> tuple[str | None, str | None, str | None, str | None]:
    try:
        if path.stat().st_size > MAX_CONFIG_BYTES:
            return None, None, None, None
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None, None, None, None

    section = ""
    car_id: str | None = None
    skin_id: str | None = None
    track_id: str | None = None
    layout_id: str | None = None
    for line in lines:
        section_match = SECTION.match(line)
        if section_match:
            section = section_match.group(1).casefold()
            continue
        entry_match = ENTRY.match(line.split(";", 1)[0])
        if not entry_match:
            continue
        key, value = entry_match.groups()
        normalized_key = key.casefold()
        if section == "car_0" and normalized_key == "model" and car_id is None:
            car_id = _content_id(value)
        elif section == "car_0" and normalized_key == "skin" and skin_id is None:
            skin_id = _content_id(value)
        elif section == "track":
            if normalized_key == "model" and track_id is None:
                track_id = _content_id(value)
            elif normalized_key == "config_track" and layout_id is None:
                layout_id = _content_id(value)
    return car_id, skin_id, track_id, layout_id


def load_active_content_ids() -> tuple[str | None, str | None, str | None, str | None]:
    """Return active content IDs from AC's race or entry-list configuration."""
    for root in _documents_roots():
        car_id: str | None = None
        skin_id: str | None = None
        track_id: str | None = None
        layout_id: str | None = None
        for filename in ("race.ini", "entry_list.ini"):
            values = _read_race_ini(root / "cfg" / filename)
            car_id = car_id or values[0]
            skin_id = skin_id or values[1]
            track_id = track_id or values[2]
            layout_id = layout_id or values[3]
        if car_id or skin_id or track_id:
            return car_id, skin_id, track_id, layout_id
    return None, None, None, None
