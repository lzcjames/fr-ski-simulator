# Les Deux Alpes — Data checkpoint 2026-11-24

[Successful build #1](https://github.com/lzcjames/fr-ski-simulator/actions/runs/45467451777); [artifact](https://github.com/lzcjames/fr-ski-simulator/actions/runs/45467451777/artifacts/14956065601). Artifact retention 14 days.

Source: OSM Overpass and AWS Terrarium. 111 × 119 samples at 30 m spacing, 1090.68–2710.93 m elevation. 152 piste segments, 24 lift segments, 722 buildings, 657 street segments, 295 POIs, 12 starts, 8 selected courses, 27 candidates, no park corridors.

| Course | Difficulty (OSM) | Planar length m | Drop m | Climb m | Grade review |
|---|---|---:|---:|---:|---|
| Vallons du Diable | intermediate | 2640.3 | 683.1 | 12.6 | no |
| Jandri 1 | easy | 2351.8 | 517.0 | 15.1 | no |
| Demoiselles | novice | 1638.5 | 193.8 | 17.0 | yes |
| Petites Crêtes | novice | 1592.0 | 249.2 | 8.0 | no |
| Diable 2 | advanced | 1526.3 | 596.3 | 0 | no |
| Thuit 2 | easy | 1420.1 | 413.4 | 0 | no |
| Clot des Fonds | novice | 1322.7 | 127.2 | 1.2 | no |
| Diable 1 | advanced | 1309.5 | 601.4 | 0 | no |

These are derived lengths/drops, not official advertised figures. Geometry and grade-review flags require route-by-route review.

## Compatibility checkpoint

Locally tested on the actual downloaded data. Thuit 2 is the first legacy-axis test route: 1221 m projected axis (not the piste length), start altitude 2359.41 m, relative endpoint grade about 33.85%. Clot des Fonds and Diable 1 also pass the strict monotonic projection test. Demoiselles is rejected. Coordinate round-trip, packed arrays and unchanged real-frame layers pass.

```sh
python scripts/legacy_adapter.py --data resort-data.json --out .work/legacy.json
python tests/test_legacy_adapter.py resort-data.json
```

The adapter deliberately duplicates one coarse grid into three slots only for compatibility; it does not create larger or higher-resolution terrain. The 15 m half-width is estimated. No ready-to-play HTML, final IGN terrain, browser or mobile QA yet. Before gameplay: remove old data mutations, hard-coded resort landmarks/parks, adapt spawn selection and bounds; review grading, forest density conventions, and all course geometry. Preserve original game author credits.
