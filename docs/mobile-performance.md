# Mobile performance baseline

Run two validated Engine v1.1 layered previews with the pinned upstream smoke probe in 390x844 portrait and 844x390 landscape Chromium mobile emulation. Keep original desktop QA, and use the software GPU on Linux for reproducibility. The extra performance probe samples three seconds of requestAnimationFrame cadence after the standard controls and pause/resume checks.

Collect game readiness time, frame interval median/p95, approximate rAF rate, canvas dimensions, JS heap when available, and screenshots. These are diagnostic metrics, not a claim of physical phone FPS or total memory. A real iPhone/Safari and Android hardware test is still required. No graphics-quality changes are made before measuring the baseline; do not compare different software runner jobs as rigorous A/B benchmarks.

The workflow downloads validated v1.1 artifacts; refresh the run ID when they expire. It preserves evidence even on a failed smoke test.
