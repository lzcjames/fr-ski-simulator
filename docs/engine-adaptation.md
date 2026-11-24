# Engine adaptation checkpoint

The authorized uploaded Avoriaz template was audited locally, not yet committed to GitHub.

- Original `index.html`: 9,527,339 bytes; SHA-256 `4cc1a0ad2d9e1dcaebf3715adf8488aeb8be1956926e72a63fe07cffc7b97047`.
- Offline copy: 9,527,172 bytes; SHA-256 `9c2300bee3e393df0138d9ebce37272580e16a308d69b90fb3a498ec7f20f024`.
- Legacy fields: origin, P0, dir, alt0, L, meanSlope, grids, cx, hw, gy, mask, buildings, pistes, lifts, courses, segs.
- Four grids: 601×401 @ 5 m (f32), 251×241 @ 20 m (u16), 321×321 @ 60 m (u16), 381×351 @ 5 m (u16).
- Schema v2 from upstream is not a drop-in replacement. It uses east/south coordinates throughout and lacks legacy corridor arrays.
- Preserve rendering, physics, animation, audio, controls and credits. Audit mixed coordinate consumers and rebuild the legacy arrays or adapt the sampler, including starts and routes. Remove Avoriaz-specific data mutations, parks, branding, loading art and locale entries. Test each actual route and both GPU backends.
- Initial 30 m Terrarium grid is a data connectivity prototype, not final IGN near-field fidelity. Final sector, route list and layered grids require real data review.
- Upstream Skill revision: 4f64120bb085d1dc8f8978b9cb65cf7e9e92fcd1. See its data-contract and architecture references.

## Run

```sh
git clone https://github.com/awoele/ski-resort-to-game.git .work/skill
git -C .work/skill checkout --detach 4f64120bb085d1dc8f8978b9cb65cf7e9e92fcd1
python -m pip install Pillow
python scripts/prepare_resort.py --skill .work/skill --work .work/les-deux-alpes
python scripts/audit_template.py /path/to/authorized/avoriaz.html
```

The Actions workflow can also acquire and validate the data on a GitHub runner. No adapted game is claimed at this checkpoint.
