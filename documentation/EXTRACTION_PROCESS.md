# Couloir 14 Asset Extraction Process

## Outcome

The untouched distribution ZIP was expanded, and all three embedded FXLK/KLX
containers were decoded into 1,476 original files totaling 2,393,797 bytes.
The result includes the LightWave authoring assets, textures, generated
lightmaps, animation and sequencing data, and both UV-set variants used by the
demo. The MP3 soundtrack was already standalone in the distribution and did
not require container decoding.

Nothing was converted, renamed, repaired, translated, or rewritten. Historical
virtual roots (`T/`, `C/`, and `D/`), filename case, Windows-1252 spelling, and
payload bytes are retained. `.gitattributes` marks every preservation layer as
binary so Git cannot normalize old text assets or line endings.

## Preservation layout

| Layer | Repository location |
|---|---|
| Untouched distribution | `demo-releases/x+rr+f_couloir14.zip` |
| Expanded ZIP | `demo-unpack/x+rr+f_couloir14/` |
| Main decoded production assets | `demo-assets/x+rr+f_couloir14/14/` |
| First lightmap/UV variant | `demo-assets/x+rr+f_couloir14/14_0/` |
| Second lightmap/UV variant | `demo-assets/x+rr+f_couloir14/14_1/` |
| Native extractor | `klx_unpack.c`, `bin/klx_unpack.exe` |
| Independent decoder | `tools/unpack_klx.py` |
| Provenance manifest | `documentation/couloir14-manifest.json` |
| Regression checks | `tests/validate_assets.py` |

## Source artifact

The source ZIP is 3,805,862 bytes with SHA-256:

```text
d0650a68859cf5894004072c96a34ccd52a647f865e83038c15ff8bfffbf9338
```

Its eight entries are recorded below. Timestamps are reproduced from the ZIP
central directory and have no timezone field.

| ZIP entry | Bytes | Compressed | CRC-32 | SHA-256 | ZIP timestamp |
|---|---:|---:|---|---|---|
| `14_0.KLX` | 96,373 | 33,162 | `309099af` | `9744dd702e0337206e0bee5711c15707b141b20b9c31a3155f3e74d0714a99c2` | 2001-07-05 02:07:58 |
| `14.KLX` | 1,585,929 | 1,575,687 | `250f186f` | `5e4a541e682368c6e69f8cfc2b236e444682ceb7893f98a9ed5d2db8a5c9009d` | 2001-07-07 06:23:12 |
| `14.MP3` | 1,920,232 | 1,889,747 | `54b84184` | `91483f7fe1f0880bcf6671b1f3bb03445c2831806338df7555dc885af49d2c66` | 2001-07-03 10:27:10 |
| `14.TXT` | 182 | 154 | `5633c60d` | `69ca375a91e57e6fe381ad3721a847c41a67183f950393807d1f527225156e2a` | 2001-07-07 06:03:00 |
| `14.EXE` | 507,904 | 136,687 | `e1984c75` | `e9aa025290f94a3b33e2c803ab4adbf289390af361ae41367a18e3a69a8b4710` | 2001-07-07 06:28:02 |
| `14_1.KLX` | 178,517 | 77,153 | `d8584526` | `48dd2a84f1c4e06a5ff7da5618edca34b7379edaf72d6a54d0922e538f8af5ca` | 2001-07-03 23:02:22 |
| `Bass.dll` | 93,208 | 91,180 | `5f5fbf9b` | `8314aa458e4858f08eab96c2925d3d1aae983be807b6528c756b22d1de92f02e` | 1999-03-14 16:16:12 |
| `scene.org` | 1,989 | 845 | `5c7fc926` | `f29eafccf3b4a32c456d003089c1b43e8fc94216cfed97f69970eb8b04bf52fa` | 2001-07-09 14:26:56 |

## Reconstruction log

### 1. Reference comparison

The Freestyle and LTP3 Invitation repositories established the three-layer
layout, safety rules, manifest shape, independent-decoder check, and structural
asset validation. Couloir 14 already contained the extended native extractor
from the LTP3 work; its ordinary FXLK mode is the path used here.

The nXng source archive describes the engine as LightWave-based and lists
Couloir 14 as an nXng production. This is consistent with the recovered `LWOB`,
`LWSC`, MOA, envelope, motion, and sequence data.

### 2. Outer ZIP expansion

The ZIP directory was inspected for absolute paths, traversal components,
duplicates, and nested archives before expansion. It was then expanded into a
new directory:

```powershell
Expand-Archive -LiteralPath demo-releases/x+rr+f_couloir14.zip `
    -DestinationPath demo-unpack/x+rr+f_couloir14
```

All eight expanded payloads were compared byte for byte with data read directly
through the ZIP directory. Their sizes, CRC-32 values, timestamps, and SHA-256
hashes are captured in the manifest.

### 3. Container identification

The three `.KLX` files begin with `46 58 4c 4b` (`FXLK`). Each compressed index
decoded cleanly and accounted for every archive byte. No executable metadata
or heuristic boundary recovery was necessary.

| Archive | Entries | Decoded bytes | Storage methods |
|---|---:|---:|---|
| `14.KLX` | 214 | 1,965,654 | 213 LZARI, 1 XOR-9A |
| `14_0.KLX` | 481 | 157,805 | 481 LZARI |
| `14_1.KLX` | 781 | 270,338 | 781 LZARI |
| **Total** | **1,476** | **2,393,797** | **1,475 LZARI, 1 XOR-9A** |

The main index does not collide with either auxiliary index. The two auxiliary
indexes share 33 names, however, and their `UVset` files differ. They were
therefore decoded into separate `14_0/` and `14_1/` trees.

### 4. Native extraction

```powershell
./bin/klx_unpack.exe demo-unpack/x+rr+f_couloir14/14.KLX `
    demo-assets/x+rr+f_couloir14/14
./bin/klx_unpack.exe demo-unpack/x+rr+f_couloir14/14_0.KLX `
    demo-assets/x+rr+f_couloir14/14_0
./bin/klx_unpack.exe demo-unpack/x+rr+f_couloir14/14_1.KLX `
    demo-assets/x+rr+f_couloir14/14_1
```

The extractor requires a new destination, validates the complete index and all
paths, and decodes every payload in memory before creating output files.

The checked-in Windows x64 extractor was rebuilt with CMake 3.30.3, MSVC
19.41, and Windows SDK 10.0.22621.0. It is 163,328 bytes with SHA-256:

```text
cffa377d6d0be721d9c6fff688f8c6cd2eaf5b1f4979ceef4ca4cde458c10629
```

### 5. Independent decoding and manifest

`tools/unpack_klx.py` separately implements the index parser, XOR storage, and
LZARI decoder in Python. `tools/build_manifest.py` decoded all 1,476 payloads
again and compared their bytes with the native extractor output before writing
`couloir14-manifest.json`.

Rebuild the manifest after a clean extraction with:

```powershell
python tools/build_manifest.py
```

### 6. Structural checks

All 100 LightWave objects have consistent IFF `FORM/LWOB` structures. All 32
scenes have the LightWave `LWSC` version 1 header. Every one of the 1,319 JPEG
files has valid marker boundaries and dimensions; Pillow 11.3.0 also fully
decoded all of them during this preservation run. MOA, motion, envelope,
sequence, MP3, and UV-set signatures were checked without altering the files.

The full regression suite performs source and payload hash checks, ZIP-to-disk
comparisons, independent Python decoding, fresh native extraction, collision
checks, overwrite refusal, and rejection of a truncated archive before output
is created:

```powershell
ctest --test-dir build -C Release --output-on-failure
```

## Evidence boundaries

- The distribution ZIP, expanded release, and decoded asset trees are
  preserved. Original authoring filesystem timestamps are not present in KLX.
- The KLX format has no internal checksum; the external SHA-256 manifest binds
  this extraction to the exact preserved bytes.
- `14.MP3` is preserved as distributed. The validation records its container
  and stream metadata but does not claim a listening test or PCM-level parity.
- MOA3, MOA4, SPL, and `2PML` UV data are signature-checked and preserved; their
  full semantics were not reverse-engineered in this extraction phase.
- No claim is made here about modern playback, DirectX rendering, timing, or
  visual fidelity. This phase recovers and verifies the production inputs.
