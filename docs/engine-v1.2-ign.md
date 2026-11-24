# Engine v1.2: IGN numeric WMS pilot

The validated 10/20/60 m Terrarium build stays the fallback. This pilot requests bounded GeoTIFFs of IGN RGE ALTI from the official Géoplateforme WMS, at 5/20/60 m output spacing. These are requested sample spacings, not proof of native survey resolution. RGE ALTI uses heterogeneous source acquisitions.

- Service documentation: https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/diffusion/wms-raster/
- Dataset / open licence: https://www.data.gouv.fr/datasets/rge-alti-r
- Layer: ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES; EPSG:2154; image/geotiff; normal style.
- Reject non-numeric, RGB, malformed, mismatched CRS/bounds/size, missing data and implausible heights.
- Compare nine points per layer against the IGN altitude API resource ign_rge_alti_wld; record differences and fail on thresholds. No silent Terrarium substitution.
- Retain raw raster hashes, request parameters, point comparison and attribution; recompute routes using near terrain before packaging.
- This tests real numeric WMS availability. It is not a verified native IGN raster release until live results pass. A failed WMS run leaves the previously successful v1.1 unchanged.

Local usage: install rasterio and Pillow, use the pinned Skill and matching OSM artifact, then run:

    python scripts/layered_terrain.py --config resorts/les-deux-alpes/config.json --skill .work/skill --osm .work/input/osm.json --work .work/ign --ign-wms

The runner validates both resorts separately. Original downloaded raster files are included in the short-lived artifact for reproducibility, not committed to the repository.
