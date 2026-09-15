#!/usr/bin/env python3
"""Regression tests for the preserved Dash distribution and recovered assets."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
TOOL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "bin" / "klx_unpack.exe"
if len(sys.argv) > 1:
    del sys.argv[1]
sys.path.insert(0, str(ROOT / "tools"))

from unpack_dash import read_entries  # noqa: E402


RELEASE_NAME = "1999_condense_dash(volcanic5)"
DISTRIBUTION = ROOT / "demo-releases" / f"{RELEASE_NAME}.zip"
UNPACKED = ROOT / "demo-unpack" / RELEASE_NAME
ASSETS = ROOT / "demo-assets" / RELEASE_NAME
EXECUTABLE = UNPACKED / "Dash.exe"
ARCHIVE = UNPACKED / "Dash.GCR"
SOUNDTRACK = UNPACKED / "Dash.XM"
MANIFEST_PATH = ROOT / "documentation" / "dash-manifest.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_lwob(path: Path, data: bytes) -> None:
    if data[:4] != b"FORM" or data[8:12] != b"LWOB":
        raise AssertionError(f"{path}: not a FORM/LWOB object")
    if struct.unpack_from(">I", data, 4)[0] + 8 != len(data):
        raise AssertionError(f"{path}: inconsistent FORM size")
    offset = 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise AssertionError(f"{path}: truncated IFF chunk")
        size = struct.unpack_from(">I", data, offset + 4)[0]
        offset += 8 + size + (size & 1)
    if offset != len(data):
        raise AssertionError(f"{path}: chunk extends beyond FORM")


def validate_tga(path: Path, data: bytes) -> tuple[int, int]:
    if len(data) < 18:
        raise AssertionError(f"{path}: truncated TGA header")
    id_length, color_map_type, image_type = data[:3]
    width, height = struct.unpack_from("<HH", data, 12)
    pixel_depth = data[16]
    if color_map_type != 0 or image_type != 10 or pixel_depth != 16 or not width or not height:
        raise AssertionError(f"{path}: unexpected TGA layout")
    offset = 18 + id_length
    remaining = width * height
    pixel_bytes = pixel_depth // 8
    while remaining:
        if offset >= len(data):
            raise AssertionError(f"{path}: truncated TGA RLE packet")
        packet = data[offset]
        offset += 1
        count = (packet & 0x7F) + 1
        if count > remaining:
            raise AssertionError(f"{path}: TGA packet exceeds image dimensions")
        offset += pixel_bytes if packet & 0x80 else count * pixel_bytes
        remaining -= count
    if offset != len(data):
        raise AssertionError(f"{path}: TGA payload has trailing or missing bytes")
    return width, height


def prk_packet_count(path: Path, data: bytes) -> int:
    if not data or len(data) % 2:
        raise AssertionError(f"{path}: invalid 16-bit PRK stream size")
    words = struct.unpack(f"<{len(data) // 2}H", data)
    offset = 0
    packets = 0
    while offset < len(words):
        face_count = words[offset]
        offset += 1
        if face_count > len(words) - offset:
            raise AssertionError(f"{path}: PRK face packet exceeds file")
        offset += face_count
        packets += 1
    return packets


class DashAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = TOOL
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def run_tool(
        self, *arguments: object, success: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(self.tool), *(str(argument) for argument in arguments)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        if success and result.returncode != 0:
            self.fail(f"extractor failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
        if not success and result.returncode == 0:
            self.fail(f"extractor unexpectedly succeeded:\n{result.stdout}")
        return result

    def test_distribution_and_expanded_zip(self) -> None:
        expected = self.manifest["distribution"]
        distribution_data = DISTRIBUTION.read_bytes()
        self.assertEqual(len(distribution_data), expected["size"])
        self.assertEqual(sha256(distribution_data), expected["sha256"])
        by_name = {entry["path"]: entry for entry in expected["entries"]}
        with ZipFile(DISTRIBUTION) as archive:
            self.assertEqual(set(archive.namelist()), set(by_name))
            for info in archive.infolist():
                data = archive.read(info)
                expanded = (UNPACKED / info.filename).read_bytes()
                self.assertEqual(data, expanded, info.filename)
                self.assertEqual(len(data), by_name[info.filename]["size"])
                self.assertEqual(sha256(data), by_name[info.filename]["sha256"])

    def test_manifest_and_committed_assets(self) -> None:
        expected_entries = {
            entry["path"]: entry for entry in self.manifest["container"]["entries"]
        }
        found = {
            path.relative_to(ASSETS).as_posix(): path
            for path in ASSETS.rglob("*")
            if path.is_file()
        }
        self.assertEqual(set(found), set(expected_entries))
        self.assertEqual(len(found), 98)
        self.assertEqual(sum(path.stat().st_size for path in found.values()), 1_818_588)
        for name, entry in expected_entries.items():
            data = found[name].read_bytes()
            self.assertEqual(len(data), entry["size"], name)
            self.assertEqual(sha256(data), entry["sha256"], name)

    def test_asset_formats(self) -> None:
        files = [path for path in ASSETS.rglob("*") if path.is_file()]
        counts = Counter(path.suffix.lower() for path in files)
        self.assertEqual(
            counts,
            Counter({".tga": 63, ".lwo": 28, ".lws": 4, ".prk": 3}),
        )
        for path in ASSETS.rglob("*.lwo"):
            validate_lwob(path, path.read_bytes())
        for path in ASSETS.rglob("*.tga"):
            validate_tga(path, path.read_bytes())
        for path in ASSETS.rglob("*.lws"):
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"LWSC\r\n1\r\n"), path)
            self.assertIn(b"D:\\vrac\\", data, path)
        expected_prk_packets = {"bcruise.prk": 38, "Ecrouland.prk": 28, "motion.prk": 50}
        for path in ASSETS.rglob("*.prk"):
            self.assertEqual(
                prk_packet_count(path, path.read_bytes()), expected_prk_packets[path.name]
            )

    def test_standalone_xm(self) -> None:
        data = SOUNDTRACK.read_bytes()
        expected = self.manifest["standalone_soundtrack"]
        self.assertEqual(len(data), expected["size"])
        self.assertEqual(sha256(data), expected["sha256"])
        self.assertTrue(data.startswith(b"Extended Module: "))
        self.assertEqual(data[37], 0x1A)
        self.assertEqual(struct.unpack_from("<H", data, 58)[0], 0x0104)
        self.assertEqual(
            struct.unpack_from("<8H", data, 64),
            (54, 0, 14, 57, 34, 1, 15, 147),
        )

    def test_python_decoder_matches_manifest(self) -> None:
        archive = ARCHIVE.read_bytes()
        entries = read_entries(archive, EXECUTABLE.read_bytes())
        by_path = {
            entry["original_path"]: entry
            for entry in self.manifest["container"]["entries"]
        }
        self.assertEqual(len(entries), 98)
        for entry in entries:
            payload = entry.decode(archive)
            expected = by_path[entry.name]
            self.assertEqual(len(payload), expected["size"], entry.name)
            self.assertEqual(sha256(payload), expected["sha256"], entry.name)

    def test_c_extractor_matches_manifest(self) -> None:
        listing = self.run_tool("--list", "--dash-exe", EXECUTABLE, ARCHIVE)
        self.assertTrue(listing.stdout.rstrip().endswith("98 files"))
        self.assertEqual(listing.stdout.count(" lzari "), 98)
        with tempfile.TemporaryDirectory(prefix="dash-unpack-") as temporary:
            output = Path(temporary) / "assets"
            self.run_tool("--dash-exe", EXECUTABLE, ARCHIVE, output)
            for entry in self.manifest["container"]["entries"]:
                data = (output / entry["path"]).read_bytes()
                self.assertEqual(sha256(data), entry["sha256"], entry["path"])
            self.run_tool("--dash-exe", EXECUTABLE, ARCHIVE, output, success=False)

    def test_rejects_truncation_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dash-invalid-") as temporary:
            temporary = Path(temporary)
            truncated = temporary / "Dash.GCR"
            truncated.write_bytes(ARCHIVE.read_bytes()[:-1])
            output = temporary / "output"
            self.run_tool("--dash-exe", EXECUTABLE, truncated, output, success=False)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
