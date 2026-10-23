"""Execute com pytest-django + Django/Channels instalados no WSL/homelab."""
import copy
import uuid

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings

from config.asgi import application
from sessions.models import DrivingSession
from telemetry.models import TelemetrySample
from tests.helpers import make_batch, make_sample

TOKEN = "test-only-token-with-at-least-32-characters"


async def send_ws(message, token=TOKEN):
    headers = [] if token is None else [(b"authorization", f"Bearer {token}".encode())]
    communicator = WebsocketCommunicator(application, "/ws/ingest/", headers=headers)
    connected, _ = await communicator.connect(timeout=5)
    if not connected:
        return None
    await communicator.send_json_to(message)
    result = await communicator.receive_json_from(timeout=5)
    await communicator.disconnect()
    return result


@override_settings(TELEMETRY_TOKEN=TOKEN, TELEMETRY_AGENT_ID="wsl-assetto-agent")
class BackendIntegrationTests(TransactionTestCase):
    reset_sequences = True

    def test_auth_required(self):
        assert async_to_sync(send_ws)(make_batch([make_sample()]), None) is None
        assert TelemetrySample.objects.count() == 0

    def test_ack_duplicates_and_unique_sequence(self):
        samples = [make_sample(sequence=0), make_sample(sequence=1)]
        original = make_batch(samples)
        ack1 = async_to_sync(send_ws)(original)
        assert ack1 == {
            "type": "telemetry.ack", "batch_id": original["batch_id"], "accepted": 2,
        }
        retransmission = make_batch(samples)
        ack2 = async_to_sync(send_ws)(retransmission)
        assert ack2 == {
            "type": "telemetry.ack", "batch_id": retransmission["batch_id"], "accepted": 2,
        }
        assert TelemetrySample.objects.count() == 2
        session = DrivingSession.objects.get(stream_id=samples[0]["stream_id"])
        assert session.sample_count == 2

    def test_conflicting_retransmission_does_not_overwrite(self):
        original = make_sample(sequence=0)
        assert async_to_sync(send_ws)(make_batch([original]))["type"] == "telemetry.ack"
        changed = copy.deepcopy(original)
        changed["telemetry"]["rpm"] = 9500
        response = async_to_sync(send_ws)(make_batch([changed]))
        assert response["type"] == "telemetry.error"
        assert TelemetrySample.objects.get().rpm == 4500
        assert DrivingSession.objects.get().sample_count == 1

    def test_atomic_batch_multi_stream(self):
        stream_new = uuid.UUID(int=1)
        stream_existing = uuid.UUID(int=2)
        original = make_sample(stream_id=stream_existing, sequence=0)
        assert async_to_sync(send_ws)(make_batch([original]))["type"] == "telemetry.ack"
        collision = copy.deepcopy(original)
        collision["telemetry"]["rpm"] = 11000
        first_new = make_sample(stream_id=stream_new, sequence=0)
        response = async_to_sync(send_ws)(make_batch([first_new, collision]))
        assert response["type"] == "telemetry.error"
        assert TelemetrySample.objects.count() == 1
        assert not DrivingSession.objects.filter(stream_id=stream_new).exists()

    def test_staff_only_endpoints(self):
        s = make_sample(sequence=0)
        async_to_sync(send_ws)(make_batch([s]))
        stream_id = s["stream_id"]
        response = self.client.get("/api/sessions/")
        assert response.status_code in (401, 403)
        user = get_user_model().objects.create_user(username="pilot", password="strong-password-test", is_staff=True)
        self.client.force_login(user)
        assert self.client.get("/api/sessions/").status_code == 200
        assert self.client.get(f"/api/sessions/{stream_id}/samples/").status_code == 200
        assert self.client.get(f"/api/sessions/{stream_id}/analysis/").status_code == 200
