"""Receives a NDJSON from the Windows AC Bridge and write on the local spool"""
from __future__ import annotations

import asyncio
import json
import logging

from buffer import BufferFullError, PersistentBuffer
from normalizer import InvalidTelemetry, TelemetryNormalizer


LOG = logging.getLogger("telemetry-agent.receiver")
MAX_LINE_BYTES = 65_536


class TelemetryReceiver:
    def __init__(self, buffer: PersistentBuffer, *, on_data: asyncio.Event,
                 on_space: asyncio.Event):
        self.buffer = buffer
        self.normalizer = TelemetryNormalizer()
        self.on_data = on_data
        self.on_space = on_space
        self.active = False
        self.active = False
        self.accepted = 0
        self.duplicates = 0
        self.invalid = 0
        
    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamReader) -> None:
        peer = writer.get_extra_info("peername")
        if self.active:
            LOG.warning("Denied concurrency connection: %s", peer)
            writer.close()
            await writer.wait_closed()
            return
        self.active = True
        LOG.info("Windows Bridge connected: %s", peer)
        try:
            while True:
                try:
                    line = await reader.readline()
                except ValueError:
                    LOG.warning("Message beyond the bytes limit: (%d bytes)", MAX_LINE_BYTES)
                    break
                if not line:
                    break
                if len(line) > MAX_LINE_BYTES:
                    LOG.warning("Message beyond the bytes limit: (%d bytes)", MAX_LINE_BYTES)
                    break
                try:
                    message = json.loads(line)
                    event = self.normalizer.normalize(message)
                except (ValueError, TypeError, InvalidTelemetry) as exc:
                    self.invalid += 1
                    if self.invalid <= 3 or self.invalid % 100 == 0:
                        LOG.warning("Invalid sample (%d): %s", self.invalid, exc)
                    continue
                
                while True:
                    try:
                        inserted = self.buffer.append(event)
                        if inserted:
                            self.accepted += 1
                            self.on_data.set()
                        else:
                            self.duplicates += 1
                        break
                    except BufferFullError:
                        LOG.error("Full spool: waiting free space. without deleting the saved samples")
                        self.on_space.clear()
                        if self.buffer.pending < self.buffer.max_events:
                            self.on_space.set()
                        try:
                            await asyncio.wait_for(self.on_space.wait(), timeout=10)
                        except asyncio.TimeoutError:
                            pass
        except (ConnectionResetError, BrokenPipeError, OSError) as exc:
            LOG.info("Bridge connection interrupted: %s", exc)
        finally:
            self.active = False
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass
            LOG.info("Disconnected bridge, Received:%d, Tries:%d, Invalids:%d",
                     self.accepted, self.duplicates, self.invalid)
    

async def start_receiver(host: str, port: int, receiver: TelemetryReceiver) -> asyncio.Server:
    server = await asyncio.start_server(
        receiver.handle_client, host=host, port=port, limit=MAX_LINE_BYTES
    )
    LOG.info("Receiving AC bridge from %s:%s", host, port)
    return server
