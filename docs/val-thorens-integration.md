# Val Thorens candidate integration

Third resort, configured around the 2300 m village, with candidate Cascades and Plein Sud coverage. Development rectangle W/S/E/N: 6.559,45.283,6.602,45.312; origin 6.5805,45.2975. This is a proposed limited sector (roughly 3.4 x 3.2 km), not the full ski area or an official boundary. Confirm actual route completeness from downloaded OSM; clipped trails are not full timed routes.

References: https://mapcarta.com/Val_Thorens and https://www.valthorens.com/en/ski/debutants/ and https://ski.valthorens.com/en/maps-and-schedule/.

The profile deliberately leaves the primary course unset and excludes grade-review candidates. The proposed wet-snow threshold is 2100 m, a visual tuning assumption, not current snow conditions. The generic onboarding workflow fetches new OSM data, obtains three independently verified IGN 5/20/60 m output grids, builds lossless HTML, then checks desktop and both mobile orientations. No coarse DEM substitution. Failed source or route checks block promotion. It reuses the same engine, not a bespoke Val Thorens implementation.

The new resort is not automatically added to the validated two-resort lobby. Promote only after all three browser gates succeed. Full route completion, actual device performance, and visual inspection remain separate gates.

WebGPU testing is a separate strict workflow against the already validated two-resort standalone HTML. It requests WebGPU explicitly and verifies the actual backend; fallback to WebGL2 cannot pass. GitHub-hosted Chrome uses a software graphics experiment; no hardware GPU guarantee. Keep the existing WebGL2 fallback unchanged.

Promotion: after New resort IGN integration succeeds, manually run Build multi-resort lobby with the successful onboarding run ID in `onboarding_run`. It merges the two orientation artifacts without overwriting existing games. Then run Shared online engine cache with the new successful lobby run ID. The Pages publisher can accept that validated shared build. No publication is automatic.
