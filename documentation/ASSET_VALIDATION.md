# Dash Extracted Asset Validation

## Summary

The native and Python decoders produced the same 98 relative paths, byte sizes,
and SHA-256 hashes. The GCR asset tree contains 1,818,588 bytes. The standalone
XM raises the preserved production-input total to 99 files and 2,409,938 bytes.

| Family | Count | Bytes | Validation performed |
|---|---:|---:|---|
| `.tga` textures | 63 | 1,431,903 | TGA header, dimensions, RLE packet bounds, exact end, full Pillow decode |
| `.lwo` objects | 28 | 237,970 | `FORM/LWOB`, FORM length, every padded IFF chunk boundary |
| `.lws` scenes | 4 | 33,793 | Windows-1252 text, `LWSC` version 1, original path references |
| `.prk` precalculation | 3 | 114,922 | Complete 16-bit face-packet traversal |
| Standalone `.XM` | 1 | 591,350 | FastTracker signature, version, header fields, libopenmpt decode |

## LightWave assets

All 28 `.lwo` files are big-endian IFF `FORM` files of type `LWOB`. For every
object, the FORM size equals the file size minus eight bytes and every child
chunk, including even-byte padding, ends exactly within the FORM boundary.

All four `.lws` files have the two-line LightWave scene header `LWSC`, version
`1`, use CRLF line endings, and retain `D:\vrac\...` object references.

| Scene | First frame | Last frame | Frames/s |
|---|---:|---:|---:|
| `bcruise.lws` | 960 | 1500 | 30 |
| `EcrouGreets.lws` | 1 | 60 | 30 |
| `Motion.lws` | 311 | 1038 | 30 |
| `scrollTore.lws` | 1 | 60 | 30 |

## Textures

All 63 textures are color-map-free, RLE true-color TGA images with 16-bit
stored pixels. They use the original pre-TGA-2.0 layout with no extension area
or footer. Every RLE packet accounts for exactly the declared pixel count and
ends at the file boundary. Pillow 11.3.0 fully decoded all images during this
preservation run.

| Dimensions | Count |
|---|---:|
| 64 x 64 | 4 |
| 64 x 256 | 2 |
| 70 x 25 | 6 |
| 128 x 64 | 8 |
| 128 x 128 | 10 |
| 128 x 256 | 2 |
| 130 x 90 | 1 |
| 186 x 24 | 1 |
| 210 x 210 | 2 |
| 215 x 160 | 1 |
| 222 x 25 | 1 |
| 250 x 24 | 1 |
| 256 x 32 | 2 |
| 256 x 64 | 1 |
| 256 x 128 | 3 |
| 256 x 256 | 7 |
| 287 x 160 | 2 |
| 288 x 51 | 1 |
| 292 x 25 | 1 |
| 320 x 200 | 1 |
| 355 x 240 | 2 |
| 440 x 281 | 1 |
| 480 x 480 | 2 |
| 640 x 200 | 1 |

## X3 precalculation streams

The three `.prk` files have no magic signature or self-describing header. Each
does, however, consume exactly as a sequence of little-endian 16-bit packets:
one face count followed by that many 16-bit face identifiers. This matches the
face-visibility packet concept documented and implemented by the later nXng
engine, but the complete older X3 semantics are not asserted here.

| File | Bytes | Packets | Face identifiers | Min/max faces per packet |
|---|---:|---:|---:|---:|
| `bcruise.prk` | 51,556 | 38 | 25,740 | 119 / 1,558 |
| `Ecrouland.prk` | 12,708 | 28 | 6,326 | 0 / 523 |
| `motion.prk` | 50,658 | 50 | 25,279 | 103 / 1,407 |

## Standalone soundtrack

`Dash.XM` is not inside GCR; it is preserved byte-for-byte in the expanded ZIP
tree. Its header fields are:

| Field | Value |
|---|---|
| Bytes | 591,350 |
| SHA-256 | `3255a8e7d85d2bd371c31a7607c4a039b5631e879567ca7ae3a8a605bee06809` |
| Module name | blank in header |
| Tracker | `FastTracker v2.00` |
| XM version | 1.04 |
| Song length | 54 orders |
| Restart position | 0 |
| Channels | 14 |
| Patterns | 57 |
| Instruments | 34 |
| Frequency mode | linear |
| Default tempo | 15 |
| Default BPM | 147 |

FFmpeg's libopenmpt demuxer decoded it during this preservation run and
reported an approximate duration of 204.1685 seconds. This is a decoder-level
sanity check, not a claim of sample-accurate playback parity with MIDAS 1.1.

## Reproducible checks

The regression suite verifies:

1. the source ZIP and every expanded payload against the manifest;
2. all 98 committed asset paths, sizes, and hashes;
3. each asset family's structure;
4. the standalone XM header and hash;
5. an independent Python decode of all records;
6. a fresh native extraction followed by 98 hash comparisons;
7. overwrite refusal and rejection of a truncated GCR before output exists.

Run it after building:

```powershell
ctest --test-dir build -C Release --output-on-failure
```

The authoritative file-level evidence is
[`dash-manifest.json`](dash-manifest.json).

