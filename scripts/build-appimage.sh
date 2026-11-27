#!/usr/bin/env bash

set -eu

# Never hang waiting for git credentials (build-deps.sh may clone); fail instead.
export GIT_TERMINAL_PROMPT=0

SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
cd -- "$SCRIPT_DIR/.."

# Outside CI fall back to the local git SHA so the artifact name is never empty.
CI_COMMIT_SHORT_SHA="${CI_COMMIT_SHORT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || printf local)}"

# Where copy_deps looks for libraries to bundle: build-deps.sh installs the codec libs and ffmpeg's shared objects here.
DEP_SEARCH_PATHS="$PWD/tools/deps/lib"

# Base-system libs every target machine already has, so never bundle these.
DEP_EXCLUDE='^libc\.so|^libpthread\.so|^libdl\.so|^libm\.so|^librt\.so|^ld-linux|^linux-vdso'

# Bundle every non-excluded library $bin links against into $dest.
# "? <soname>" entries (ldd found no path) are re-resolved from DEP_SEARCH_PATHS.
copy_deps() {
    local bin=$1
    local dest=$2
    local unresolved=""

    if [ ! -f "$bin" ]; then
        return 0
    fi
    echo "Collecting dependencies for $bin..."

    local search
    search=$(printf '%s' "$DEP_SEARCH_PATHS" | tr ' ' ':')

    while IFS= read -r entry; do
        local src
        local name

        if [ "${entry#\? }" = "$entry" ]; then
            src=$entry
            name=${src##*/}
        else
            src=""
            name="${entry#\? }"
        fi

        if printf '%s\n' "$name" | grep -qE "$DEP_EXCLUDE"; then
            continue
        fi

        # Sonames resolve identically for every tool, so bundle each one only once.
        if [ -e "$dest/$name" ]; then
            continue
        fi

        if [ -z "$src" ]; then
            local d
            for d in $DEP_SEARCH_PATHS; do
                if [ -e "$d/$name" ]; then
                    src="$d/$name"
                    break
                fi
            done
            if [ -z "$src" ]; then
                unresolved="$unresolved $name"
                continue
            fi
        fi

        if ! cp -L "$src" "$dest/$name"; then
            echo "  !! failed to copy $src" >&2
            unresolved="$unresolved $name"
        fi
    done < <(LD_LIBRARY_PATH="$search${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        ldd "$bin" 2>/dev/null \
        | awk '$2 == "=>" { if ($3 ~ /^\//) print $3; else print "? " $1 }')

    if [ -n "$unresolved" ]; then
        echo "ERROR: $bin needs libraries that could not be bundled:$unresolved" >&2
        echo "Looked for them in: $DEP_SEARCH_PATHS" >&2
        return 1
    fi
}

rm -rf build dist AppDir

# Reuse a prebuilt tools/ tree (e.g. a CI cache mounted at $TOOLS_SEED) instead of recompiling ffmpeg from source.
TOOLS_SEED="${TOOLS_SEED:-/opt/ffmpeg2discord/tools}"
if [ ! -f "tools/ffmpeg" ] && [ -f "$TOOLS_SEED/ffmpeg" ]; then
    echo "Using the FFmpeg prebuilt into the packaging image ($TOOLS_SEED)..."
    rm -rf tools
    cp -a "$TOOLS_SEED" tools
fi
mkdir -p tools
if [ ! -f "tools/ffmpeg" ]; then
    bash "$SCRIPT_DIR/build-deps.sh" tools
fi

# jpegoptim comes from the build host; copy_deps bundles its shared libs below.
if [ ! -f "tools/jpegoptim" ]; then
    echo "Copying jpegoptim..."
    cp /usr/bin/jpegoptim tools/
fi

# Single-file PyInstaller build of the app; the Qt .ui file ships as bundled data.
pyinstaller --noconsole --onefile --optimize 2 --add-data "src/FFmpeg2DiscordUI.ui:." src/FFmpeg2Discord.py

# AppDir skeleton that appimagetool packs into the final image; the icons
# subdir backs the Icon=ffmpeg2discord entry in the .desktop file.
mkdir -p AppDir/usr/bin AppDir/usr/lib AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/64x64/apps

# Install the app binary and every bundled tool into the image's usr/bin.
# Tools are named explicitly: copying all of tools/ would drag tools/deps --
# a build-time tree of headers and pkgconfig files -- into the image.
TOOLS="ffmpeg ffprobe jpegoptim"
cp dist/FFmpeg2Discord AppDir/usr/bin/FFmpeg2Discord
for tool in $TOOLS; do
    cp "tools/$tool" "AppDir/usr/bin/$tool"
done

# Collect each tool's shared libs into usr/lib so the image runs without host libs.
for tool in $TOOLS; do
    copy_deps "tools/$tool" "AppDir/usr/lib"
done

# Fail the build if $bin resolves any non-excluded library from outside $libdir
# (i.e. from the build host, which target systems won't have).
verify_bundled_libs() {
    local bin=$1
    local libdir
    local line
    local name
    local path
    local offenders=""

    if [ ! -f "$bin" ]; then
        echo "ERROR: $bin is missing from the AppDir." >&2
        return 1
    fi
    libdir=$(cd "$2" && pwd)

    while IFS= read -r line; do
        name=${line%% *}
        path=${line#* }
        name=${name##*/}

        if printf '%s\n' "$name" | grep -qE "$DEP_EXCLUDE"; then
            continue
        fi

        case $path in
            "$libdir"/*) ;;
            *) offenders="$offenders $name" ;;
        esac
    done < <(LD_LIBRARY_PATH="$libdir" ldd "$bin" 2>/dev/null |
        awk '$2 == "=>" { print $1, ($3 == "not" ? "not-found" : $3) }')

    if [ -n "$offenders" ]; then
        echo "ERROR: $bin resolves libraries from the build host, not the AppImage:$offenders" >&2
        echo "Bundle them via DEP_SEARCH_PATHS, or add them to DEP_EXCLUDE if they" >&2
        echo "are guaranteed to exist on every target system." >&2
        return 1
    fi
}

for tool in $TOOLS; do
    verify_bundled_libs "AppDir/usr/bin/$tool" AppDir/usr/lib
done

# Re-run build-deps.sh's feature check against the bundled ffmpeg + libs.
bash "$SCRIPT_DIR/build-deps.sh" --check AppDir/usr/bin/ffmpeg AppDir/usr/lib

# Root copy is what appimagetool requires; the usr/share/applications copy
# follows the usual FHS layout inside the image.
cp appimage/ffmpeg2discord.desktop AppDir/
cp appimage/ffmpeg2discord.desktop AppDir/usr/share/applications/

# Create dummy icon since it is required by Appimage.
ICON_FILE="appimage/ffmpeg2discord.png"
if [ ! -f "$ICON_FILE" ]; then
    echo "Icon not found, creating dummy icon..."
    mkdir -p appimage
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==" | base64 -d > "$ICON_FILE"
fi
cp "$ICON_FILE" AppDir/
# .DirIcon is the icon name the AppImage spec expects at the AppDir root.
cp "$ICON_FILE" AppDir/.DirIcon
cp "$ICON_FILE" AppDir/usr/share/icons/hicolor/64x64/apps/

# AppRun is the AppImage's entry point (see appimage/AppRun); image is broken without it.
if [ ! -f "appimage/AppRun" ]; then
    echo "ERROR: appimage/AppRun is missing; it is the entry point of the AppImage." >&2
    exit 1
fi
cp appimage/AppRun AppDir/AppRun
chmod +x AppDir/AppRun

# Pack the AppDir; zstd keeps the image small and cheap to decompress at runtime.
appimagetool --comp zstd --mksquashfs-opt -Xcompression-level --mksquashfs-opt 19 \
    AppDir "FFmpeg2Discord-x86_64-$CI_COMMIT_SHORT_SHA.AppImage"

echo "AppImage build complete: FFmpeg2Discord-x86_64-$CI_COMMIT_SHORT_SHA.AppImage"
