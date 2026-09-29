"""
Immutable audit log for highlight export operations.

Every export request — successful or rejected — writes an entry to the log.
The log is append-only so that a compliance review can reconstruct exactly
what was exported, when, by whom, and to which destination.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEvent:
    event_id: str
    timestamp: str                   # ISO-8601 UTC
    requester_id: str                # API key owner / integration ID
    destination: str                 # target system identifier (e.g. "acme-scouting-v2")
    player_ids_requested: List[str]  # what was asked for
    player_ids_exported: List[str]   # what was actually included (consent-filtered)
    player_ids_blocked: List[str]    # omitted due to missing consent
    clip_count: int
    outcome: str                     # "success" | "partial" | "denied" | "error"
    denial_reason: Optional[str] = None
    watermark_token: Optional[str] = None


class AuditLog:
    """
    Append-only audit log with optional JSONL file backend.

    Production deployments should write to an immutable store (e.g. a
    write-once S3 bucket, append-only database table, or SIEM pipeline).
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        self._events: List[AuditEvent] = []
        self._log_path = log_path

    def record(self, event: AuditEvent) -> None:
        self._events.append(event)
        if self._log_path:
            with open(self._log_path, "a") as fh:
                fh.write(json.dumps(asdict(event)) + "\n")

    def all_events(self) -> List[AuditEvent]:
        return list(self._events)

    def events_for_player(self, player_id: str) -> List[AuditEvent]:
        return [e for e in self._events if player_id in e.player_ids_exported]

    def events_for_requester(self, requester_id: str) -> List[AuditEvent]:
        return [e for e in self._events if e.requester_id == requester_id]
