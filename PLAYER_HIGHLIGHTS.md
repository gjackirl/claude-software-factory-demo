# Player Highlights

A feature that lets coaches generate a per-player highlight reel to use during development talks and performance reviews.

## Overview

Player Highlights allows coaching staff to compile short video clips for individual players into a single reel. Reels can be reviewed together with the player to give concrete, visual feedback on recent performances and areas for growth.

## Example Use Cases

- **Mid-season development talk** – A coach prepares a reel showing a midfielder's best defensive interventions alongside moments where pressing could be sharper.
- **End-of-season review** – A striker's reel is built from goals and assists across the full campaign, giving a clear picture of attacking contribution.
- **Position-switch conversation** – A player being trialled in a new role gets a reel that highlights the specific skills relevant to that position.

## Clip Types

| Clip Type          | Description                                               |
|--------------------|-----------------------------------------------------------|
| Goals              | Shots that resulted in a goal                             |
| Assists            | Passes or actions directly leading to a goal              |
| Defensive actions  | Tackles, interceptions, blocks, and clearances            |
| Coach notes        | Tagged moments with a text or audio annotation from the coach |

## Export Options

When exporting a reel, coaches can choose to bake in any tactical drawings or markups they have added to individual clips. With this option enabled, the exported video includes all on-screen annotations at the correct timestamps — no third-party editing required.

See [TACTICAL_DRAWINGS_EXPORT.md](./TACTICAL_DRAWINGS_EXPORT.md) for the full feature spec and API reference.

## Notes

Reels are generated on demand and can be exported as a single video file or shared as a timestamped link. Access is scoped per player so athletes only see their own reel.
