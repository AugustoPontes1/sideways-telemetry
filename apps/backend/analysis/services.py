"""Análise conservadora: reporta medidas e indícios, sem diagnosticar 'erro de drift'."""
from __future__ import annotations

from django.db.models import Avg, Count, Max, Min

from telemetry.models import TelemetrySample


def summarize_session(session, event_window: int = 2000) -> dict:
    qs = TelemetrySample.objects.filter(session=session)
    stats = qs.aggregate(
        count=Count("id"), speed_min_kmh=Min("speed_kmh"), speed_max_kmh=Max("speed_kmh"),
        speed_avg_kmh=Avg("speed_kmh"), rpm_min=Min("rpm"), rpm_max=Max("rpm"),
        throttle_avg=Avg("throttle"),
    )
    # A janela ordenada é intencional; a sessão completa pode ter milhões de pontos.
    latest = list(qs.order_by("-sequence")[:event_window])
    latest.reverse()
    events = detect_input_events(latest)
    return {
        "stream_id": str(session.stream_id),
        "car": session.car,
        "track": session.track,
        "stats": stats,
        "events": events,
        "event_window_samples": len(latest),
        "interpretation": (
            "Eventos são hipóteses de análise, não comprovação de erro. "
            "Sem validação dos referenciais do Assetto Corsa não calculamos ângulo de drift "
            "nem uma trajetória ideal."
        ),
    }


def detect_input_events(samples: list) -> list[dict]:
    """Derivadas discretas simples com limiares ilustrativos (calibrar em campo)."""
    events = []
    last_emitted: dict[str, float] = {}
    for previous, current in zip(samples, samples[1:]):
        dt = (current.payload["timestamp_unix_ns"] - previous.payload["timestamp_unix_ns"]) / 1e9
        if not 0.005 <= dt <= 1.0:
            continue  # pausas, saltos e amostras fora de ordem
        time_s = current.payload["timestamp_unix_ns"] / 1e9
        rates = [
            ("throttle_change", abs(current.throttle - previous.throttle) / dt, 1.5, "fração/s"),
            ("steering_change", abs(current.steer_angle_rad - previous.steer_angle_rad) / dt,
             2.0, "rad/s"),
        ]
        for kind, value, threshold, unit in rates:
            if value < threshold or time_s - last_emitted.get(kind, -1e12) < 0.5:
                continue
            events.append({
                "kind": kind, "sequence": current.sequence,
                "rate": round(value, 3), "unit": unit,
                "label": "Mudança rápida de comando; investigar com outros sinais",
            })
            last_emitted[kind] = time_s
    return events[:100]
