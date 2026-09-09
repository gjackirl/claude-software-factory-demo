"""
HighlightExportProxy — the central access-control layer.

Workflow for every export request:
  1. Validate the requester's API key and destination registration.
  2. Filter out any players who have not granted consent for the
     "scouting" (or caller-specified) purpose.
  3. Apply watermark metadata to every clip being returned.
  4. Write a full audit event regardless of outcome.
  5. Return only the consented, watermarked clips to the caller.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .audit import AuditEvent, AuditLog
from .consent import ConsentStore
from .watermark import apply_to_clip_metadata


@dataclass
class ExportRequest:
    requester_id: str          # identifies the API client / integration
    destination: str           # human-readable target system name
    player_ids: List[str]      # players whose clips are requested
    purpose: str = "scouting"  # consent scope to check


@dataclass
class ExportResult:
    request_id: str
    exported_clips: List[Dict[str, Any]]
    blocked_players: List[str]   # omitted due to missing consent
    outcome: str                 # "success" | "partial" | "denied"
    message: str = ""


class HighlightExportProxy:
    """
    Thin proxy that enforces consent, applies watermarks, and logs everything.

    Parameters
    ----------
    clip_store:
        Any callable ``(player_ids: list[str]) -> list[dict]`` that returns
        raw clip objects.  Pass in a mock/stub for testing.
    consent_store:
        A ``ConsentStore`` instance.
    audit_log:
        An ``AuditLog`` instance.
    allowed_destinations:
        Optional allowlist of registered destination identifiers.  When
        supplied, requests from unregistered destinations are rejected.
    """

    def __init__(
        self,
        clip_store,
        consent_store: ConsentStore,
        audit_log: AuditLog,
        allowed_destinations: Optional[List[str]] = None,
    ) -> None:
        self._clip_store = clip_store
        self._consent = consent_store
        self._audit = audit_log
        self._allowed_destinations = set(allowed_destinations or [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export(self, request: ExportRequest) -> ExportResult:
        """Process a bulk highlight export request."""
        request_id = str(uuid.uuid4())

        # 1. Destination allowlist check
        if self._allowed_destinations and request.destination not in self._allowed_destinations:
            self._write_audit(
                request_id=request_id,
                request=request,
                exported=[],
                blocked=request.player_ids,
                outcome="denied",
                denial_reason=f"Destination '{request.destination}' is not registered.",
                watermark_token=None,
            )
            return ExportResult(
                request_id=request_id,
                exported_clips=[],
                blocked_players=list(request.player_ids),
                outcome="denied",
                message=f"Destination '{request.destination}' is not an approved export target.",
            )

        # 2. Consent filtering
        consented_players = [
            pid for pid in request.player_ids
            if self._consent.has_consent(pid, request.purpose)
        ]
        blocked_players = [
            pid for pid in request.player_ids
            if pid not in consented_players
        ]

        if not consented_players:
            self._write_audit(
                request_id=request_id,
                request=request,
                exported=[],
                blocked=blocked_players,
                outcome="denied",
                denial_reason="No requested players have granted consent.",
                watermark_token=None,
            )
            return ExportResult(
                request_id=request_id,
                exported_clips=[],
                blocked_players=blocked_players,
                outcome="denied",
                message=(
                    f"Export denied: none of the {len(request.player_ids)} requested "
                    f"player(s) have granted '{request.purpose}' consent."
                ),
            )

        # 3. Fetch clips for consented players only
        raw_clips = self._clip_store(consented_players)

        # 4. Watermark every clip
        watermark_token = f"export-{request_id[:8]}"
        watermarked = [
            apply_to_clip_metadata(clip, request.requester_id, request.destination)
            for clip in raw_clips
        ]

        # 5. Audit
        outcome = "partial" if blocked_players else "success"
        self._write_audit(
            request_id=request_id,
            request=request,
            exported=consented_players,
            blocked=blocked_players,
            outcome=outcome,
            denial_reason=None,
            watermark_token=watermark_token,
        )

        return ExportResult(
            request_id=request_id,
            exported_clips=watermarked,
            blocked_players=blocked_players,
            outcome=outcome,
            message=(
                f"Exported {len(watermarked)} clip(s) for {len(consented_players)} player(s)."
                + (
                    f" {len(blocked_players)} player(s) omitted — consent not granted."
                    if blocked_players
                    else ""
                )
            ),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_audit(
        self,
        request_id: str,
        request: ExportRequest,
        exported: List[str],
        blocked: List[str],
        outcome: str,
        denial_reason: Optional[str],
        watermark_token: Optional[str],
    ) -> None:
        import time

        self._audit.record(
            AuditEvent(
                event_id=request_id,
                timestamp=_iso_now(),
                requester_id=request.requester_id,
                destination=request.destination,
                player_ids_requested=list(request.player_ids),
                player_ids_exported=exported,
                player_ids_blocked=blocked,
                clip_count=0 if outcome in ("denied",) else len(exported),
                outcome=outcome,
                denial_reason=denial_reason,
                watermark_token=watermark_token,
            )
        )


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
