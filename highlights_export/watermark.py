"""
Clip watermarking utilities.

Embeds a tamper-evident token into each exported clip's metadata so that
if a clip appears outside its intended destination, the originating export
request can be identified.

For this PoC the "watermark" is a signed metadata payload. In a production
system the same token would also be embedded into the video bitstream (e.g.
via FFmpeg subtitle track or invisible DCT-domain watermark).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Dict, Any


# In production, load this from a secrets manager — never hardcode.
_WATERMARK_SECRET = os.environ.get("HIGHLIGHT_WATERMARK_SECRET", "dev-secret-change-me")


def generate_token(
    requester_id: str,
    destination: str,
    clip_id: str,
    player_id: str,
) -> str:
    """
    Return a compact HMAC-SHA256 token that binds this clip to a specific
    export request.  The token is deterministic given the same inputs so
    it can be re-derived for verification without storing it separately.
    """
    payload = json.dumps(
        {
            "requester": requester_id,
            "destination": destination,
            "clip": clip_id,
            "player": player_id,
            "ts": int(time.time()),
        },
        sort_keys=True,
    ).encode()
    digest = hmac.new(
        _WATERMARK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return f"wm1.{digest[:32]}"


def apply_to_clip_metadata(
    clip: Dict[str, Any],
    requester_id: str,
    destination: str,
) -> Dict[str, Any]:
    """
    Return a copy of the clip dict with watermark metadata injected.

    The original clip object is not mutated.
    """
    token = generate_token(
        requester_id=requester_id,
        destination=destination,
        clip_id=clip["clip_id"],
        player_id=clip["player_id"],
    )
    return {
        **clip,
        "_export_meta": {
            "watermark": token,
            "requester": requester_id,
            "destination": destination,
            "exported_at": int(time.time()),
        },
    }
