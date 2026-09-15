# Dash Asset Extraction Process

## Outcome

The original distribution was preserved unchanged, its ordinary ZIP layer was
expanded, and the demo-specific `Dash.GCR` container was reconstructed into 98
original files totaling 1,818,588 bytes. The decoded payloads are the LightWave
objects and scenes, TGA textures, and X3 visibility-precalculation data used by
the demo. The 591,350-byte FastTracker XM soundtrack was already a standalone
file in the ZIP. Together these represent 99 production assets totaling
2,409,938 bytes.

Nothing inside the recovered assets was converted, renamed, repaired,
translated, or rewritten. The historical `D:/vrac/` authoring root, filename
case, and payload bytes are retained. The drive letter is represented as the
ordinary top-level directory `D/` so extraction stays inside the repository.
`.gitattributes` marks every preservation layer as binary so Git cannot
normalize original text payloads or line endings.

## Preservation layout

| Preservation layer | Repository location |
|---|---|
| Untouched distribution | `demo-releases/1999_condense_dash(volcanic5).zip` |
| Expanded ZIP contents | `demo-unpack/1999_condense_dash(volcanic5)/` |
| Decoded GCR assets | `demo-assets/1999_condense_dash(volcanic5)/` |
| Native extractor source and build | `klx_unpack.c`, `bin/klx_unpack.exe` |
| Independent Python decoder | `tools/unpack_dash.py` |
| Shared Python LZARI implementation | `tools/unpack_klx.py` |
| Per-file provenance and hashes | `documentation/dash-manifest.json` |
| Regression checks | `tests/validate_assets.py` |

## Source artifact

The source ZIP is 1,404,833 bytes and has SHA-256:

```text
e692f7becd209810ab3ba84ba473d5a5e66355f5dddf81e1dda4c6e20cf2d110
```

Sizes and timestamps below come from the ZIP central directory. ZIP timestamps
have no timezone field and are reproduced as stored; the 2012/2013 dates show
that this distribution ZIP was assembled or normalized well after the 1999
release.

| ZIP entry | Bytes | Compressed bytes | CRC-32 | SHA-256 | ZIP timestamp |
|---|---:|---:|---|---|---|
| `Dash.exe` | 109,056 | 51,202 | `3d3bdd54` | `9fc2c84f136da8a412bfddc0ba7c110cefe7518cff3d1f598d9313447226c433` | 2012-12-27 13:25:12 |
| `Dash.GCR` | 898,364 | 897,431 | `df8076df` | `73d17c75bea94ca6596347a4ded21032464c4ae9ed01159b4e68c787331afa97` | 2012-12-27 13:25:12 |
| `DASH.TXT` | 2,467 | 1,341 | `c655fab9` | `22642718d2ab832d9b16362477d738d01d772bfd16748d3ef039e5547f8e0d7a` | 2012-12-27 13:25:12 |
| `Dash.XM` | 591,350 | 370,887 | `4c38dca2` | `3255a8e7d85d2bd371c31a7607c4a039b5631e879567ca7ae3a8a605bee06809` | 2012-12-27 13:25:12 |
| `midas11.dll` | 160,256 | 81,125 | `706a8713` | `1b9ec903edeb6e91fff67539c381c4e4d55543e61aa572ce09863c270a0a2054` | 2012-12-27 13:25:12 |
| `scene.org.txt` | 3,190 | 1,359 | `df3cbd70` | `a7eb26524568697448be7246a1ccc4249a51c168041a265e177b92d440024acf` | 2013-01-02 13:41:10 |

## Chronological reconstruction log

### 1. Reference workflow inspection

The Freestyle, LTP3 Invitation, and Couloir 14 repositories established the
desired three-layer layout, safety rules, manifest shape, independent-decoder
comparison, and structural validation. The starting `klx_unpack.c` and
`tools/unpack_klx.py` in this repository were inherited from Couloir 14 and
already contained the LZARI codec recovered during the Freestyle work.

### 2. Outer archive expansion

The ZIP directory was checked before writing files. It contains six flat,
unique names and no absolute path, traversal component, or nested archive. It
was expanded into a new directory:

```powershell
Expand-Archive `
    -LiteralPath 'demo-releases/1999_condense_dash(volcanic5).zip' `
    -DestinationPath 'demo-unpack/1999_condense_dash(volcanic5)'
```

Every expanded payload was then compared byte for byte with the corresponding
ZIP entry. Its size, CRC-32, timestamp, and SHA-256 are recorded in the
manifest.

### 3. FXLK hypothesis rejected

`Dash.GCR` does not begin with the later `FXLK` signature and has no embedded
filenames or index. Its first bytes are:

```text
33 0b 00 00 ff ff f3 13 d4 29 e5 1a 23 66 61 f5
```

The first word, `0x00000b33` (2,867), proved to be the decoded size of the first
asset rather than an entry count or signature. As with the later LTP3 external-
table container, the exact matching executable is necessary to recover names
and record boundaries.

### 4. Executable metadata-table recovery

`Dash.exe` is an unpacked PE32 image with image base `0x00400000`, entry RVA
`0x0000e550`, and PE timestamp `0x36cf092a` (1999-02-20 19:12:42 UTC). Static
strings expose the `D:/vrac/` production paths.

The file lookup routine at VA `0x00401440` walks a 98-entry table at RVA
`0x00017030` (VA `0x00417030`, raw file offset `0x00015e30`). Each 12-byte entry
contains an absolute path pointer, a compression flag, and the complete stored
record size. The loop compares filenames and advances through the third field
from VA `0x00417038` to `0x004174d0`, establishing all 98 entries independently
of the string count.

Every release entry has compression flag `1`. The sum of the 98 record sizes is
exactly 898,364 bytes, the full size of `Dash.GCR`; there are no unexplained
gaps or trailers. Full field and codec details are in
[`dash-container-format.md`](dash-container-format.md).

### 5. First proof decode

The first table record names `D:/vrac/xBaRrMask.tga`, has a stored record size
of 1,225 bytes, and begins with decoded size 2,867. The remaining 1,221 bytes
decode with the inherited LZARI implementation to a structurally valid 287 x
160, 16-bit RLE TGA image. This established the record layout and codec before
the complete extraction.

### 6. Extractor implementation and full extraction

The existing native extractor was generalized rather than replaced. Its
`--dash-exe` mode:

- requires the exact metadata executable explicitly;
- parses and bounds-checks the PE32 section table;
- maps the fixed table RVA through the PE sections;
- validates all names, flags, sizes, cumulative offsets, and path conflicts;
- decodes every payload before creating the destination;
- refuses existing destinations, unsafe paths, links, duplicate paths, and
  file/directory prefix collisions;
- preserves Windows-1252 names by converting only the host filesystem path.

The build and extraction commands were:

```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
./bin/klx_unpack.exe --list --dash-exe `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.exe' `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.GCR'
./bin/klx_unpack.exe --dash-exe `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.exe' `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.GCR' `
    'demo-assets/1999_condense_dash(volcanic5)'
```

The Windows x64 extractor was built with CMake 3.30.3, MSVC 19.41, and Windows
SDK 10.0.22621.0 using C99, `/W4 /WX`, and the static Microsoft runtime. The
checked-in binary imports only `KERNEL32.dll`; it is 163,840 bytes with SHA-256:

```text
4abff9c97ea0241d5b87867c386ee22108888afb4e56d9652222d0c3aef7ac46
```

### 7. Independent decoding and manifest

`tools/unpack_dash.py` independently parses the PE metadata table and performs
the extraction using the Python LZARI implementation. Python 3.12.5 decoded all
98 records into an ignored analysis directory. Relative paths, byte sizes, and
SHA-256 hashes were compared with the C output: all files matched and there
were zero differences.

`tools/build_manifest.py` repeats the Python decode and comparison before
writing `documentation/dash-manifest.json`. Rebuild it after a clean extraction
with:

```powershell
python tools/build_manifest.py
```

List or independently extract with Python:

```powershell
python tools/unpack_dash.py --list `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.exe' `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.GCR'
```

### 8. Structural validation

All 28 LightWave objects have complete IFF `FORM/LWOB` structures. All four
scenes are LightWave `LWSC` version 1 text files and retain their absolute
authoring references. All 63 textures are 16-bit RLE true-color TGA images;
their packet boundaries and dimensions were checked, and Pillow 11.3.0 fully
decoded every image during this preservation run.

The three `.prk` payloads consume exactly as sequences of 16-bit face-list
packets. The standalone module has a valid FastTracker XM 1.04 header and was
also decoded by FFmpeg/libopenmpt during the preservation run. See
[`ASSET_VALIDATION.md`](ASSET_VALIDATION.md) for the exact results and limits.

### 9. X3 and nXng lineage

The original `DASH.TXT` states that xBaRr/gOds lent the already-written X3
engine and that the demo's 3D scenes were produced in about a week. The
[preserved nXng repository](https://github.com/demoscene-source-archive/preservation-nxng-engine)
describes the family as LightWave-based and lists the production sequence as
Dash/X3, LTP3/X32, FreeStyle/nX, and Couloir 14/nXng. The extracted `LWOB`,
`LWSC`, TGA, and precalculation data agree with that account.

This is strong evidence that Dash preserves the earliest documented production
stage of the X3-to-nXng lineage. It does not prove that no earlier private test
or unreleased production existed.

## Evidence boundaries and remaining uncertainty

- The ZIP, executable, GCR container, standalone XM, and decoded files are
  preserved; original authoring-directory timestamps are not present in GCR.
- GCR is not self-describing. Its interpretation depends on the exact
  `Dash.exe` hash recorded above and in the manifest.
- The file lookup routine and table traversal were statically inspected, but
  the original executable was not run under emulation as a third extraction
  oracle. Confidence comes from exact size accounting, two independent
  decoders, valid payload structures, and complete hash agreement.
- `.prk` packet boundaries are validated, but their complete X3 semantics have
  not been reverse-engineered.
- The XM is preserved and structurally decoded, but no sample-accurate MIDAS
  playback parity is claimed.
- This phase recovers the production inputs. It makes no claim about modern
  DirectDraw/Direct3D playback, timing, or rendered visual parity.
