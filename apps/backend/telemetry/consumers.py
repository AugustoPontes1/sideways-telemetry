"""WebSockets: entrada de lotes autenticada por token; observação ao vivo por sessão."""
from __future__ import annotations

import hmac
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.db import DatabaseError

from sessions.models import DrivingSession
from telemetry.ingestion import persist_batch
from telemetry.validators import InvalidBatch, MAX_BATCH_BYTES, validate_batch

LOG = logging.getLogger(__name__)


def stream_group(stream_id) -> str:
    return f"telemetry.{stream_id.hex}"


class IngestConsumer(AsyncWebsocketConsumer):
    """Contrato do agent transport.py: ACK total apenas após transação confirmada."""

    async def connect(self):
        headers = [v for k, v in self.scope.get("headers", []) if k.lower() == b"authorization"]
        try:
            header = headers[0].decode("ascii") if len(headers) == 1 else ""
        except UnicodeDecodeError:
            header = ""
        prefix = "Bearer "
        received_token = header[len(prefix):] if header.startswith(prefix) else ""
        expected_token = settings.TELEMETRY_TOKEN
        if (not expected_token or not received_token or
                len(received_token) > 512 or
                not hmac.compare_digest(received_token, expected_token)):
            await self.close(code=4401)
            return
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            await self.close(code=1003)
            return
        if len(text_data.encode("utf-8")) > MAX_BATCH_BYTES:
            await self.close(code=1009)
            return
        try:
            message = json.loads(text_data)
            batch = validate_batch(message, settings.TELEMETRY_AGENT_ID)
            result = await database_sync_to_async(persist_batch)(batch)
        except (json.JSONDecodeError, InvalidBatch) as exc:
            LOG.warning("Lote de telemetria rejeitado: %s", exc)
            # Não confirmar. O cliente mantém o spool para correção/reenvio.
            await self.send(text_data=json.dumps({
                "type": "telemetry.error", "code": "invalid_batch", "reason": str(exc)[:200],
            }))
            return
        except DatabaseError:
            LOG.exception("Falha no banco ao persistir telemetria")
            await self.close(code=1011)
            return
        except Exception:
            LOG.exception("Falha inesperada na ingestão")
            await self.close(code=1011)
            return

        # Neste ponto, o commit em persist_batch() já aconteceu.
        await self.send(text_data=json.dumps({
            "type": "telemetry.ack",
            "batch_id": str(batch.batch_id),
            "accepted": result.acknowledged,  # inclui duplicatas previamente salvas
        }, separators=(",", ":")))

        # Atualização ao vivo é best-effort; falhas aqui NÃO cancelam ACK.
        for sample in result.live_updates:
            try:
                await self.channel_layer.group_send(
                    stream_group_str(sample["stream_id"]),
                    {"type": "telemetry.update", "payload": sample},
                )
            except Exception:
                LOG.exception("Publicação ao vivo falhou; dados continuam salvos")


def stream_group_str(stream_id: str) -> str:
    """Mesmo nome de grupo, a partir de UUID em texto."""
    from uuid import UUID
    return stream_group(UUID(stream_id))


class SessionLiveConsumer(AsyncWebsocketConsumer):
    """Canal read-only para usuários staff logados (cookie + Origin permitido)."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not user.is_staff:
            await self.close(code=4403)
            return
        self.stream_id = self.scope["url_route"]["kwargs"]["stream_id"]
        if not await database_sync_to_async(
            lambda: DrivingSession.objects.filter(stream_id=self.stream_id).exists()
        )():
            await self.close(code=4404)
            return
        self.group_name = stream_group(self.stream_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        # Dashboard recebe eventos, mas não pode alterar telemetria via WebSocket.
        await self.close(code=1003)

    async def telemetry_update(self, event):
        await self.send(text_data=json.dumps(event["payload"], separators=(",", ":")))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
