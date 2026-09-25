"""
Player consent store.

Each player must explicitly opt in before any of their clips can be included
in an API export. Consent can be scoped to specific purposes (e.g. "scouting",
"coaching") and can be revoked at any time.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"   # not yet responded


@dataclass
class ConsentRecord:
    player_id: str
    purpose: str                          # e.g. "scouting", "coaching", "broadcast"
    status: ConsentStatus
    granted_at: Optional[str] = None      # ISO-8601 UTC
    revoked_at: Optional[str] = None
    notes: str = ""


class ConsentStore:
    """
    In-memory consent store with optional JSON file persistence.

    Production deployments should swap this for a database-backed store
    and integrate with the player-facing consent UI.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        # key: (player_id, purpose)
        self._records: Dict[tuple, ConsentRecord] = {}
        self._storage_path = storage_path
        if storage_path and os.path.exists(storage_path):
            self._load(storage_path)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def grant(self, player_id: str, purpose: str, notes: str = "") -> ConsentRecord:
        """Record that a player has opted in for a given purpose."""
        record = ConsentRecord(
            player_id=player_id,
            purpose=purpose,
            status=ConsentStatus.GRANTED,
            granted_at=_now_iso(),
            revoked_at=None,
            notes=notes,
        )
        self._records[(player_id, purpose)] = record
        self._persist()
        return record

    def revoke(self, player_id: str, purpose: str) -> ConsentRecord:
        """Withdraw consent for a player/purpose pair."""
        key = (player_id, purpose)
        if key not in self._records:
            raise KeyError(f"No consent record for player={player_id} purpose={purpose}")
        record = self._records[key]
        record.status = ConsentStatus.DENIED
        record.revoked_at = _now_iso()
        self._persist()
        return record

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def has_consent(self, player_id: str, purpose: str) -> bool:
        """Return True only if the player has an active GRANTED record."""
        record = self._records.get((player_id, purpose))
        return record is not None and record.status == ConsentStatus.GRANTED

    def get(self, player_id: str, purpose: str) -> Optional[ConsentRecord]:
        return self._records.get((player_id, purpose))

    def list_for_player(self, player_id: str) -> List[ConsentRecord]:
        return [r for (pid, _), r in self._records.items() if pid == player_id]

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _persist(self) -> None:
        if not self._storage_path:
            return
        data = [asdict(r) for r in self._records.values()]
        with open(self._storage_path, "w") as fh:
            json.dump(data, fh, indent=2)

    def _load(self, path: str) -> None:
        with open(path) as fh:
            data = json.load(fh)
        for item in data:
            item["status"] = ConsentStatus(item["status"])
            r = ConsentRecord(**item)
            self._records[(r.player_id, r.purpose)] = r


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
