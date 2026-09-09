"""
Highlights Export Proxy — Privacy-Safe Bulk Export PoC

Provides a thin proxy layer between internal highlight storage and external
third-party scouting software. Enforces:
  - Per-player opt-in consent before any clips are included in an export
  - Metadata watermarking so every exported clip is traceable to the request
  - Immutable audit log of every export operation
"""

from .proxy import HighlightExportProxy
from .consent import ConsentStore, ConsentStatus
from .audit import AuditLog, AuditEvent

__all__ = [
    "HighlightExportProxy",
    "ConsentStore",
    "ConsentStatus",
    "AuditLog",
    "AuditEvent",
]
