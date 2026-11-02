#!/usr/bin/env bash
# Build FFmpeg tối giản (chỉ các codec / bộ lọc app dùng) để bản phát hành nhẹ:
# ~4-6 MB thay vì ~80 MB của bản FFmpeg đầy đủ trong imageio-ffmpeg.
#
# Dùng:   packaging/build_ffmpeg.sh <linux|windows> <thư_mục_đầu_ra>
# Cần (Ubuntu 22.04+): build-essential nasm pkg-config curl xz-utils
#                      + gcc-mingw-w64-x86-64 binutils-mingw-w64-x86-64 mingw-w64-x86-64-dev khi build cho windows
set -euo pipefail

TARGET=${1:?target: linux | windows}
OUT=$(realpath -m "${2:?output directory}")
WORK=${WORK_DIR:-$(mktemp -d)}
JOBS=$(nproc)

FFMPEG_VERSION=8.1.3
FFMPEG_SHA256=7138d28c96d9d3e3af4ee3d8cad72741f8ffb40da90c1112235dea3ecd3178a3
LAME_VERSION=3.100
LAME_SHA256=ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e
ZLIB_VERSION=1.3.1
ZLIB_SHA256=9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23

case "$TARGET" in
  linux)
    HOST=""
    CROSS_ARGS=()
    EXE=ffmpeg
    ;;
  windows)
    HOST=x86_64-w64-mingw32
    CROSS_ARGS=(--arch=x86_64 --target-os=mingw32 --cross-prefix="$HOST-")
    EXE=ffmpeg.exe
    ;;
  *)
    echo "Unknown target: $TARGET" >&2
    exit 1
    ;;
esac

PREFIX="$WORK/prefix-$TARGET"
mkdir -p "$WORK" "$PREFIX" "$OUT"
cd "$WORK"

fetch() {  # fetch <url> <file> <sha256>
  [ -f "$2" ] || curl -fsSL --retry 3 -o "$2" "$1"
  echo "$3  $2" | sha256sum -c -
}

# --- zlib (giải mã ảnh bìa PNG) ---
fetch "https://github.com/madler/zlib/releases/download/v$ZLIB_VERSION/zlib-$ZLIB_VERSION.tar.gz" \
      "zlib-$ZLIB_VERSION.tar.gz" "$ZLIB_SHA256"
rm -rf "zlib-$ZLIB_VERSION" && tar xf "zlib-$ZLIB_VERSION.tar.gz"
(
  cd "zlib-$ZLIB_VERSION"
  CHOST=$HOST CFLAGS="-O2" ./configure --prefix="$PREFIX" --static
  make -j"$JOBS" && make install
)

# --- LAME (bộ mã hóa MP3) ---
fetch "https://downloads.sourceforge.net/project/lame/lame/$LAME_VERSION/lame-$LAME_VERSION.tar.gz" \
      "lame-$LAME_VERSION.tar.gz" "$LAME_SHA256"
rm -rf "lame-$LAME_VERSION" && tar xf "lame-$LAME_VERSION.tar.gz"
(
  cd "lame-$LAME_VERSION"
  ./configure --prefix="$PREFIX" ${HOST:+--host=$HOST} --disable-shared --enable-static \
              --disable-frontend --disable-decoder --disable-gtktest CFLAGS="-O2"
  make -j"$JOBS" && make install
)

# --- FFmpeg ---
fetch "https://ffmpeg.org/releases/ffmpeg-$FFMPEG_VERSION.tar.xz" "ffmpeg-$FFMPEG_VERSION.tar.xz" "$FFMPEG_SHA256"
rm -rf "ffmpeg-$FFMPEG_VERSION" && tar xf "ffmpeg-$FFMPEG_VERSION.tar.xz"
cd "ffmpeg-$FFMPEG_VERSION"

join() { local IFS=,; echo "$*"; }

# Đọc: âm thanh từ YouTube / Facebook / TikTok / SoundCloud và file người dùng thêm vào trình cắt ghép
DEMUXERS=(mov matroska mp3 aac flac wav ogg asf mpegts image2 image_jpeg_pipe image_png_pipe image_webp_pipe
          ffmetadata pcm_s16le rawvideo)
DECODERS=(aac aac_latm mp3 mp3float mp2 mp2float flac vorbis opus alac wmav1 wmav2 ac3
          pcm_s16le pcm_s16be pcm_s24le pcm_s32le pcm_f32le pcm_u8 mjpeg png webp h264 rawvideo)
PARSERS=(aac aac_latm mpegaudio flac opus vorbis ac3 mjpeg png webp h264 hevc vp8 vp9 av1)
# Ghi: MP3 / M4A / WAV / FLAC, ảnh bìa JPEG, PCM thô để vẽ dạng sóng
# (opus + webm, đọc pcm_s16le / rawvideo chỉ để `--check` tự tạo dữ liệu thử giống nguồn YouTube)
ENCODERS=(libmp3lame aac flac pcm_s16le mjpeg opus)
MUXERS=(mp3 ipod mp4 adts flac wav pcm_s16le image2 webm null)
FILTERS=(aresample aformat asetnsamples anull concat acrossfade afade volume loudnorm crop scale format null)
# Các bộ lọc bitstream yt-dlp dùng khi chuyển AAC sang M4A, tạo ảnh bìa JPEG, sửa mốc thời gian
BSFS=(aac_adtstoasc mjpeg2jpeg setts)
PROTOCOLS=(file pipe)

# configure bỏ qua im lặng tên thành phần sai: kiểm tra trước để không âm thầm thiếu tính năng
check_names() {  # check_names <loại> <tên...>
  local kind=$1 available
  shift
  available=$(./configure --list-"$kind" | tr -s ' \t' '\n')
  for name in "$@"; do
    grep -qx "$name" <<<"$available" || { echo "Unknown FFmpeg $kind: $name" >&2; exit 1; }
  done
}
check_names demuxers "${DEMUXERS[@]}"
check_names decoders "${DECODERS[@]}"
check_names parsers "${PARSERS[@]}"
check_names encoders "${ENCODERS[@]}"
check_names muxers "${MUXERS[@]}"
check_names filters "${FILTERS[@]}"
check_names bsfs "${BSFS[@]}"
check_names protocols "${PROTOCOLS[@]}"

./configure \
  "${CROSS_ARGS[@]}" \
  --prefix="$PREFIX" \
  --pkg-config-flags=--static \
  --extra-cflags="-I$PREFIX/include" \
  --extra-ldflags="-L$PREFIX/lib -static" \
  --extra-libs="-lm" \
  --enable-static --disable-shared \
  --enable-small \
  --disable-autodetect --enable-zlib --enable-libmp3lame \
  --disable-everything \
  --disable-doc --disable-debug --disable-network \
  --disable-ffplay --disable-ffprobe --disable-avdevice \
  --enable-protocol="$(join "${PROTOCOLS[@]}")" \
  --enable-demuxer="$(join "${DEMUXERS[@]}")" \
  --enable-decoder="$(join "${DECODERS[@]}")" \
  --enable-parser="$(join "${PARSERS[@]}")" \
  --enable-encoder="$(join "${ENCODERS[@]}")" \
  --enable-muxer="$(join "${MUXERS[@]}")" \
  --enable-filter="$(join "${FILTERS[@]}")" \
  --enable-bsf="$(join "${BSFS[@]}")"

make -j"$JOBS"
"${HOST:+$HOST-}strip" -o "$OUT/$EXE" "$EXE"
ls -la "$OUT/$EXE"
