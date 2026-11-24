# Multi-route engineering preview v0.2

All eight OSM candidate courses are embedded and exposed through the existing timed-route picker, with eight route-head free starts. Demoiselles is explicitly flagged for grade review and cannot save a personal best. The fixed legacy coordinate frame remains Thuit 2; route navigation uses individual polylines. Grade adjustment on the other seven candidates is bounded to ±2 m; the old main-axis corridor grade overlay is disabled. No fabricated park features.

Local generated HTML: 5,118,946 bytes. Both inline JS scripts passed Node --check. Data inspection confirmed all eight names, unique IDs, difficulty and grade flags. Local Chromium file:// navigation returned ERR_BLOCKED_BY_ADMINISTRATOR before boot; route selection, completion, spawning, frame rate and mobile remain unverified. Some legacy scenery and terrain bounds still require audit. The DEM remains a single 30 m grid duplicated for compatibility, not final IGN terrain.

Reproduction, after generating v0.1 with build_preview.py:

    python scripts/expand_preview.py --preview .work/les-deux-alpes-preview.html --data .work/legacy.json --out .work/les-deux-alpes-multiroute-preview.html

Do not publish as a validated game. The authorized original template is still absent from this repository.
