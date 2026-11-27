# Engine v2.0 candidate

Source: authorized Avoriaz public snapshot captured in run 45913169272, normalized SHA-256 1f41cd96d76c5ac30a371aa890bd6378806fd7d7340e0241e35d6fc002f86c70. Engine v1.3 and validated lobby are unchanged.

Use the new upstream code as the base (not a wholesale copy of the old resort data), with the existing reviewed geographic adaptation and bit-exact codec. The new ski/snowboard logic, camera, collision, touch UI, cloud rendering and animation remain upstream code. This is a source-level inheritance, not evidence that each feature has been individually exercised. Remove the Avoriaz-only LiDAR table indexed by its own buildings; never pretend other resorts have LiDAR building heights. Existing Avoriaz-specific scene heuristics still need visual review. New early language selection is retained, except its temporary hardcoded page title. Social-share text and personal best/onboarding keys are adapted. PBs are intentionally segregated by engine generation because the physics changed.

Before creating a WebGPU canvas, check the adapter's sampled texture limit (18 needed by existing layout). An insufficient adapter returns null to the original WebGL2 fallback. This does not make all WebGPU adapters compatible; actual WebGPU and fallback must still be tested separately.

The three-resort workflow uses existing verified IGN geographic artifacts, including Val Thorens whose previous build stopped only at the obsolete original snapshot gate. No live download of Avoriaz is required. Validate original grid equality, deterministic bundle, JS syntax, file limit, desktop and both mobile orientations. Candidate artifacts are not published or added to the validated lobby. The 90-day upstream artifact extends snapshot retention but is not a permanent source archive; keep a local backup. Source acquisition and QA inputs have finite retention and must be refreshed or archived before expiry.

Next gates: inspect actual browser reports and compare shared engine hashes, separately test ski/snowboard controls, camera and collision; then adapt shared-site extraction to the new early locale script and verify HTTP cache again. Do not equate smoke tests with complete race validation or real device performance.

## Regression checkpoint

Run 45914214557 succeeded: all nine desktop/mobile WebGL2 basic operation tests passed. Identical compiled engine SHA-256 87a47362d898bb8485bdb231199f7c93dd2f021de6cb42caa7238458cd418de3. Les Deux Alpes 7,354,708 bytes / 8 courses; Alpe d'Huez 7,435,553 bytes / 8 courses; Val Thorens 7,262,670 bytes / 7 courses after grade-review filtering. The three-resort v2 lobby workflow uses only this successful full regression source, verifies actual QA dimensions, source identity and shared engine hash, preserves the early locale script inline, and retests HTTP cache. Old v1 lobby remains unchanged. No public deployment yet.
