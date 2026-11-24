# Startup performance experiment

The 5/20/60 m IGN compact builds reduce raw HTML by 1,019,820 bytes (Les Deux Alpes) and 1,256,092 bytes (Alpe d'Huez), with exact Float32 restoration. Portrait emulation passed in 45505895867. This experiment preserves those inputs.

engine_performance.py creates an instrumented copy of a validated HTML. Default appearance and original device-quality governor are unchanged. Query parameters:

- frprofile=1: expose startup timestamps, quality tier, backend and texture dimensions for QA.
- frlight=1: opt into smaller far-vista (2048), city (768) and nebula (768) texture widths. Explicit existing vistares/cityres/nebres parameters still override.
- No DEM, physics, geometry or input changes. Reduced cosmetic texture quality is an explicit trade-off, not a lossless optimization.

The paired workflow runs original and light on the same Linux runner at the same resolution and initial quality tier, preserving the upstream smoke test and screenshots. Report stage durations and readiness time; one ordered pair is exploratory, not a reliable hardware benchmark. The original is run first, so possible cache/warm-up effects remain. Do not claim a real phone performance benefit or make light the default until repeated and hardware tests.

Local use: python scripts/engine_performance.py --input validated.html --out profiled.html. Open profiled.html?frprofile=1&frlight=1 to opt in. The instrumented copy is not a replacement for validated release artifacts.
