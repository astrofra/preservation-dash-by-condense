# Couloir 14 KLX / FXLK Format

## Scope

Couloir 14 ships three self-describing nXng asset containers. All begin with
the ASCII signature `FXLK` and use the same index and LZARI codec reconstructed
during the FreeStyle preservation effort. Unlike the earlier LTP3 Invitation
container, these files do not depend on a metadata table in the executable.

The observations below apply to the exact files preserved in
`demo-unpack/x+rr+f_couloir14/`.

| Archive | Bytes | Decoded index | Stored index | First payload | Entries | Decoded bytes |
|---|---:|---:|---:|---:|---:|---:|
| `14.KLX` | 1,585,929 | 6,138 | 2,524 | 2,536 | 214 | 1,965,654 |
| `14_0.KLX` | 96,373 | 10,943 | 2,803 | 2,815 | 481 | 157,805 |
| `14_1.KLX` | 178,517 | 17,774 | 5,094 | 5,106 | 781 | 270,338 |

## Header and index

All integers are unsigned 32-bit little-endian values. There is no alignment
padding.

| Offset | Size | Meaning |
|---:|---:|---|
| `0x00` | 4 | ASCII signature `FXLK` (`0x4b4c5846` as little-endian integer) |
| `0x04` | 4 | Decoded index size |
| `0x08` | 4 | Stored index size |
| `0x0c` | stored index size | Headerless LZARI index stream |
| following | variable | File payloads in index order |

The decoded index has no count or sentinel. Its declared decoded size marks the
end. Each entry contains:

1. a null-terminated Windows-1252 path;
2. the decoded payload size as a little-endian `uint32`;
3. the stored payload size as a little-endian `uint32`.

An entry's payload offset is `12 + stored_index_size` plus all previous stored
payload sizes. In all three archives, the final entry ends exactly at the end
of the file; there are no unexplained gaps or trailers.

Paths use Windows backslashes and drive-like prefixes in these indexes:
`T:\\` and `D:\\` in the main archive, and lowercase `c:\\` in the auxiliary
archives. The extractor retains the drive identity as an uppercase ordinary
directory (`T/`, `D/`, or `C/`) below a new destination. It does not rewrite
the absolute `T:\\...` references inside LightWave and sequence files.

## Payload storage

If stored and decoded sizes differ, the payload is a headerless LZARI stream.
This applies to 1,475 of the 1,476 entries.

If the sizes are equal, each stored byte is decoded with `byte ^ 0x9a`. The
only such entry is the 20-byte `T/sub.bat` in `14.KLX`.

The LZARI variant uses:

- a 4,096-byte sliding window and matches from 3 to 60 bytes;
- 4,036 initial ASCII spaces followed by 60 zero bytes;
- 314 adaptive symbols, where 0–255 are literals and 256–313 encode match
  lengths as `symbol - 253`;
- arithmetic bounds `[0, 0x20000)` and a 17-bit initial code;
- bits read most-significant first;
- adaptive character frequencies initialized to one and halved at `0x7fff`;
- a fixed distance model built with `cum[i-1] = cum[i] + 10000 / (i + 200)`;
- the declared decoded byte count as the terminator rather than an EOF symbol.

Arithmetic termination can require limited zero-bit lookahead. Both supplied
decoders allow at most two virtual zero bytes and reject reads beyond that.

## Multiple containers

`14.KLX` is the main production archive. `14_0.KLX` and `14_1.KLX` contain two
different generated lightmap/UV sets:

| Archive | JPEG lightmaps | `UVset` bytes | Path root |
|---|---:|---:|---|
| `14_0.KLX` | 480 | 13,160 | `C/` plus `UVset` |
| `14_1.KLX` | 780 | 15,997 | `C/` plus `UVset` |

The two indexes share 33 case-insensitive paths, and their `UVset` payloads are
different. Extracting them into separate directories is therefore part of the
preservation model, not a cosmetic layout choice.

## Reconstruction and validation

`klx_unpack.c` derives from the extractor reconstructed from FreeStyle's
original x86 archive reader. Couloir 14 provides additional compatibility
evidence: all three files have valid `FXLK` headers, their indexes account for
every stored byte, and both the C and independent Python implementations decode
the same 1,476 paths, sizes, and SHA-256 payload hashes.

The format itself contains no checksums or timestamps. The authoritative
external hashes are recorded in `couloir14-manifest.json`; ZIP timestamps are
only available for the eight distribution files, not for individual KLX
entries.

The native extractor decodes every payload before creating the destination. It
rejects malformed sizes, traversal and rooted paths, Windows reserved names,
case-insensitive duplicates within one container, file/directory conflicts,
existing destinations, and inputs or decoded output above its 256 MiB limits.

Compatibility is established for the exact three Couloir 14 archives and the
previously preserved FreeStyle archive. No claim is made for every historical
file that happens to use a `.KLX` extension.
