"""
Read only for shared memory on Assetoir Corsa (PC/Windows)

Maps only prefixes for layouts. it doesnt need declared fields that
are not being used. Order, types and alignment needs to correspond to SDK AC.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

I32 = ctypes.c_int32
F32 = ctypes.c_float
W16 = ctypes.c_uint16 # wchar_t on windows = UTF-16 (2 bytes)


class Physics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
       ("packetId", I32),
        ("gas", F32),
        ("brake", F32),
        ("fuel", F32),
        ("gear", I32),
        ("rpms", I32),
        ("steerAngle", F32),
        ("speedKmh", F32),
        ("velocity", F32 * 3),
        ("accG", F32 * 3),
        ("wheelSlip", F32 * 4),
        ("wheelLoad", F32 * 4),
        ("wheelsPressure", F32 * 4),
        ("wheelAngularSpeed", F32 * 4),
        ("tyreWear", F32 * 4),
        ("tyreDirtyLevel", F32 * 4),
        ("tyreCoreTemperature", F32 * 4),
        ("camberRAD", F32 * 4),
        ("suspensionTravel", F32 * 4),
        ("drs", F32),
        ("tc", F32),
        ("heading", F32),
        ("pitch", F32),
        ("roll", F32),
        ("cgHeight", F32),
        ("carDamage", F32 * 5),
        ("numberOfTyresOut", I32),
        ("pitLimiterOn", I32),
        ("abs", F32),
        ("kersCharge", F32),
        ("kersInput", F32),
        ("autoShifterOn", I32),
        ("rideHeight", F32 * 2),
        ("turboBoost", F32),
        ("ballast", F32),
        ("airDensity", F32),
        ("airTemp", F32),
        ("roadTemp", F32),
        ("localAngularVel", F32 * 3),
        ("finalFF", F32),
        ("performanceMeter", F32),
        ("engineBrake", I32),
        ("ersRecoveryLevel", I32),
        ("ersPowerLevel", I32),
        ("ersHeatCharging", I32),
        ("ersIsCharging", I32),
        ("kersCurrentKJ", F32),
        ("drsAvailable", I32),
        ("drsEnabled", I32),
        ("brakeTemp", F32 * 4),
        ("clutch", F32),
    ]


class Graphics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", I32),
        ("status", I32),
        ("session", I32),
        ("currentTime", W16 * 15),
        ("lastTime", W16 * 15),
        ("bestTime", W16 * 15),
        ("split", W16 * 15),
        ("completedLaps", I32),
        ("position", I32),
        ("iCurrentTime", I32),
        ("iLastTime", I32),
        ("iBestTime", I32),
        ("sessionTimeLeft", F32),
        ("distanceTraveled", F32),
        ("isInPit", I32),
        ("currentSectorIndex", I32),
        ("lastSectorTime", I32),
        ("numberOfLaps", I32),
        ("tyreCompound", W16 * 33),
        ("replayTimeMultiplier", F32),
        ("normalizedCarPosition", F32),
        ("carCoordinates", F32 * 3),
    ]


class Static(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion", W16 * 15),
        ("acVersion", W16 * 15),
        ("numberOfSessions", I32),
        ("numCars", I32),
        ("carModel", W16 * 33),
        ("track", W16 * 33),
    ]

def utf16_text(value: ctypes.Array) -> str:
    """ Decodify wchar_t[] of SDK (dont use c_wchar on Linux: 4 bytes)."""
    return bytes(value).decode("utf-16-le", errors="replace").split("\x00", 1)[0]


class NamedPage:
    FILE_MAP_READ = 0x0004
    
    def __init__(self, names: tuple[str, ...], layout: type[ctypes.Structure]):
        if sys.platform != "win32":
            raise RuntimeError("The read memory AC needs python running on Windows")

        self._api = ctypes.WinDLL("kernel32", use_last_error=True)
        self._api.OpenFileMappingW.restype = wintypes.HANDLE
        self._api.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                            wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
        self._api.MapViewOfFile.restype = ctypes.c_void_p
        self._api.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self._api.CloseHandle.argtypes = [wintypes.HANDLE]
        self._api.CloseHandle.restype = wintypes.BOOL
        
        self.layout = layout
        self._handle = None
        self._address = None
        for name in names:
            handle = self._api.OpenFileMappingW(self.FILE_MAP_READ, False, name)
            if handle:
                address = self._api.MapViewOfFile(
                    handle, self.FILE_MAP_READ, 0, 0, ctypes.sizeof(layout)
                )
                if not address:
                    error = ctypes.get_last_error()
                    self._api.CloseHandle(handle)
                    raise OSError(error, f"Not possible to map {name}")
                self._handle, self._address = handle, address
                break
        if self._address is None:
            raise FileNotFoundError(f"Share AC memory not available")
    
    def read(self):
        if self._address is None:
            raise RuntimeError("Attempt read page of closed memory")
        
        # Copy avoids keeping ctypes objects pointing to mutable from the games memory
        return self.layout.from_buffer_copy(
            ctypes.string_at(self._address, ctypes.sizeof(self.layout))
        )
    
    def close(self) -> None:
        if self._address is not None:
            self._api.UnmapViewOfFile(self._address)
            self._address = None
        if self._handle is not None:
            self._api.CloseHandle(self._handle)
            self._handle = None


class ACSharedMemory:
    """
    Manage pages and return snapshots without mutable references
    """
    
    def __init__(self):
        self._pages: dict[str, NamedPage] = {}
        try:
            self._pages["physics"] = NamedPage((r"Local\acpmf_physics", "acpmf_physics"), Physics)
            self._pages["graphics"] = NamedPage((r"Local\acpmf_graphics", "acpmf_graphics"), Graphics)
            self._pages["static"] = NamedPage((r"Local\acpmf_static", "acpmf_static"), Static)
        except Exception:
            self.close()
            raise
    
    def read(self) -> tuple[Physics, Graphics] | None:
        """
        Read of best effort. Discard frames if physics packetId changed during the gameplay
        """

        for _ in range(3):
            p = self._pages["physics"].read()
            g = self._pages["graphics"].read()
            if p.packetId == self._pages["physics"].read().packetId:
                return p, g
        return None
    
    def read_static(self) -> Static:
        return self._pages["static"].read()
    
    def close(self) -> None:
        for page in self._pages.values():
            page.close()
        self._pages.clear()
    
    def __enter__(self) -> "ACSharedMemory":
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()