# Highlights Export Proxy — Privacy-Safe Bulk Export (PoC)

This module implements a privacy-safe proxy layer that sits between internal
highlight storage and external third-party scouting software, directly
addressing the L3 escalation from a multi-camera club requesting bulk API
export of player highlights.

## Problem

A multi-camera club wants to pull player highlights out via API into their own
scouting software. No supported integration path exists today, and a naive bulk
export endpoint would:

- Expose player footage without individual consent
- Provide no traceability if clips are misused
- Leave no audit trail for compliance review

## Solution Architecture

```
Club's Scouting Software
         │
         │  export_request(player_ids, destination, purpose)
         ▼
┌─────────────────────────────────┐
│      HighlightExportProxy       │
│  1. Destination allowlist check │
│  2. Per-player consent filter   │──► ConsentStore (opt-in DB)
│  3. Watermark clip metadata     │──► WatermarkEngine
│  4. Write audit event           │──► AuditLog (append-only)
│  5. Return filtered clips       │
└─────────────────────────────────┘
         │
         ▼
  Internal Clip Store
```

## Privacy Guardrails

### 1. Per-Player Consent (`consent.py`)
- Every player must explicitly opt in for a named **purpose** (e.g. `"scouting"`)
  before any of their clips are included in an API export.
- Consent is purpose-scoped: granting `"coaching"` does **not** imply `"scouting"`.
- Consent can be revoked at any time; subsequent export calls will exclude that
  player immediately.

### 2. Clip Watermarking (`watermark.py`)
- Every exported clip receives an `_export_meta` block containing an HMAC-SHA256
  token that binds the clip to the specific requester, destination, and timestamp.
- If a clip surfaces outside its intended destination, the originating export
  request can be identified from the token.
- Production extension: the same token should also be embedded in the video
  bitstream (e.g. via FFmpeg subtitle track or DCT-domain watermarking).

### 3. Immutable Audit Log (`audit.py`)
- Every export attempt — success, partial, or denied — writes an `AuditEvent`
  containing: requester, destination, requested players, exported players,
  blocked players, clip count, outcome, and denial reason.
- The log is append-only; no event is ever deleted or modified.
- Production extension: write to an immutable store (write-once S3, append-only
  DB table, or SIEM pipeline).

### 4. Destination Allowlist (`proxy.py`)
- The proxy can be configured with a set of approved destination identifiers.
- Requests from unregistered destinations are rejected and logged before any
  consent check is performed.

## Usage

```python
from highlights_export import HighlightExportProxy, ConsentStore, AuditLog
from highlights_export.proxy import ExportRequest

# Set up
consent_store = ConsentStore(storage_path="consents.json")
audit_log = AuditLog(log_path="audit.jsonl")

consent_store.grant("player-42", "scouting")  # player opted in

proxy = HighlightExportProxy(
    clip_store=my_clip_db.fetch_clips,
    consent_store=consent_store,
    audit_log=audit_log,
    allowed_destinations=["acme-scouting-v2"],
)

# Handle an export request from the club's scouting software
result = proxy.export(ExportRequest(
    requester_id="acme-scouting",
    destination="acme-scouting-v2",
    player_ids=["player-42", "player-99"],
    purpose="scouting",
))

print(result.outcome)          # "partial" — player-99 had no consent
print(result.blocked_players)  # ["player-99"]
print(result.exported_clips)   # watermarked clip dicts for player-42 only
```

## Running the Tests

```bash
python -m pytest highlights_export/test_export_proxy.py -v
```

## What's Not Included (Production TODO)

- **Video bitstream watermarking** — embed token into the actual MP4/HLS stream,
  not just metadata.
- **Player consent UI** — a web or mobile surface for players to manage their
  consent settings.
- **Rate limiting / quota** — throttle export volume per requester.
- **Encryption in transit** — TLS + short-lived signed URLs for clip delivery.
- **GDPR/right-to-erasure** — purge a player's data from the audit log on request
  (requires a separate erasure pipeline; the audit log itself must remain intact
  for legal holds).

## Related

- [`PLAYER_HIGHLIGHTS.md`](./PLAYER_HIGHLIGHTS.md) — overview of the per-player
  highlight reel feature this export proxy builds upon.
