from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.microsoft import is_msvc

from os import getenv

required_conan_version = ">=2.13.0"

class VCMI(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

    _libRequires = [
        "minizip/[^1.2.12]",
        "zlib/[^1.2.12]",
    ]
    _clientRequires = [
        "onetbb/[^2021.7]",
        "sdl_image/[^2.8.2]",
        "sdl_mixer/[^2.8.0]",
        "sdl_ttf/[^2.0.18]",
    ]
    _launcherRequires = [
        "xz_utils/[^5.2.5]", # innoextract
    ]
    requires = _libRequires + _clientRequires + _launcherRequires

    options = {
        "target_pre_windows10": [True, False],
        "with_ffmpeg": [True, False],
        "with_onnxruntime": [True, False],
        "lua_lib": [None, "luajit", "lua"]
    }
    default_options = {
        "target_pre_windows10": False,
        "with_ffmpeg": True,
        "with_onnxruntime": True,
        "lua_lib": "luajit",
    }

    def config_options(self):
        # static on "single app" platforms
        isSdlShared = not (self.settings.os == "iOS" or self.settings.os == "Android")
        self.options["sdl"].shared = isSdlShared
        self.options["sdl_image"].shared = isSdlShared
        self.options["sdl_mixer"].shared = isSdlShared
        self.options["sdl_ttf"].shared = isSdlShared

        if self.settings.os == "Android":
            self.options["qt"].android_sdk = getenv("ANDROID_HOME")

        if self.settings.os != "Windows":
            del self.options.target_pre_windows10

    def requirements(self):
        # lib
        # boost::filesystem removed support for Windows < 10 in v1.87
        boostMinVersion = "1.74"
        if self.options.get_safe("target_pre_windows10", False):
            self.requires(f"boost/[>={boostMinVersion} <1.87]")
        else:
            self.requires(f"boost/[^{boostMinVersion}]")

        if self.options.lua_lib:
            lib = str(self.options.lua_lib)
            libVersion = {
                "lua": "[^5.4.7]",
                "luajit": "2.1.0-beta3",
            }.get(lib)
            self.requires(f"{lib}/{libVersion}")

        # client
        if self.options.with_ffmpeg:
            self.requires("ffmpeg/[>=4.4]")

        # TODO: try enabling version range once there's no conflict
        # sdl_image & sdl_ttf depend on earlier version
        # ERROR: Version conflict: Conflict between sdl/2.28.5 and sdl/2.28.3 in the graph.
        # Conflict originates from sdl_mixer/2.8.0
        # upcoming SDL version 3.0+ is not supported at the moment due to API breakage
        # SDL versions between 2.22-2.26.1 have broken sound
        # self.requires("sdl/[^2.26.1 || >=2.0.20 <=2.22.0]")
        # versions before 2.30.7 don't build for Android with NDK 27: https://github.com/libsdl-org/SDL/issues/9792
        self.requires("sdl/2.32.2", override=True)

        # launcher
        if self.settings.os == "Android":
            self.requires("qt/[~5.15.14]") # earlier versions have serious bugs
        else:
            self.requires("qt/[~5.15.2]")

        if self.options.with_onnxruntime:
            self.requires("onnxruntime/1.18.1")

    def validate(self):
        # FFmpeg
        if is_msvc(self) and self.options.with_ffmpeg and self.dependencies["ffmpeg"].options.shared != True:
            raise ConanInvalidConfiguration("MSVC FFmpeg static build requires static runtime, but VCMI uses dynamic runtime. You must build FFmpeg as shared.")

        # SDL
        sdl2mainValue = self.settings.os != "iOS"
        if self.dependencies["sdl"].options.sdl2main != sdl2mainValue:
            raise ConanInvalidConfiguration(f"sdl:sdl2main option for {self.settings.os} must be set to {sdl2mainValue}")

        # LuaJIT
        if is_msvc(self) and self.settings.arch == "armv8" and self.options.lua_lib == "luajit":
            raise ConanInvalidConfiguration("LuaJIT can't be built for MSVC ARM64 at the moment, &:lua_lib option must be set to lua")

        # Qt
        qtDep = self.dependencies["qt"]
        if qtDep.options.qttools != True:
            raise ConanInvalidConfiguration("qt:qttools option must be set to True")
        if self.settings.os == "Android" and qtDep.options.qtandroidextras != True:
            # TODO: in Qt 6 this option doesn't exist
            raise ConanInvalidConfiguration("qt:qtandroidextras option for Android must be set to True")
        if not is_apple_os(self) and qtDep.options.openssl != True:
            raise ConanInvalidConfiguration("qt:openssl option for non-Apple OS must be set to True, otherwise mods can't be downloaded")
