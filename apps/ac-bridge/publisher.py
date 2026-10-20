"""
Start the collection on windows and publush a NDJSON via TCP for WSL.
"""

from __future__ import annotations

import argparse
import json
import logging
import socket
import time
import uuid

from shared_memory import ACSharedMemory
from telemetry_reader import TelemetryReader