"""
Sends the telemetry to the homelab with WebSocket with ACK and safely resend.

Backend contract:
- input: {type:'telemetry.batch', batch_id, agent_id, samples:[...]}
- output, AFTER it persists on the entire loot: {type:'telemetry.ack', batch_id, accepted:N}
- idempotence of each sample from key (stream_id, sequence).
"""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException

from buffer import PersistentBuffer


LOG = logging.getLogger("telemetry-agent.transport")


class InvalidAcnowledgement(RuntimeError):
    """ACK wrong, partial or referenced from other part"""


@dataclass(frozen=True)
class TrasnportConfig:
    url: str
    agent_id: str
    token: str
    ca_file: str | None = None
    batch_size: int = 20
    flush_interval_s: float = 0.20
    ack_timeout_s: float = 8.0
    allow_insecure_dev: bool = False
    
    def validate(self) -> None:
        parsed = urlsplit(self.url)
        if parsed.scheme == "wss" and parsed.hostname:
            pass
        elif (self.allow_insecure_dev and parsed.scheme == "ws"
              and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
            pass
        else:
            raise ValueError("Use wss:// for the homelab (ws:// just on loopback tests)")
        if parsed.username or parsed.password or parsed.fragment:
            raise ValueError("URL cant include credentials and fragments")
        if not self.token or not self.token.strip():
            raise ValueError("TELEMETRY_TOKEN not defined")
        if not self.agent_id or len(self.agent_id) > 100:
            raise ValueError("invalid agent_id")
        if not 1 <= self.batch_size <= 100:
            raise ValueError("batch_size beyond range 1..100")
        if not 0.01 <= self.flush_interval_s <= 10:
            raise ValueError("flush_interval_s needs to be positive")
        if self.ack_timeout_s <= 0:
            raise ValueError("ack_timeout_s needs to be positive")
        if self.ca_file is not None and not Path(self.ca_file).is_file():
            raise ValueError("CA file not found")


class WebSocketTransport:
    def __init__(self, config: TrasnportConfig, buffer: PersistentBuffer, *,
                 on_data: asyncio.Event, on_space: asyncio.Event):
        config.validate()
        self.config = config
        self.buffer = buffer
        self.on_data = on_data
        self.on_space = on_space
        self._ack_received = False
    
    def _tls_context(self) -> ssl.SSLContext | None:
        if self.config.url.startswith("ws://"):
            return None
        context = ssl.create_default_context(cafile=self.config.ca_file)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context
    
    async def _wait_for_data(self) -> None:
        self.on_data.clear()
        if self.buffer.pending:
            return
        try:
            await asyncio.wait_for(self.on_data.wait(), timeout=1)
        except asyncio.TimeoutError:
            pass
    
    @staticmethod
    def _check_ack(response: str | bytes, *, batch_id: str, count: int) -> None:
        if not isinstance(response, str):
            raise InvalidAcnowledgement("ACK needs to be text JSON")
        try:
            value = json.loads(response)
        except json.JSONDecodeError as exc:
            raise InvalidAcnowledgement("ACK not a valid JSON") from exc
        if not isinstance(value, dict):
            raise InvalidAcnowledgement("ACK needs to be a object")
        if (value.get("type") != "telemetry.ack" or
                value.get("batch_id") != batch_id or
                type(value.get("accepted")) is not int or value["accepted"] != count):
            raise InvalidAcnowledgement("ACK diverges, partial or outside of the sequence")
    
    async def _serve_connection(self) -> None:
        cfg = self.config
        async with connect(
            cfg.url,
            ssl=self._tls_context(),
            additional_headers={"Authorization": f"Bearer {cfg.token}"},
            open_timeout=8,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20,
            max_size=4096,
            compression=None,
            proxy=None,
        ) as websocket:
            LOG.info("Connected to the homelab: %s", cfg.url)
            while True:
                if self.buffer.pending == 0:
                    await self._wait_for_data()
                    continue
                # Small interval to group the samples and reduce overhead
                await asyncio.sleep(cfg.flush_interval_s)
                batch = self.buffer.take(cfg.batch_size)
                if not batch:
                    continue
                batch_id = str(uuid.uuid4())
                request = {
                    "type": "telemetry.batch",
                    "schema_version": 1,
                    "batch_id": batch_id,
                    "agent_id": cfg.agent_id,
                    "samples": [item.payload for item in batch],
                }
                serialized = json.dumps(request, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                if len(serialized.encode("utf-8")) > 1_048_576:
                    raise ValueError("Loot exceeded 1 MiB; lower the batch size")
                await websocket.send(serialized)
                response = await asyncio.wait_for(websocket.recv(), timeout=cfg.ack_timeout_s)
                self._check_ack(response, batch_id=batch_id, count=len(batch))
                deleted = self.buffer.acknowledge(item.id for item in batch)
                self.on_space.set()
                self._ack_received = True
                LOG.debug("ACK %s: %d confirmed events, pending=%d",
                          batch_id, deleted, self.buffer.pending)
    
    async def run(self) -> None:
        """Trying a reconnection, without removing the ACK events without confirmation"""
        backoff = 1.0
        while True:
            try:
                # Doesnt stablish connections when theres i not data to send.
                if self.buffer.pending == 0:
                    await self._wait_for_data()
                    continue
                await self._serve_connection()
            except asyncio.CancelledError:
                raise
            except (OSError, ValueError, TimeoutError, WebSocketException,
                    InvalidAcnowledgement) as error:
                # When the loot is confirmed, restart the penalty backoff
                if self._ack_received:
                    backoff = 1.0
                    self._ack_received = False
                # Keep the spool unchanged until it receives a valid ACK
                LOG.warning("Unavailable transmission (%s: %s) new attempts in %.0f s",
                            type(error).__name__, error, backoff)
                await asyncio.sleep(backoff)
                backoff = min(30.0, backoff * 2)
