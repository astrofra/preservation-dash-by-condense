#!/usr/bin/env python3
"""Build Dash's provenance manifest from the untouched ZIP and GCR data."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
from zipfile import ZipFile

from unpack_dash import ENTRY_COUNT, TABLE_RVA, read_entries


ROOT = Path(__file__).resolve().parents[1]
RELEASE_NAME = "1999_condense_dash(volcanic5)"
DISTRIBUTION = ROOT / "demo-releases" / f"{RELEASE_NAME}.zip"
UNPACKED = ROOT / "demo-unpack" / RELEASE_NAME
ASSETS = ROOT / "demo-assets" / RELEASE_NAME
EXECUTABLE = UNPACKED / "Dash.exe"
ARCHIVE = UNPACKED / "Dash.GCR"
SOUNDTRACK = UNPACKED / "Dash.XM"
OUTPUT = ROOT / "documentation" / "dash-manifest.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def xm_metadata(data: bytes) -> dict[str, object]:
    if len(data) < 80 or not data.startswith(b"Extended Module: ") or data[37] != 0x1A:
        raise ValueError("Dash.XM has an invalid FastTracker XM header")
    version = struct.unpack_from("<H", data, 58)[0]
    header_size = struct.unpack_from("<I", data, 60)[0]
    fields = struct.unpack_from("<8H", data, 64)
    if version != 0x0104 or header_size < 20:
        raise ValueError("Dash.XM uses an unexpected XM version or header size")
    return {
        "module_name": data[17:37].rstrip(b"\0 ").decode("cp437"),
        "tracker": data[38:58].rstrip(b"\0 ").decode("cp437"),
        "version": f"{version >> 8}.{version & 0xff:02d}",
        "header_size": header_size,
        "song_length": fields[0],
        "restart_position": fields[1],
        "channels": fields[2],
        "patterns": fields[3],
        "instruments": fields[4],
        "linear_frequency_table": bool(fields[5] & 1),
        "default_tempo": fields[6],
        "default_bpm": fields[7],
    }


def main() -> int:
    distribution_data = DISTRIBUTION.read_bytes()
    zip_entries = []
    with ZipFile(DISTRIBUTION) as archive:
        for info in archive.infolist():
            expanded = (UNPACKED / info.filename).read_bytes()
            if len(expanded) != info.file_size:
                raise ValueError(f"expanded ZIP size mismatch: {info.filename}")
            if archive.read(info) != expanded:
                raise ValueError(f"expanded ZIP payload mismatch: {info.filename}")
            zip_entries.append(
                {
                    "path": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "sha256": sha256(expanded),
                    "zip_timestamp": datetime(*info.date_time).isoformat(sep=" "),
                }
            )

    executable = EXECUTABLE.read_bytes()
    archive_data = ARCHIVE.read_bytes()
    entries = read_entries(archive_data, executable)
    if len(entries) != ENTRY_COUNT:
        raise ValueError("unexpected GCR entry count")
    result_entries = []
    methods = Counter()
    extensions = Counter()
    for entry in entries:
        payload = entry.decode(archive_data)
        committed = ASSETS / entry.path
        if committed.read_bytes() != payload:
            raise ValueError(f"committed payload mismatch: {committed}")
        methods[entry.method] += 1
        extensions[entry.path.suffix.lower()] += 1
        result_entries.append(
            {
                "original_path": entry.name,
                "path": entry.path.as_posix(),
                "record_offset": entry.record_offset,
                "record_size": entry.record_size,
                "size": entry.size,
                "payload_offset": entry.payload_offset,
                "stored_size": entry.stored_size,
                "method": entry.method,
                "sha256": sha256(payload),
            }
        )

    soundtrack_data = SOUNDTRACK.read_bytes()
    total_size = sum(entry.size for entry in entries)
    manifest = {
        "schema_version": 1,
        "title": "Dash asset extraction manifest",
        "distribution": {
            "path": f"demo-releases/{RELEASE_NAME}.zip",
            "size": len(distribution_data),
            "sha256": sha256(distribution_data),
            "entries": zip_entries,
        },
        "container": {
            "path": f"demo-unpack/{RELEASE_NAME}/Dash.GCR",
            "size": len(archive_data),
            "sha256": sha256(archive_data),
            "format": "Dash GCR external-table LZARI",
            "metadata_executable": f"demo-unpack/{RELEASE_NAME}/Dash.exe",
            "metadata_executable_size": len(executable),
            "metadata_executable_sha256": sha256(executable),
            "metadata_table_rva": f"0x{TABLE_RVA:08x}",
            "metadata_table_raw_offset": "0x00015e30",
            "filename_encoding": "Windows-1252",
            "path_mapping": "drive identity retained as an ordinary directory",
            "file_count": len(entries),
            "total_size": total_size,
            "methods": dict(sorted(methods.items())),
            "extensions": dict(sorted(extensions.items())),
            "entries": result_entries,
        },
        "standalone_soundtrack": {
            "path": f"demo-unpack/{RELEASE_NAME}/Dash.XM",
            "size": len(soundtrack_data),
            "sha256": sha256(soundtrack_data),
            "format": "FastTracker XM",
            "metadata": xm_metadata(soundtrack_data),
        },
        "totals": {
            "container_file_count": len(entries),
            "container_decoded_size": total_size,
            "production_asset_count_including_soundtrack": len(entries) + 1,
            "production_asset_size_including_soundtrack": total_size + len(soundtrack_data),
        },
        "verification": (
            "Every GCR payload was independently decoded in Python and compared "
            "byte for byte with the committed native-extractor output."
        ),
    }
    OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUTPUT}: {len(entries)} files, {total_size} decoded bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
