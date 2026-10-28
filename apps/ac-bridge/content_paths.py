"""Locate an Assetto Corsa installation on the Windows bridge host."""
from __future__ import annotations

import os
import re
from pathlib import Path


def _steam_roots() -> list[Path]:
    roots: list[Path] = []
    for value in (
        os.getenv("STEAM_ROOT"),
        os.getenv("PROGRAMFILES(X86)"),
        os.getenv("PROGRAMFILES"),
        os.getenv("LOCALAPPDATA"),
    ):
        if value:
            path = Path(value)
            roots.append(path if path.name.casefold() == "steam" else path / "Steam")
    roots.extend(Path(path) for path in (
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
    ))
    return roots


def _steam_library_paths() -> list[Path]:
    libraries: list[Path] = []
    for steam_root in _steam_roots():
        vdf = steam_root / "steamapps" / "libraryfolders.vdf"
        try:
            content = vdf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw_path in re.findall(r'"path"\s+"([^"]+)"', content, flags=re.IGNORECASE):
            library = Path(raw_path.replace("\\\\", "\\"))
            if library not in libraries:
                libraries.append(library)
    return libraries


def candidate_roots(ac_root: str | None) -> list[Path]:
    roots: list[Path] = []
    if ac_root:
        roots.append(Path(ac_root).expanduser())
    env_root = os.getenv("AC_ROOT")
    if env_root and Path(env_root).expanduser() not in roots:
        roots.append(Path(env_root).expanduser())
    roots.extend(Path(path) for path in (
        r"C:\Program Files (x86)\Steam\steamapps\common\assettocorsa",
        r"C:\Program Files\Steam\steamapps\common\assettocorsa",
    ))
    roots.extend(library / "steamapps" / "common" / "assettocorsa" for library in _steam_library_paths())
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique
