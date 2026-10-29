"""Transactional batch persistence with deduplication and ACK only after commit."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from sessions.models import DrivingSession
from telemetry.models import TelemetrySample
from telemetry.validators import InvalidBatch, ValidatedBatch, ValidatedSample


@dataclass(frozen=True)
class PersistResult:
    acknowledged: int
    inserted: int
    live_updates: list[dict[str, Any]]


def sample_to_model(session: DrivingSession, item: ValidatedSample) -> TelemetrySample:
    f = item.frame
    return TelemetrySample(
        session=session,
        sequence=item.sequence,
        sampled_at=item.sampled_at,
        received_at=item.received_at,
        physics_packet_id=f["physics_packet_id"],
        graphics_packet_id=f["graphics_packet_id"],
        completed_laps=f["completed_laps"],
        speed_kmh=f["speed_kmh"],
        speed_mps=f["speed_mps"],
        rpm=f["rpm"],
        gear=f["gear"],
        throttle=f["throttle"],
        brake=f["brake"],
        clutch=f["clutch"],
        steer_angle_rad=f["steer_angle_rad"],
        heading_rad=f["heading_rad"],
        pitch_rad=f["pitch_rad"],
        roll_rad=f["roll_rad"],
        position_world_m=f["position_world_m"],
        velocity_world_mps=f["velocity_world_mps"],
        acceleration_g=f["acceleration_g"],
        angular_velocity_local_rad_s=f["angular_velocity_local_rad_s"],
        wheel_slip_raw=f["wheel_slip_raw"],
        payload=f,
        frame_hash=item.frame_hash,
    )


def persist_batch(batch: ValidatedBatch) -> PersistResult:
    """Ensure idempotency for (stream, sequence) and verify content on conflicts.

    The transaction covers the ENTIRE batch, including batches with multiple streams.
    Serializa gravadores por stream via select_for_update (PostgreSQL).
    """
    grouped: dict[Any, list[ValidatedSample]] = defaultdict(list)
    for item in batch.samples:
        grouped[item.stream_id].append(item)
    inserted_count = 0
    live_updates: list[dict[str, Any]] = []

    with transaction.atomic():
        # Stable ordering prevents lock inversion across multi-stream batches.
        for stream_id, group in sorted(grouped.items(), key=lambda pair: pair[0].hex):
            newest = max(group, key=lambda item: item.sequence)
            oldest_time = min(item.sampled_at for item in group)
            newest_time = max(item.sampled_at for item in group)
            first = min(group, key=lambda item: item.sequence)
            session, _ = DrivingSession.objects.get_or_create(
                stream_id=stream_id,
                defaults={
                    "agent_id": batch.agent_id,
                    "car": first.frame["car"],
                    "track": first.frame["track"],
                    "track_map": first.frame.get("track_map", {}),
                    "car_visual": first.frame.get("car_visual", {}),
                    "session_type": first.frame["session_type"],
                    "first_sample_at": oldest_time,
                    "last_sample_at": newest_time,
                    "max_sequence": newest.sequence,
                },
            )
            session = DrivingSession.objects.select_for_update().get(pk=session.pk)
            if session.agent_id != batch.agent_id:
                raise InvalidBatch("stream_id já pertence a outro agente")
            keys = [item.sequence for item in group]
            existing = dict(TelemetrySample.objects.filter(
                session=session, sequence__in=keys
            ).values_list("sequence", "frame_hash"))
            unique_new: dict[int, ValidatedSample] = {}
            for item in group:
                stored_hash = existing.get(item.sequence)
                if stored_hash is not None and stored_hash != item.frame_hash:
                    raise InvalidBatch("Reenvio com mesmo stream/sequence e telemetria divergente")
                if stored_hash is None:
                    unique_new.setdefault(item.sequence, item)

            if unique_new:
                TelemetrySample.objects.bulk_create(
                    [sample_to_model(session, item) for item in unique_new.values()]
                )
                inserted_count += len(unique_new)
                # Publish only newly inserted samples, in batches, preserving every
                # sample for 2D/3D interpolation at ~50 Hz in the frontend.
                live_samples = []
                for new in sorted(unique_new.values(), key=lambda item: item.sequence):
                    f = new.frame
                    live_samples.append({
                        "sequence": new.sequence,
                        "timestamp_unix_ns": f["timestamp_unix_ns"],
                        "speed_kmh": f["speed_kmh"],
                        "rpm": f["rpm"],
                        "gear": f["gear"],
                        "throttle": f["throttle"],
                        "brake": f["brake"],
                        "clutch": f["clutch"],
                        "steer_angle_rad": f["steer_angle_rad"],
                        "heading_rad": f["heading_rad"],
                        "pitch_rad": f["pitch_rad"],
                        "roll_rad": f["roll_rad"],
                        "position_world_m": f["position_world_m"],
                        "velocity_world_mps": f["velocity_world_mps"],
                        "car_damage": f["car_damage"],
                    })
                live_updates.append({
                    "type": "telemetry.samples",
                    "stream_id": str(stream_id),
                    "samples": live_samples,
                })

            map_frame = next((item.frame for item in sorted(group, key=lambda item: item.sequence)
                              if item.frame.get("track_map") is not None), None)
            if map_frame is not None:
                session.track_map = map_frame["track_map"]
            visual_frame = next((item.frame for item in sorted(group, key=lambda item: item.sequence)
                                 if item.frame.get("car_visual") is not None), None)
            if visual_frame is not None:
                session.car_visual = visual_frame["car_visual"]

            session.first_sample_at = min(session.first_sample_at, oldest_time)
            session.last_sample_at = max(session.last_sample_at, newest_time)
            session.sample_count += len(unique_new)
            if newest.sequence >= session.max_sequence:
                session.max_sequence = newest.sequence
                session.car = newest.frame["car"]
                session.track = newest.frame["track"]
                session.session_type = newest.frame["session_type"]
            session.updated_at = timezone.now()
            session.save(update_fields=[
                "first_sample_at", "last_sample_at", "sample_count", "max_sequence",
                "car", "track", "track_map", "car_visual", "session_type", "updated_at",
            ])

    # Outside the transaction: all records have been committed by the database.
    return PersistResult(acknowledged=len(batch.samples), inserted=inserted_count,
                         live_updates=live_updates)
