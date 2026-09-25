"""
Tests for the HighlightExportProxy and supporting modules.

Run with:  python -m pytest highlights_export/test_export_proxy.py -v
"""

from __future__ import annotations

import pytest
from typing import List, Dict, Any

from highlights_export import HighlightExportProxy, ConsentStore, AuditLog
from highlights_export.proxy import ExportRequest


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_clip_store(clips: List[Dict[str, Any]]):
    """Return a callable clip store that filters by player_id."""
    def _store(player_ids: List[str]) -> List[Dict[str, Any]]:
        return [c for c in clips if c["player_id"] in player_ids]
    return _store


SAMPLE_CLIPS = [
    {"clip_id": "clip-001", "player_id": "player-A", "type": "goal",    "url": "https://cdn.example.com/clip-001.mp4"},
    {"clip_id": "clip-002", "player_id": "player-A", "type": "assist",  "url": "https://cdn.example.com/clip-002.mp4"},
    {"clip_id": "clip-003", "player_id": "player-B", "type": "tackle",  "url": "https://cdn.example.com/clip-003.mp4"},
    {"clip_id": "clip-004", "player_id": "player-C", "type": "goal",    "url": "https://cdn.example.com/clip-004.mp4"},
]


def make_proxy(
    clips=None,
    consents=None,
    allowed_destinations=None,
):
    """
    Build a proxy with optional pre-seeded consent records.

    consents: list of (player_id, purpose) tuples that should be GRANTED.
    """
    store = ConsentStore()
    for pid, purpose in (consents or []):
        store.grant(pid, purpose)

    log = AuditLog()
    clip_store = make_clip_store(clips or SAMPLE_CLIPS)

    proxy = HighlightExportProxy(
        clip_store=clip_store,
        consent_store=store,
        audit_log=log,
        allowed_destinations=allowed_destinations,
    )
    return proxy, store, log


# ---------------------------------------------------------------------------
# Consent tests
# ---------------------------------------------------------------------------

class TestConsentStore:
    def test_grant_and_check(self):
        cs = ConsentStore()
        cs.grant("player-A", "scouting")
        assert cs.has_consent("player-A", "scouting") is True

    def test_missing_consent_returns_false(self):
        cs = ConsentStore()
        assert cs.has_consent("player-X", "scouting") is False

    def test_revoke_removes_consent(self):
        cs = ConsentStore()
        cs.grant("player-A", "scouting")
        cs.revoke("player-A", "scouting")
        assert cs.has_consent("player-A", "scouting") is False

    def test_consent_is_purpose_scoped(self):
        cs = ConsentStore()
        cs.grant("player-A", "coaching")
        assert cs.has_consent("player-A", "scouting") is False
        assert cs.has_consent("player-A", "coaching") is True

    def test_revoke_nonexistent_raises(self):
        cs = ConsentStore()
        with pytest.raises(KeyError):
            cs.revoke("nobody", "scouting")


# ---------------------------------------------------------------------------
# Export proxy — happy path
# ---------------------------------------------------------------------------

class TestExportProxySuccess:
    def test_full_consent_returns_all_clips(self):
        proxy, _, log = make_proxy(
            consents=[("player-A", "scouting"), ("player-B", "scouting")]
        )
        result = proxy.export(ExportRequest(
            requester_id="acme-scouting",
            destination="acme-scouting-v2",
            player_ids=["player-A", "player-B"],
        ))
        assert result.outcome == "success"
        assert result.blocked_players == []
        assert len(result.exported_clips) == 3   # 2 clips for A, 1 for B

    def test_clips_have_watermark_metadata(self):
        proxy, _, _ = make_proxy(consents=[("player-A", "scouting")])
        result = proxy.export(ExportRequest(
            requester_id="acme",
            destination="acme-scouting-v2",
            player_ids=["player-A"],
        ))
        for clip in result.exported_clips:
            assert "_export_meta" in clip
            assert clip["_export_meta"]["requester"] == "acme"
            assert clip["_export_meta"]["watermark"].startswith("wm1.")

    def test_audit_log_records_success(self):
        proxy, _, log = make_proxy(consents=[("player-A", "scouting")])
        proxy.export(ExportRequest(
            requester_id="acme",
            destination="acme-scouting-v2",
            player_ids=["player-A"],
        ))
        events = log.all_events()
        assert len(events) == 1
        assert events[0].outcome == "success"
        assert "player-A" in events[0].player_ids_exported


# ---------------------------------------------------------------------------
# Export proxy — partial consent
# ---------------------------------------------------------------------------

class TestExportProxyPartial:
    def test_only_consented_players_exported(self):
        # player-A consented, player-B has not
        proxy, _, log = make_proxy(consents=[("player-A", "scouting")])
        result = proxy.export(ExportRequest(
            requester_id="acme",
            destination="acme-scouting-v2",
            player_ids=["player-A", "player-B"],
        ))
        assert result.outcome == "partial"
        assert "player-B" in result.blocked_players
        exported_players = {c["player_id"] for c in result.exported_clips}
        assert "player-B" not in exported_players

    def test_audit_records_partial(self):
        proxy, _, log = make_proxy(consents=[("player-A", "scouting")])
        proxy.export(ExportRequest(
            requester_id="acme",
            destination="acme-scouting-v2",
            player_ids=["player-A", "player-B"],
        ))
        event = log.all_events()[0]
        assert event.outcome == "partial"
        assert "player-B" in event.player_ids_blocked


# ---------------------------------------------------------------------------
# Export proxy — denied
# ---------------------------------------------------------------------------

class TestExportProxyDenied:
    def test_no_consent_returns_denied(self):
        proxy, _, _ = make_proxy()  # no consents seeded
        result = proxy.export(ExportRequest(
            requester_id="acme",
            destination="acme-scouting-v2",
            player_ids=["player-A"],
        ))
        assert result.outcome == "denied"
        assert result.exported_clips == []

    def test_unregistered_destination_denied(self):
        proxy, _, log = make_proxy(
            consents=[("player-A", "scouting")],
            allowed_destinations=["approved-dest"],
        )
        result = proxy.export(ExportRequest(
            requester_id="acme",
            destination="rogue-destination",
            player_ids=["player-A"],
        ))
        assert result.outcome == "denied"
        assert result.exported_clips == []
        event = log.all_events()[0]
        assert "not registered" in (event.denial_reason or "")

    def test_audit_records_denial(self):
        proxy, _, log = make_proxy()
        proxy.export(ExportRequest(
            requester_id="acme",
            destination="acme-scouting-v2",
            player_ids=["player-Z"],
        ))
        event = log.all_events()[0]
        assert event.outcome == "denied"
        assert event.denial_reason is not None


# ---------------------------------------------------------------------------
# Audit log — query helpers
# ---------------------------------------------------------------------------

class TestAuditLog:
    def test_events_for_player(self):
        proxy, _, log = make_proxy(
            consents=[("player-A", "scouting"), ("player-C", "scouting")]
        )
        proxy.export(ExportRequest("req1", "dest-x", ["player-A"]))
        proxy.export(ExportRequest("req2", "dest-x", ["player-C"]))
        assert len(log.events_for_player("player-A")) == 1
        assert len(log.events_for_player("player-C")) == 1

    def test_events_for_requester(self):
        proxy, _, log = make_proxy(consents=[("player-A", "scouting")])
        proxy.export(ExportRequest("requester-1", "dest-x", ["player-A"]))
        proxy.export(ExportRequest("requester-2", "dest-x", ["player-A"]))
        assert len(log.events_for_requester("requester-1")) == 1
        assert len(log.events_for_requester("requester-2")) == 1
