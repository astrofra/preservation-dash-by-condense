# Dash GCR External-Table Format

## Scope

Dash ships an early X3 asset container named `Dash.GCR`. Unlike the later
self-describing FXLK/KLX archives used by FreeStyle and Couloir 14, it has no
signature, internal filenames, index, timestamps, or checksums. Names, storage
methods, and record boundaries live in a table compiled into the matching
`Dash.exe`.

The observations here apply to the exact files in
`demo-unpack/1999_condense_dash(volcanic5)/`. Compatibility is not claimed for
other files that happen to use a `.GCR` extension.

## Executable metadata table

`Dash.exe` is a PE32 image with image base `0x00400000`. The table is in the
raw `.data` section:

| Property | Value |
|---|---:|
| Table RVA | `0x00017030` |
| Table VA | `0x00417030` |
| PE raw offset | `0x00015e30` |
| Entry count | 98 |
| Entry size | 12 bytes |
| Table size | 1,176 bytes |
| Table end (exclusive) | RVA `0x000174c8` |

Each entry contains three unsigned 32-bit little-endian values:

| Entry offset | Meaning |
|---:|---|
| `+0x00` | Absolute VA of a null-terminated Windows-1252 asset path |
| `+0x04` | Compression flag (`1` for all 98 release entries) |
| `+0x08` | Complete stored GCR record size, including its four-byte size prefix |

Every path begins with `D:/vrac/`. Extraction maps the drive identity to an
ordinary `D/` directory but does not alter references inside LightWave scenes.

The lookup routine at VA `0x00401440` normalizes backslashes, walks the table,
compares each name, and adds the third field to locate the matching record.
Its loop starts on the first record-size field at VA `0x00417038`, advances by
12 bytes, and stops at VA `0x004174d0`. That range independently establishes
98 entries.

## GCR record stream

Records occur in table order with no alignment padding:

| Record offset | Size | Meaning |
|---:|---:|---|
| `+0x00` | 4 | Decoded payload size, unsigned little-endian |
| `+0x04` | table record size minus 4 | Headerless LZARI payload |

For the preserved file:

| Property | Value |
|---|---:|
| GCR bytes | 898,364 |
| Records | 98 |
| Size-prefix bytes | 392 |
| Stored LZARI bytes | 897,972 |
| Decoded bytes | 1,818,588 |
| Unaccounted bytes | 0 |

The first record demonstrates the layout:

| Field | Value |
|---|---|
| Path | `D:/vrac/xBaRrMask.tga` |
| Record offset | 0 |
| Complete record size | 1,225 |
| Decoded-size prefix | 2,867 |
| LZARI bytes | 1,221 |
| Decoded result | 287 x 160, 16-bit RLE TGA |

## LZARI payload codec

The stream uses the same LZARI variant later found in LTP3 and FXLK/KLX:

- a 4,096-byte sliding window and matches from 3 to 60 bytes;
- 4,036 initial ASCII spaces followed by 60 zero bytes;
- 314 adaptive symbols, where 0-255 are literals and 256-313 encode match
  lengths as `symbol - 253`;
- arithmetic bounds `[0, 0x20000)` and a 17-bit initial code;
- bits read most-significant first;
- adaptive character frequencies initialized to one and halved at `0x7fff`;
- a fixed distance model built with
  `cumulative[i-1] = cumulative[i] + 10000 / (i + 200)`;
- the declared decoded byte count as the terminator rather than an EOF symbol.

Arithmetic termination can require limited zero-bit lookahead. Both supplied
decoders permit at most two virtual zero bytes and reject reads beyond that.

## Relationship to later containers

Dash/GCR and LTP3/data use the same broad external-table design: the executable
supplies paths, flags, and record sizes, while each compressed record supplies
its decoded size. Their table RVAs and counts differ. The later FXLK format
makes the archive self-describing by adding a header and compressed index.

This shared codec and evolving index design are technical continuity evidence
for the X3/X32/nX/nXng engine lineage, alongside the explicit production list
in the
[preserved engine repository](https://github.com/demoscene-source-archive/preservation-nxng-engine).

## Validation and safety

`klx_unpack.c` and `tools/unpack_dash.py` separately parse the PE table and
decode the records. Both enforce the exact table structure, complete byte
accounting, bounded decoded output, safe relative paths, case-insensitive
duplicate rejection, and refusal to overwrite an existing destination. Their
98 outputs agree in path, size, and SHA-256.

Because GCR has no internal checksums, `documentation/dash-manifest.json` is the
external integrity binding between the preserved ZIP, `Dash.exe`, `Dash.GCR`,
and every recovered payload.

