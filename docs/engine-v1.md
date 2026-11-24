# Engine v1 — shared template experiment

The verified Avoriaz snapshot remains the source of rendering, physics, animation, audio and UI. The old build_game.py is retained as a compatibility reference. The new engine_v1.py has two explicit stages:

1. compile: verify the original snapshot, apply the common legacy adaptation once, and emit an unplayable shared template with typed placeholders.
2. pack: adapt one resort's real data, fill the template with independent JSON metadata and geographic data, escape HTML and JS separately, and emit a standalone HTML.

The runtime reads FR_RESORT for title, map labels, snow threshold, and resort-specific PB/onboarding storage keys. General preferences stay shared. Identical terrain grids are serialized once and their original ordering is restored before the legacy engine boots; this reduces raw HTML size but does not improve terrain resolution or guarantee GPU memory savings.

The template is an intermediate build artifact, not a user-facing game. No original engine code is deleted outside the existing reviewed patch set. Unresolved or duplicate slots abort the build. This is an incremental extraction; remaining Avoriaz-specific geography and UI must be audited separately.

Commands:

    python scripts/engine_v1.py compile --template engine/avoriaz-offline.html --out .work/shared.html
    python scripts/engine_v1.py pack --engine .work/shared.html --config resorts/les-deux-alpes/config.json --data .work/data/resort-data.json --out .work/les-deux-alpes.html

Repeat only the pack step for another resort with its own validated data and profile. Browser QA, actual route completion, layered IGN terrain and device performance remain release gates.

Alpe d'Huez's first legacy generator run successfully acquired 199 piste segments, 36 lift segments, 762 buildings, 8 candidate courses and 12 starts. The verified template download and 5,193,888-byte HTML build succeeded, but the WebGL2 readiness test timed out. See https://github.com/lzcjames/fr-ski-simulator/actions/runs/45492818325. It is not a playable release.
