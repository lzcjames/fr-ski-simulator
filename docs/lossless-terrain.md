# Lossless high-resolution terrain packaging

Engine v1.2 IGN builds passed desktop smoke tests in run 45498926509. Both use 5/20/60 m output grids. The original HTML sizes were 8,225,432 and 8,542,549 bytes.

Optional --compact-heights encodes the exact little-endian Float32 bit patterns as XOR deltas and unsigned LEB128, then Base64. Each grid uses the codec only if its encoded representation is smaller. Browser JS restores the identical byte sequence before the original renderer starts. This does not quantize heights, change route geometry, modify rendering quality or require network resources. Unit tests check exact Python/JS round trips, incompressible input, and malformed data. The bundle checker reconstructs the original data and checks script syntax.

The IGN mobile workflow uses actual IGN artifacts, compares raw and compact bytes, and tests both mobile orientations. It uses software-GPU Chrome, not physical hardware. No speedup or memory reduction is claimed until measured; decoding introduces startup work. Raw f32 packaging remains the default fallback. Previously validated uncompressed files are preserved.

Source: IGN RGE ALTI, official Géoplateforme WMS, Licence Ouverte 2.0. Nine point comparisons per grid are spot checks, not survey-accuracy certification.
