# Qt 6.8.3 for Windows 7, 8, and 8.1

This repository builds a source-patched `qt/6.8.3` package only when the VCMI
root option `target_pre_windows10=True` is selected. Other platforms and the
ordinary Windows 10+ configuration keep the existing Qt 5 dependency.

## Pinned inputs

- vcmi-dependencies base (`latest`): `68f3f22614a3b17c80aa603b0c013181db845048`
- compared experiment (`Qt6_Win7`): `7161db952022a90bb636dffc074af1ba1e265740`
- merge-base: `1210d49b440150d22d7ec283083feb63b1ef17af`
- conan-center-index recipe: `990ef02afd83fa965fa654bdf3c156609f89f8b8`
- compatibility source: crystalidea/qt6windows7 `v6.8.4`, commit
  `5b0166ab2d15a1afbeb7bb63eaaf4dbaa3c17d27`
- Qt source: the CCI `qt/6.8.3` archive with SHA-256
  `cdd3a69967208276bb01af7ace7dba0ba53e679f886a4cbe624225c60fb73f2c`

The compatibility files were diffed against clean Qt 6.8.4 and that logical
diff was applied to clean Qt 6.8.3. The two 6.8.3-specific conflicts (thread
naming and UI Automation notification dispatch) were adapted instead of
copying whole 6.8.4 files.

## Toolchain and package shape

The existing `msvc-x86` and `msvc-x64` profiles target Windows 7 SP1 headers
(`_WIN32_WINNT=0x0601`) and MSVC 19.29/v142. They use C++20 for VCMI (Qt itself
requires at least C++17), the dynamic MSVC runtime, and Release packages. The
generated platform-tools profile sets only the required C++17 minimum for the
native build context, because `qttools` makes Qt a build requirement as well as
a host requirement. This does not lower the independently configured C++20
host profile. The override is emitted only with `target_pre_windows10=True`;
Windows ARM64, Linux, macOS, iOS, and Android retain their existing build
profiles unchanged. The build machine may be a newer Windows release.

The patched Qt package is shared and includes Widgets, SVG, Qt Tools, and md4c.
Qt Multimedia, WebEngine, and PDF are not in the current VCMI Conan graph and
are not built. Direct3D 11/12 RHI is disabled only for the v142 legacy package;
the backport documents those RHI paths as unsupported on Windows 7. The normal
newer-Windows packages are unaffected.

## Local build

Install Visual Studio with the v142 x86/x64 toolset, a current Windows SDK,
Python, Conan 2.25 or newer, Git for Windows, CMake, Ninja, and Strawberry Perl.
Run from a Git Bash whose environment can locate `cl.exe` and Strawberry Perl:

```bash
export WINDOWS_PERL_DIR='/c/Strawberry/perl/bin'
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
The CCI pin and recipe modification are executed only for
`target_pre_windows10=True`. Within that patched recipe, MSVC 19.29/v142 is
accepted generally because it is the Windows 7 toolchain. The source backport
and Direct3D feature changes remain restricted to exactly Qt 6.8.3. Other
platforms retain the unmodified CCI recipe and existing dependency flow.

To inspect the resulting graph without the custom LuaJIT recipe, use:

```bash
conan graph info . \
  --profile:host=conan_profiles/msvc-x64 \
  --profile:build=default \
  --options='&:target_pre_windows10=True' \
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
  validation, and legacy-only D3D feature handling.
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
