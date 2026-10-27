"""Limited SQLite Spool. Delete registries only after homelab ACK"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class BufferFullError(RuntimeError):
    """Spool limit reached and cannot remove samples silently"""


@dataclass(frozen=True, slots=True)
class BufferedItem:
    id: int
    payload: dict


class PersistentBuffer:
    def __init__(self, path: str | Path, *, max_events: int = 180_000):
        if max_events < 1:
            raise ValueError("max_events needs to be positive")
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.max_events = max_events
        self.db = sqlite3.connect(self.path, timeout=5)
        if os.name == "posix":
            os.chmod(self.path, 0o600)
        self.db.execute("PRAGMA journal_mode=WAL")
        # NORMAL preservation durability between restart of the process.
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS pending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at_ns INTEGER NOT NULL,
            UNIQUE(stream_id, sequence)
        )""")
        self.db.commit()
        self._count = int(self.db.execute("SELECT COUNT(*) FROM pending").fetchone()[0])
    
    @property
    def pending(self) -> int:
        return self._count
    
    def append(self, event: dict) -> bool:
        """Return False for a duplicate sample. Never remove new registers"""
        stream_id, sequence = event["stream_id"], event["sequence"]
        if self._count >= self.max_events:
            exists = self.db.execute(
                "SELECT 1 FROM pending WHERE stream_id=? AND sequence=?",
                (stream_id, sequence),
            ).fetchone()
            if exists:
                return False
            raise BufferFullError(f"Full buffer ({self.max_events} samples)")
        
        encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        with self.db:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO pending(stream_id, sequence, content, created_at_ns) "
                "VALUES (?, ?, ?, ?)",
                (stream_id, sequence, encoded, time.time_ns()),
            )
        inserted = cursor.rowcount == 1
        if inserted:
            self._count += 1
        return inserted
    
    def take(self, limit: int = 20) -> list[BufferedItem]:
        if not 1 <= limit <= 500:
            raise ValueError("limit needs to be between 1 and 500")
        if self._count <= limit:
            rows = self.db.execute(
                "SELECT id, content FROM pending ORDER BY id LIMIT ?", (limit,)
            ).fetchall()
        else:
            older_count = limit // 2
            recent_count = limit - older_count
            older = self.db.execute(
                "SELECT id, content FROM pending ORDER BY id LIMIT ?", (older_count,)
            ).fetchall()
            recent = self.db.execute(
                "SELECT id, content FROM pending ORDER BY id DESC LIMIT ?", (recent_count,)
            ).fetchall()
            rows = older + recent
        return [BufferedItem(id=row[0], payload=json.loads(row[1])) for row in rows]
    
    def acknowledge(self, ids: Iterable[int]) -> int:
        unique_ids = list(dict.fromkeys(ids))
        if not unique_ids:
            return 0
        if len(unique_ids) > 500 or any(type(x) is not int for x in unique_ids):
            raise ValueError("Invalid IDs")
        placeholders = ",".join("?" for _ in unique_ids)
        with self.db:
            cursor = self.db.execute(
                f"DELETE FROM pending WHERE id IN ({placeholders})", unique_ids
            )
        removed = cursor.rowcount
        self._count -= removed
        return removed
    
    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "PersistentBuffer":
        return self
    
    def __exit__(self, *_args) -> None:
        self.close()
