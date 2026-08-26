# Tactical Drawings Export

Feature spec for exporting highlight clips with coach-created tactical drawings and markups baked in.

## Problem

Coaches annotate clips in real time using on-screen drawing tools — arrows, circles, lines, player paths — to highlight tactical moments. When a clip is downloaded today, those drawings are discarded. Coaches must re-create the annotations manually in third-party tools (iMovie, Hudl, etc.) before sharing with players or agents, adding friction and reducing the quality of feedback sessions.

**Community demand:** 275 votes on the Veo Ideas Board (idea #29).

## Goal

Allow a coach to export a highlight clip — or a full Player Highlights reel — as a video file that permanently includes any drawings and markups they created, without requiring external editing tools.

## How It Works

### Drawing Layer

When a coach draws on a clip, annotations are stored as a time-stamped overlay layer attached to that clip:

```
Clip
 └── AnnotationLayer[]
      ├── timestamp_ms: number       // when in the clip the drawing appears
      ├── duration_ms: number        // how long it stays on screen
      ├── shapes: Shape[]            // vector shapes (arrows, circles, freehand)
      └── fade_out: boolean          // whether it fades smoothly or cuts
```

### Export Pipeline

On export, the server renders a composite video by merging the raw clip with its annotation layer using frame-accurate compositing:

```
Raw clip (H.264/H.265)
        +
Annotation layer (SVG → PNG frames @ clip FPS)
        ↓
  FFmpeg overlay filter
        ↓
  Output MP4 (H.264, AAC, web-compatible)
```

### Export Options

| Option | Description | Default |
|---|---|---|
| `include_drawings` | Bake annotation layer into output | `true` |
| `drawing_opacity` | Opacity of annotations (0–100) | `85` |
| `fade_duration_ms` | Fade-out time for each annotation | `400` |
| `output_format` | `mp4` \| `mov` | `mp4` |
| `resolution` | `720p` \| `1080p` \| `original` | `original` |

### API Example

```http
POST /api/v1/clips/{clip_id}/export
Content-Type: application/json

{
  "include_drawings": true,
  "drawing_opacity": 85,
  "output_format": "mp4",
  "resolution": "1080p"
}
```

Response:

```json
{
  "export_id": "exp_abc123",
  "status": "processing",
  "estimated_seconds": 30,
  "download_url": null
}
```

Poll `GET /api/v1/exports/{export_id}` until `status` is `"ready"`, then fetch `download_url`.

### Player Highlights Reel Integration

When exporting a full reel via the existing Player Highlights flow, the `include_drawings` flag propagates to each clip in the reel:

```http
POST /api/v1/reels/{reel_id}/export
Content-Type: application/json

{
  "include_drawings": true,
  "drawing_opacity": 85,
  "output_format": "mp4"
}
```

Clips without annotations are passed through unchanged, so there is no quality penalty.

## Edge Cases

| Scenario | Behaviour |
|---|---|
| Clip has no annotations | Exported as-is, no overlay step |
| Annotation layer corrupt/missing | Export succeeds without drawings; warning logged |
| Very long reel (>60 clips) | Async job; user notified by email/in-app when ready |
| Coach edits drawings after export | Original export is unchanged; re-export needed |

## Acceptance Criteria

- [ ] Exported MP4 includes all on-screen drawings visible at the correct timestamps
- [ ] Annotations respect opacity and fade settings
- [ ] Clips with no drawings export identically to today's behaviour
- [ ] Export job status is queryable and returns a direct download URL when ready
- [ ] Full reel export supports `include_drawings` flag
- [ ] Export UI shows a "Include drawings" toggle, defaulting to on

## Dependencies

- FFmpeg >= 6.0 (overlay filter with alpha compositing)
- Annotation storage schema migration (add `AnnotationLayer` table)
- Export job queue (existing async infra can be reused)
