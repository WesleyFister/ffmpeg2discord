#!/usr/bin/env bash

set -eu
export GIT_TERMINAL_PROMPT=0

# Exact feature set the app needs (must match src/encoder.py).
# verify_ffmpeg fails the build if the finished ffmpeg can't provide any of it.
REQUIRED_ENCODERS="libx264 libvpx-vp9 libsvtav1 libopus aac mjpeg libwebp libwebp_anim"
REQUIRED_MUXERS="mp4 matroska webm ogg webp image2 image2pipe"

# "libvpx-vp9 libwebp_anim" -> "libvpx_vp9,libwebp_anim": the comma/underscore
# list form ./configure's --enable-encoder/--enable-muxer expect.
configure_list() {
    printf '%s' "$1" | tr ' -' ',_'
}

FFMPEG_BIN=""
FFMPEG_LIBDIR=""
missing=""

# Note every name from the list in "${@:2}" that `ffmpeg $flag` doesn't offer.
check_available() {
    local flag=$1
    local name
    local list

    list=$(LD_LIBRARY_PATH="$FFMPEG_LIBDIR" \
        "$FFMPEG_BIN" -hide_banner "$flag" |
        awk '{print $2}')

    if [ -z "$list" ]; then
        echo "ERROR: '$FFMPEG_BIN $flag' produced no output, so the check cannot run." >&2
        echo "$FFMPEG_BIN cannot load its libraries from $FFMPEG_LIBDIR." >&2
        exit 1
    fi

    for name in "${@:2}"; do
        if ! printf '%s\n' "$list" | grep -qw -- "$name"; then
            missing="$missing $name"
        fi
    done
}

# Run the availability checks against the ffmpeg at $1 (libs loaded from $2) and exit nonzero if anything required is missing.
verify_ffmpeg() {
    FFMPEG_BIN=$1
    FFMPEG_LIBDIR=$2
    missing=""

    # shellcheck disable=SC2086
    check_available -encoders $REQUIRED_ENCODERS
    # shellcheck disable=SC2086
    check_available -muxers $REQUIRED_MUXERS

    if [ -n "$missing" ]; then
        echo "ERROR: $FFMPEG_BIN is missing:$missing" >&2
        echo "Compare REQUIRED_ENCODERS/REQUIRED_MUXERS in this file with src/encoder.py." >&2
        exit 1
    fi
}

# --check mode: verify an already-built ffmpeg (e.g. the bundled one from
# build-appimage.sh) instead of building anything.
if [ "${1:-}" = "--check" ]; then
    if [ -z "${2:-}" ]; then
        echo "Usage: ${0##*/} --check <ffmpeg-binary> [library-dir]" >&2
        exit 2
    fi
    verify_ffmpeg "$2" "${3:-$(dirname "$2")/../lib}"
    echo "OK: $2 provides every encoder and muxer that src/encoder.py needs."
    exit 0
fi

TOOLS_DIR="${1:-$PWD/tools}"
mkdir -p "$TOOLS_DIR"
TOOLS_DIR="$(cd "$TOOLS_DIR" && pwd)"

DEPS_PREFIX="$TOOLS_DIR/deps"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

export PKG_CONFIG_PATH="$DEPS_PREFIX/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"

# Built first so its headers/pkgconfig files are in place for FFmpeg's configure.
echo "Compiling SVT-AV1 from source..."
git clone --depth 1 https://github.com/AOMediaCodec/SVT-AV1.git "$WORK_DIR/svtav1_src"
cmake -S "$WORK_DIR/svtav1_src" -B "$WORK_DIR/svtav1_build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$DEPS_PREFIX" \
    -DBUILD_SHARED_LIBS=ON \
    -DSVT_AV1_LTO=ON \
    -DSVT_AV1_PGO=ON
cmake --build "$WORK_DIR/svtav1_build" -j"$(nproc)"
cmake --install "$WORK_DIR/svtav1_build"
rm -rf "$WORK_DIR/svtav1_src"

echo "Compiling FFmpeg from source..."
# Fall back to the GitHub mirror if git.ffmpeg.org is unreachable.
git clone --depth 1 https://git.ffmpeg.org/ffmpeg.git "$WORK_DIR/ffmpeg_src" ||
    git clone --depth 1 https://github.com/FFmpeg/FFmpeg.git "$WORK_DIR/ffmpeg_src"

# Minimal shared build: only the required encoders/muxers stay enabled (smaller
# binary), and --enable-shared/--disable-static so the libs can be bundled later.
cd "$WORK_DIR/ffmpeg_src"
./configure \
    --prefix="$WORK_DIR/ffmpeg-install" \
    --extra-cflags="-I$DEPS_PREFIX/include" \
    --extra-ldflags="-L$DEPS_PREFIX/lib" \
    --enable-gpl \
    --enable-shared \
    --disable-static \
    --enable-libx264 \
    --enable-libvpx \
    --enable-libopus \
    --enable-libsvtav1 \
    --enable-libdav1d \
    --enable-libwebp \
    --disable-encoders \
    --enable-encoder="$(configure_list "$REQUIRED_ENCODERS")" \
    --disable-muxers \
    --enable-muxer="$(configure_list "$REQUIRED_MUXERS")" \
    --disable-debug \
    --disable-doc
make -j"$(nproc)"
make install

# Final layout: binaries in $TOOLS_DIR, shared libs in $DEPS_PREFIX/lib --
# the dir build-appimage.sh's DEP_SEARCH_PATHS points at.
mkdir -p "$DEPS_PREFIX/lib"
mv "$WORK_DIR/ffmpeg-install/bin/ffmpeg" "$TOOLS_DIR/ffmpeg"
mv "$WORK_DIR/ffmpeg-install/bin/ffprobe" "$TOOLS_DIR/ffprobe"
mv "$WORK_DIR/ffmpeg-install/lib/"*.so* "$DEPS_PREFIX/lib/"
chmod +x "$TOOLS_DIR/ffmpeg" "$TOOLS_DIR/ffprobe"
verify_ffmpeg "$TOOLS_DIR/ffmpeg" "$DEPS_PREFIX/lib"

echo "Built ffmpeg and ffprobe in $TOOLS_DIR (shared libraries in $DEPS_PREFIX/lib)."
