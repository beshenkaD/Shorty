# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first (cached separately from the project's own code).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY pyproject.toml uv.lock README.md LICENCE ./
COPY src ./src

# Non-editable: the runtime stage copies only the venv, not /app/src.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


# yt-dlp only uses ffmpeg to remux/merge with stream copy, so build a static ffmpeg with
# every container, parser and bitstream filter but no codecs or external libraries.
# Debian's ffmpeg package drags in hundreds of MB of codec and GPU libraries instead.
FROM debian:bookworm-slim AS ffmpeg

ARG FFMPEG_VERSION=7.1.1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN curl -fsSL "https://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.xz" \
    | tar -xJ --strip-components=1

# Decoders are only for probing: MPEG-TS (HLS) streams don't store sample rate/dimensions
# in the container, so remuxing them to mp4 fails without them.
RUN ./configure \
        --prefix=/opt/ffmpeg \
        --enable-static --disable-shared --extra-ldflags=-static \
        --disable-autodetect --disable-debug --disable-doc --disable-network \
        --disable-x86asm --disable-ffplay --disable-everything \
        --enable-ffmpeg --enable-ffprobe \
        --enable-protocol=file,pipe \
        --enable-demuxers --enable-muxers --enable-parsers --enable-bsfs \
        --enable-decoder=aac,aac_latm,mp3,opus,vorbis,flac,ac3,eac3,h264,hevc,vp8,vp9,av1 \
    && make -j"$(nproc)" \
    && make install \
    && strip /opt/ffmpeg/bin/ffmpeg /opt/ffmpeg/bin/ffprobe


FROM python:3.12-slim-bookworm

# yt-dlp writes its cache under XDG_CACHE_HOME; the app user has no home directory.
ENV PATH="/app/.venv/bin:$PATH" \
    XDG_CACHE_HOME=/tmp/.cache

RUN groupadd --system app && useradd --system --gid app app

COPY --from=ffmpeg /opt/ffmpeg/bin/ffmpeg /opt/ffmpeg/bin/ffprobe /usr/local/bin/

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

USER app

CMD ["shorty-bot"]
