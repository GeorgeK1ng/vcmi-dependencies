# VCMI Dependencies

Repository for building and publishing prebuilt Conan dependencies used by [VCMI](https://vcmi.eu/).

This repo is primarily used by GitHub Actions to produce dependency bundles (`dependencies-*.txz`) for multiple platforms. Developers can also use it locally to reproduce the same dependency graph/options as CI.

## What is in this repository

- `conanfile.py` - root dependency graph + high-level feature switches used by VCMI.  
- `conan_profiles/` - platform profiles (host settings/options/conf), including shared base profiles.  
- `conan_patches/` - custom patches applied to selected Conan Center recipes.  
- `ci/` - helper scripts used by CI jobs (platform setup).  
- `.github/workflows/rebuildDependencies.yml` - main build workflow producing artifacts.  
- `.github/workflows/releaseFromRun.yml` - workflow that converts artifacts from a selected run into a GitHub release.

## Prerequisites (local)

- Python 3
- Conan 2.13+
- C/C++ toolchain for your target platform
- Optional: Android SDK/NDK for Android builds

In CI, Conan is installed via `pipx install conan`.

## Quick start (local)

### 1) Install Conan and detect default profile

```bash
pipx install conan
conan profile detect
```

### 2) Build dependencies for a target

Basic example (Windows x64, dynamic mode):

```bash
conan install . --output-folder=conan-generated --build=missing --profile=conan_profiles/msvc-x64
```

If you want to build recipe binaries directly (like CI does for selected recipes), use `conan create` on recipe paths.

## Main Conan options in `conanfile.py`

These switches are defined at the top level and can be passed as `-o "&:<option>=<value>"`.

- `windows_libs=dynamic|static` (Windows only, default `dynamic`)
- `target_pre_windows10=True|False` (Windows only)
- `with_ffmpeg=True|False`
- `with_onnxruntime=True|False`
- `with_discord_presence=True|False` (not available on mobile)
- `lua_lib=None|luajit|lua`

Example:

```bash
conan install . --output-folder=conan-generated --build=missing --profile=conan_profiles/msvc-x64 -o "&:windows_libs=static"
```

## Windows linkage modes (dynamic vs static)

Windows dependencies can be generated in two linkage variants:

- `windows_libs=dynamic` (default)
- `windows_libs=static`

CI publishes both variants for Windows targets.

## Platform profiles

Top-level profiles in `conan_profiles/` compose shared base profiles from `conan_profiles/base/`.

Common host profiles:

- Windows: `msvc-x64`, `msvc-x86`, `msvc-arm64`
- Linux: `linux-x64`, `linux-arm64`
- macOS: `macos-intel`, `macos-arm`
- iOS: `ios-arm64`
- Android: `android-32-ndk`, `android-64-ndk`, `android-x64-ndk`

Notes:

- Most shared options are centralized in `conan_profiles/base/common`.
- Apple/Android profiles use `replace_requires` to pick selected system packages.
- Android NDK tool requirement is configured in `conan_profiles/base/android-ndk`.

## How CI build works

Main workflow: `.github/workflows/rebuildDependencies.yml`

High-level flow per matrix target:

1. Checkout repository.
2. Prepare platform environment (`ci/*.sh` when needed).
3. Install Conan and setup profiles/tool-requires.
4. Build selected patched recipes from Conan Center / fork.
5. Run `conan install . --build=missing ...` for remaining graph.
6. Clean cache, generate package list, archive cache to `dependencies-<platform>.txz`.
7. Upload two artifacts:
   - `list of dependencies-<platform>`
   - `dependencies-<platform>`

Windows matrix currently builds both linkage variants:

- `windows-x64-dynamic`, `windows-x64-static`
- `windows-x86-dynamic`, `windows-x86-static`
- `windows-arm64-dynamic`, `windows-arm64-static`

## Release process

Current flow to update dependencies:

1. Open PR with changes.
2. Make sure CI build succeeds.
3. Merge the PR.
4. Run `Create release from Actions run` workflow (`releaseFromRun.yml`) with the source run ID.
5. (TBD) Update dependencies submodule and prebuilts URL in VCMI repo to point to the new commit/release; update VCMI code if needed.

## Working with patches

Custom recipe patches are stored in `conan_patches/<package>/`.

When patching/updating:

- keep versions in patch metadata aligned with versions used in CI/workflow commands,
- keep comments in workflow and profile files in sync with actual constraints/workarounds,
- verify patched recipes still build on all affected matrix targets.
