# Engine preview v0.1

Local integration checkpoint: Les Deux Alpes / Thuit 2. Generated HTML 5,053,221 bytes. Both inline scripts passed Node --check. Browser attempt failed before loading: net::ERR_BLOCKED_BY_ADMINISTRATOR on file://. This is not a validated playable build.

## Changes

- Insert genuine Les Deux Alpes legacy data, limit timed selection to Thuit 2, preserve engine.
- Remove Avoriaz-specific POI/street/course mutations and park routes; disable procedural park/fork additions.
- Replace start and map labels, remove old loading image, separate local PB namespace.
- Limit main corridor grade blend; no claim that residual terrain adjustments, collisions or free travel are validated.
- Coarse 30 m Terrarium only, duplicated compatibility grids, not final IGN terrain. Unknown piste difficulty segments and clipped/unnamed lifts omitted for preview. Remaining locale, scene, boundaries and spawn behavior require review.

## Reproduce

Place the authorized, cleaned offline template at engine/avoriaz-offline.html (not yet in this repo). Obtain resort-data.json from Actions build #1, then:

    python scripts/legacy_adapter.py --data resort-data.json --out .work/legacy.json
    python scripts/build_preview.py --template engine/avoriaz-offline.html --data .work/legacy.json --out .work/les-deux-alpes-preview.html

The original template must not be overwritten. Keep original credits and all relevant data attribution. No public playable release until real browser QA passes.
