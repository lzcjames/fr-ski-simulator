# Engine v1.1: nested terrain pilot

The original engine already blends three nested DEMs; the first preview supplied three copies of a single 30 m grid. The new pipeline independently samples near (10 m), mid (20 m), and far (60 m) grids, with 150/900/7500 m padding around the configured sector. All use the same projection and Terrarium zoom 13 in the pilot. This improves actual geographic coverage, not guaranteed native resolution or survey accuracy.

The optional local raster mode uses one georeferenced single-band national elevation mosaic for every layer, defaulting to 5/20/60 m. It rejects missing data rather than silently mixing sources. Supply actual IGN RGE ALTI data with appropriate licence and datum information; use rasterio. No IGN raster has yet been acquired or verified by this experiment. Official dataset: https://www.data.gouv.fr/datasets/rge-alti-r

The near grid is used to regenerate route/lift data and run upstream validation before the wider grids are added. Nested coverage and source consistency are validated separately. The existing engine handles the spatial blending; no artificial mountain is created. The workflow reuses previous real OSM artifacts (which expire after 14 days) and re-samples the DEM. Replace expired artifact IDs with new successful data runs.

    python scripts/layered_terrain.py --config resorts/les-deux-alpes/config.json --skill .work/skill --osm .work/input/osm.json --work .work/terrain

For a verified local raster add --raster /path/to/mosaic.tif --source-credit "dataset name, licence, vertical datum". The data must cover all three layers.

Browser smoke tests are not complete run validation or performance certification. Keep the confirmed 30 m Engine v1 as fallback until the new layers pass.
