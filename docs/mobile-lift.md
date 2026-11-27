# Mobile lift action — Engine v2.0.2 candidate

User report: phone controls have no way to board the lift. The pinned upstream AVZMap binds KeyE to ride()/rideEnd(true), but never mounts a touch lift control. The v2.0.1 release has the same omission.

The new context action sits below the mini-map. In touch free-ride mode it appears within the original 34 m boarding radius of a named lift with more than 20 m height gain, using the nearest eligible lower station. It is hidden away from a station, in the route menu/photo/finish states, and on non-touch devices. During an actual ride it offers Go to summit. Tap calls the existing ride/rideEnd functions, not a synthetic E key. The click re-checks live eligibility; no new physics, route or elevation data. Desktop keyboard E remains unchanged. The original nighttime direct-to-summit fallback remains. All seven existing UI languages have a concise label; no French localization is introduced.

The eight mobile lift tests across four resorts and two orientations position a player using the real lift data, require an unobscured >=44 px control, tap it, verify native lift state and summit arrival, and verify hiding away from the station and in the map. The original five browser gates also remain. Only a fully successful four-resort build can be staged for Vercel. The existing v2.0.1 production release is not overwritten while QA is running. Valloire sector only; complete race, night lift and real-device tests remain separate.

## Release checkpoint

Run 45990548083 completed successfully, including all eight mobile lift tests and four-resort HTTP cache QA. Production Vercel deployment dpl_Cf4uo75d9i7w41E3QDLRVXiur9ft is READY and the production domain points to the exact release commit 05206bdf08bcbd57f5958923af57eb3cec847d05. All 19 release files passed build integrity checks. Real mobile hardware validation remains outstanding.
