# Qt 6 for Windows 7, 8, and 8.1

The Windows x86 and x64 CI matrix builds three independent dependency archives:
Qt 5, source-patched Qt 6.8.3, and source-patched Qt 6.11.1. The VCMI option
`qt_version` selects the package while `target_pre_windows10=True` keeps the
shared Windows 7 dependency constraints. Windows ARM64 and all non-Windows
platforms retain their previous Qt 5 dependency.

## Pinned inputs

- vcmi-dependencies base (`latest`):
  [`68f3f22614a3b17c80aa603b0c013181db845048`](https://github.com/GeorgeK1ng/vcmi-dependencies/commit/68f3f22614a3b17c80aa603b0c013181db845048)
- compared experiment (`Qt6_Win7`):
  [`7161db952022a90bb636dffc074af1ba1e265740`](https://github.com/GeorgeK1ng/vcmi-dependencies/commit/7161db952022a90bb636dffc074af1ba1e265740)
- merge-base:
  [`1210d49b440150d22d7ec283083feb63b1ef17af`](https://github.com/GeorgeK1ng/vcmi-dependencies/commit/1210d49b440150d22d7ec283083feb63b1ef17af)
- pinned [conan-center-index recipe commit](https://github.com/conan-io/conan-center-index/commit/990ef02afd83fa965fa654bdf3c156609f89f8b8):
  `990ef02afd83fa965fa654bdf3c156609f89f8b8`
- Qt 6.8.3 compatibility source:
  [crystalidea/qt6windows7 at `5b0166a`](https://github.com/crystalidea/qt6windows7/tree/5b0166ab2d15a1afbeb7bb63eaaf4dbaa3c17d27)
- official [QtBase v6.8.3 source](https://github.com/qt/qtbase/tree/v6.8.3) and
  [Conan Center `qt/6.8.3` recipe](https://conan.io/center/recipes/qt?version=6.8.3),
  with source archive SHA-256
  `cdd3a69967208276bb01af7ace7dba0ba53e679f886a4cbe624225c60fb73f2c`
- Qt 6.11.1 compatibility source:
  [forkgram/qt6windows7 at `2127fa0`](https://github.com/forkgram/qt6windows7/tree/2127fa0668b67fada62b7b4198ba979eaa638b6c)
  (the requested [`6.11.1` branch](https://github.com/forkgram/qt6windows7/tree/6.11.1))
- official [QtBase v6.11.1 source](https://github.com/qt/qtbase/tree/v6.11.1) and
  [Conan Center `qt/6.11.1` recipe](https://conan.io/center/recipes/qt?version=6.11.1),
  with source archive SHA-256
  `252acef8c5ae68074d91cadba2ee4a83465051bbb970dd26e8f0daa0f3904e03`
- workflow cache design:
  [GeorgeK1ng/vcmi-dependencies `cache` branch](https://github.com/GeorgeK1ng/vcmi-dependencies/blob/cache/.github/workflows/rebuildDependencies.yml)

The compatibility files were diffed against clean Qt 6.8.4 and that logical
diff was applied to clean Qt 6.8.3. The two 6.8.3-specific conflicts (thread
naming and UI Automation notification dispatch) were adapted instead of
copying whole 6.8.4 files. VCMI's D3D11 QRhi completion is deliberately stored
separately in `6.8.3-win7-d3d11.diff`. A second VCMI patch,
`6.8.3-win7-sdk.diff`, contains compile-time fixes for inconsistencies between
Qt's Windows 10 SDK declarations and the Windows 7 NTDDI target. Both are
applied after the imported backport so upstream-derived changes stay untouched.
For 6.11.1, Forkgram already includes the SDK declarations and the D3D11
factory/swapchain fallback, so its 77-file overlay is stored as one logical
diff against the clean official Qt 6.11.1 tag instead of duplicating fixes.

## Toolchain and package shape

The existing `msvc-x86` and `msvc-x64` profiles target Windows 7 SP1 headers
(`_WIN32_WINNT=0x0601`) and MSVC 19.29/v142. They use C++20 for VCMI (Qt itself
requires at least C++17), the dynamic MSVC runtime, and Release packages. The
generated platform-tools profile sets only the required C++17 minimum for the
native build context, because `qttools` makes Qt a build requirement as well as
a host requirement. This does not lower the independently configured C++20
host profile. Windows ARM64, Linux, macOS, iOS, and Android retain their
existing build profiles unchanged. The C++17 override is emitted only for a
selected Qt 6 variant. The build machine may be a newer Windows release.

The patched Qt package is shared and includes Widgets, SVG, Qt Tools, md4c,
and `qtdeclarative` (Qt Quick).
Qt Multimedia, WebEngine, and PDF are not in the current VCMI Conan graph and
are not built. Direct3D 11 RHI remains enabled: on Windows 7/8 the backport
falls back to `CreateDXGIFactory1` and a DXGI 1.1 discard-model HWND swapchain.
That legacy path intentionally has no HDR, tearing, DirectComposition, or frame
latency waitable object support. Direct3D 12 remains disabled only for the v142
legacy package because its required runtime APIs are unavailable on Windows 7.
The normal newer-Windows packages are unaffected.

On Windows 7, the D3D11 backend requires SP1 and the Platform Update
(`KB2670838`), because Qt 6.8 requires the Direct3D 11.1 runtime interfaces such
as `ID3D11DeviceContext1`. If that update or a compatible graphics driver is
missing, QRhi must fall back to another backend such as OpenGL.

Qt 6 remains compiled with `_WIN32_WINNT=0x0601` and
`NTDDI_VERSION=0x06010000`. Its private QRhi headers unconditionally store
DirectComposition interface pointers, whose declarations the Windows SDK hides
at that target level. A narrow private wrapper temporarily exposes only the
`dcomp.h` declarations and then restores `NTDDI_VERSION` to Windows 7. The
actual `DCompositionCreateDevice` entry point remains dynamically resolved and
the legacy swapchain path does not invoke DirectComposition.

## Local build

Install Visual Studio with the v142 x86/x64 toolset, a current Windows SDK,
Python, Conan 2.25 or newer, Git for Windows, CMake, Ninja, and Strawberry Perl.
Run from a Git Bash whose environment can locate `cl.exe` and Strawberry Perl:

```bash
export WINDOWS_PERL_DIR='/c/Strawberry/perl/bin'
export QT_VARIANT=qt6-8-3   # qt5, qt6-8-3, or qt6-11-1
./build.sh windows-x64
# or
./build.sh windows-x86
```

For stepwise diagnosis, preserve the variables printed by `prepare` and run:

```bash
BUILD_ACTION=prepare ./build.sh windows-x64
BUILD_ACTION=build_recipes_with_patches ./build.sh windows-x64
BUILD_ACTION=build_onnx_recipes_with_patches ./build.sh windows-x64
BUILD_ACTION=build_custom_recipes ./build.sh windows-x64
BUILD_ACTION=build_normal_recipes ./build.sh windows-x64
```

`build_recipes_with_patches` checks the recipe patch before applying it, pins
CCI, creates the Qt package locally, and then verifies both the merged patch
metadata and exported patch file in the Conan cache. The later install does not
use `--update`, so the locally exported recipe revision remains selected.
The CCI pin and recipe modification are executed only for a `qt6-*` variant.
Within that patched recipe, MSVC 19.29/v142 is
accepted generally because it is the Windows 7 toolchain. The source backport
and Direct3D compatibility changes remain restricted to the exact selected Qt
6 version. Other platforms retain the unmodified CCI recipe and existing
dependency flow.

To inspect the resulting graph without the custom LuaJIT recipe, use:

```bash
conan graph info . \
  --profile:host=conan_profiles/msvc-x64 \
  --profile:build=default \
  --options='&:target_pre_windows10=True' \
  --options='&:qt_version=6.8.3' \
  --options='&:lua_lib=lua'
conan list 'qt/6.8.3#*:*'
```

## Runtime verification

Do not treat a successful build as proof of Windows 7 compatibility. On clean
VMs, install Windows 7 SP1 plus the Platform Update KB2670838 and the matching
VC++ 2015-2022 x86/x64 redistributable. Copy the VCMI build and deploy the Qt
platform and image plugins. On Windows 7 SP1, Windows 8, Windows 8.1, and a
current Windows regression machine, test:

1. launcher and editor startup and loading `qwindows.dll`;
2. text rendering, SVG icons, file dialogs, drag and drop, and accessibility;
3. HTTPS downloads through VCMI/libcurl and DNS resolution;
4. clean shutdown and absence of missing-import errors in Qt DLLs/plugins.

Use `dumpbin /imports` (or Dependencies) on `Qt6Core.dll`, `Qt6Gui.dll`,
`Qt6Widgets.dll`, `Qt6Network.dll`, `Qt6Svg.dll`, `qwindows.dll`, and their
transitive DLLs. The source backport dynamically resolves newer APIs and uses
fallbacks; `_WIN32_WINNT` alone is not the compatibility mechanism.

No Windows 7/8/8.1 VM is available in this checkout, so runtime compatibility
must remain reported as unverified until those tests pass.

## Experimental branch decisions

- Adapted: Qt 6.8.3 selection, the source compatibility patch, v142 recipe
  validation, a DXGI 1.1 D3D11 swapchain fallback, and legacy-only D3D12
  disabling.
- Corrected: patch metadata lives under `conan_patches/qt`, because Conan's
  `core.sources.patch:extra_path` keys it by package name. The experimental
  `conan_patches/qt6` metadata was never selected.
- Corrected: CCI and the compatibility source are pinned; the upstream CCI
  source/checksum and its existing patches remain merged into exported data.
- Rejected: lowering C++17 to C++14. Qt 6.8.3 still validates C++17, while the
  VCMI profiles request C++20.
- Rejected: globally disabling D3D, merging the diverged branch, or replacing
  Qt source metadata with a five-line file.
- Replaced: the experiment's workflow edits. Current `latest` centralizes these
  steps in `build.sh`; it now has a single Qt 6 source path and skips the Qt 5
  PR recipe for legacy Windows builds.
