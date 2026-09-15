#!/usr/bin/env python3
"""Build Couloir 14's provenance manifest from the untouched ZIP and KLX data."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct
from zipfile import ZipFile

from unpack_klx import read_archive, relative_path


ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTION = ROOT / "demo-releases" / "x+rr+f_couloir14.zip"
UNPACKED = ROOT / "demo-unpack" / "x+rr+f_couloir14"
ASSETS = ROOT / "demo-assets" / "x+rr+f_couloir14"
OUTPUT = ROOT / "documentation" / "couloir14-manifest.json"
ARCHIVES = (
    ("14.KLX", "14"),
    ("14_0.KLX", "14_0"),
    ("14_1.KLX", "14_1"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
            timestamp = datetime(*info.date_time).isoformat(sep=" ")
            zip_entries.append(
                {
                    "path": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "sha256": sha256(expanded),
                    "zip_timestamp": timestamp,
                }
            )

    archive_manifests = []
    total_files = total_bytes = 0
    for archive_name, output_directory in ARCHIVES:
        data = (UNPACKED / archive_name).read_bytes()
        entries, index = read_archive(data)
        index_size, stored_index_size = struct.unpack_from("<II", data, 4)
        if len(index) != index_size:
            raise ValueError(f"decoded index size mismatch: {archive_name}")
        result_entries = []
        methods = Counter()
        for entry in entries:
            relative = relative_path(entry.name)
            payload = entry.decode(data)
            committed = ASSETS / output_directory / relative
            if committed.read_bytes() != payload:
                raise ValueError(f"committed payload mismatch: {committed}")
            methods[entry.method] += 1
            result_entries.append(
                {
                    "original_path": entry.name,
                    "path": f"{output_directory}/{relative.as_posix()}",
                    "size": entry.size,
                    "stored_size": entry.stored_size,
                    "offset": entry.offset,
                    "method": entry.method,
                    "sha256": sha256(payload),
                }
            )
        decoded_size = sum(entry.size for entry in entries)
        archive_manifests.append(
            {
                "name": archive_name,
                "output_directory": output_directory,
                "archive_size": len(data),
                "archive_sha256": sha256(data),
                "index_size": index_size,
                "stored_index_size": stored_index_size,
                "index_sha256": sha256(index),
                "file_count": len(entries),
                "total_size": decoded_size,
                "methods": dict(sorted(methods.items())),
                "entries": result_entries,
            }
        )
        total_files += len(entries)
        total_bytes += decoded_size

    manifest = {
        "schema_version": 1,
        "title": "Couloir 14 asset extraction manifest",
        "distribution": {
            "path": "demo-releases/x+rr+f_couloir14.zip",
            "size": len(distribution_data),
            "sha256": sha256(distribution_data),
            "entries": zip_entries,
        },
        "format": "FXLK / KLX",
        "filename_encoding": "Windows-1252",
        "path_mapping": "archive separators normalized below a per-KLX directory",
        "archives": archive_manifests,
        "totals": {"file_count": total_files, "decoded_size": total_bytes},
        "verification": (
            "Every payload was independently decoded in Python and compared byte for "
            "byte with the committed C extractor output."
        ),
    }
    OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUTPUT}: {total_files} files, {total_bytes} decoded bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
