# Alpe d'Huez: second-resort integration

Candidate scope: Signal, Les Jeux and the resort village, not the whole Grand Domaine.
The proposed bounds are W/S/E/N 6.049,45.084,6.091,45.113 (approximately 3.3 × 3.2 km).
Coordinates are a development choice, not an official boundary. References:
- https://www.alpedhuez.com/en/activities/maps/
- https://www.alpes-isere.com/sit/webcam-du-signal-alpe-dhuez-7180061/
- https://www.alpes-isere.com/sit/espace-alpe-dhuez-193788/
- https://www.alpes-isere.com/sit/alpe-dhuez-134483/

The existing shared generator selects a compatible descending reference route automatically.
Grade-review routes are excluded. 30 m Terrarium sampling is an initial test, not final IGN terrain.

The integration workflow invokes the same generic generator as Les Deux Alpes. Real OSM and DEM
artifacts are uploaded before resolving the template, so data is preserved if template or QA fails.
For the engine, a committed template is preferred. Otherwise the workflow downloads the public
authorized Avoriaz page, removes only the previously identified analytics script, and requires
the exact SHA-256 of the uploaded cleaned snapshot. A changed page causes a hard failure, not an
unreviewed engine update. No external script is executed before verification.

A successful data or HTML build is not proof of gameplay. Browser smoke results and individual
route completion, scenery, terrain boundaries and mobile validation remain separate requirements.
