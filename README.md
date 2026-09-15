# Preservation of Dash by Condense

Asset extraction for **Dash**, a 1999 Win32 demo by Condense released at
Volcanic Party 5. The untouched distribution archive is kept in
`demo-releases/`, its six ordinary ZIP entries in `demo-unpack/`, and the 98
files recovered from `Dash.GCR` in `demo-assets/`.

The recovered container files comprise 28 LightWave objects, four LightWave
scenes, 63 TGA textures, and three X3 precalculation streams. The original
591,350-byte FastTracker XM soundtrack is already a standalone ZIP entry. No
asset path or payload was converted, renamed, or rewritten.

The release notes identify X3 as the 3D engine used by Dash. The preserved
[nXng engine repository](https://github.com/demoscene-source-archive/preservation-nxng-engine)
also lists Dash/X3 before LTP3/X32, FreeStyle/nX, and Couloir 14/nXng, making
this release direct evidence for the earliest documented branch of that engine
lineage.

Build and extract on Windows:

```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
./bin/klx_unpack.exe --dash-exe `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.exe' `
    'demo-unpack/1999_condense_dash(volcanic5)/Dash.GCR' `
    demo-assets/another-extraction
```

The destination must not already exist. Run the regression checks with:

```powershell
ctest --test-dir build -C Release --output-on-failure
```

See the [complete extraction process](documentation/EXTRACTION_PROCESS.md),
[GCR format description](documentation/dash-container-format.md),
[asset validation report](documentation/ASSET_VALIDATION.md), and
[SHA-256 manifest](documentation/dash-manifest.json).
