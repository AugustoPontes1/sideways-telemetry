"""Telemetry Agent Entrypoint on Ubuntu WSL"""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import logging
import os
from pathlib import Path

from buffer import BufferFullError, PersistentBuffer
from normalizer import InvalidTelemetry
from transport import TrasnportConfig, WebSocketTransport
from receiver import start_receiver, TelemetryReceiver

LOG = logging.getLogger("telemetry-agent")


def config_from_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Windows AC Bridge -> WSL -> Homelab")
    parser.add_argument("--listen-host", default=os.getenv("TELEMETRY_LISTEN_HOST", "127.0.0.1"))
    parser.add_argument("--listen-port", type=int, default=int(os.getenv("TELEMETRY_LISTEN_PORT", "8765")))
    parser.add_argument("--db", default=os.getenv(
        "TELEMETRY_DB", "~/.local/state/drift-telemetry/telemetry.sqlite3"))
    parser.add_argument("--max-events", type=int, default=int(os.getenv("TELEMETRY_MAX_EVENTS", "180000")))
    parser.add_argument("--upstream-url", default=os.getenv("TELEMETRY_UPSTREAM_URL"))
    parser.add_argument("--agent-id", default=os.getenv("TELEMETRY_AGENT_ID", "wsl-assetto-agent"))
    parser.add_argument("--ca-file", default=os.getenv("TELEMETRY_CA_FILE"))
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--flush-interval", type=float, default=0.2)
    parser.add_argument("--capture-only", action="store_true", help="Store data without sending to the homelab")
    parser.add_argument("--allow-insecure-dev", action="store_true", help="Allow ws:// localhost only")
    parser.add_argument("--allow-nonlocal-listen", action="store_true", help="Accept bind outside of the loopback; firewall required")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.listen_port <= 65535:
        parser.error("--listen-port needs to stay between 1 and 65535")
    if args.max_events < 1:
        parser.error("--max-events needs to be positive")
    try:
        addr = ipaddress.ip_address(args.listen_host)
        safe_localhost = addr.is_loopback
    except ValueError:
        safe_localhost = args.listen_host.lower() == "localhost"
    if not safe_localhost and not args.allow_nonlocal_listen:
        parser.error("Outside localhost requires --allow-nonlocal-listen and firewall")
    if not args.capture_only and not args.upstream_url:
        parser.error("Add TELEMETRY_UPSTREAM_URL or use --capture-only")
    return args


async def serve(args: argparse.Namespace) -> None:
    spool = PersistentBuffer(Path(args.db), max_events=args.max_events)
    data_event = asyncio.Event()
    space_event = asyncio.Event()
    receiver = TelemetryReceiver(spool, on_data=data_event, on_space=space_event)
    foward_task = None
    try:
        if not args.capture_only:
            cfg = TrasnportConfig(
                url=args.upstream_url,
                agent_id=args.agent_id,
                token=os.getenv("TELEMETRY_TOKEN"),
                ca_file=args.ca_file,
                batch_size=args.batch_size,
                flush_interval_s=args.flush_interval,
                allow_insecure_dev=args.allow_insecure_dev,
            )
            upstream = WebSocketTransport(cfg, spool, on_data=data_event, on_space=space_event)
            foward_task = asyncio.create_task(upstream.run(), name="homelab-fowarder")
        else:
            LOG.warning("CAPTURE MODE: samples only on SQLite; limit=%d", args.max_events)
        server = await start_receiver(args.listen_host, args.listen_port, receiver)
        LOG.info("Spool=%s, pending start=%d", Path(args.db).expanduser(), spool.pending)
        async with server:
            await server.serve_forever()
    finally:
        if foward_task is not None:
            foward_task.cancel()
            await asyncio.gather(foward_task, return_exceptions=True)
        spool.close()


def main() -> None:
    args = config_from_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logging.getLogger("websockets.client").setLevel(logging.INFO)
    if not args.capture_only and args.allow_insecure_dev:
        LOG.warning("Developer mode allows ws:// only for loopback")
    try:
        asyncio.run(serve(args))
    except KeyboardInterrupt:
        LOG.info("Agent finished")


if __name__ == "__main__":
    main()
