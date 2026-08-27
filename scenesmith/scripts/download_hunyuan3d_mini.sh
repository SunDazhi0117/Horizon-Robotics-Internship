#!/usr/bin/env bash
set -euo pipefail

model_dir="$HOME/.cache/hy3dgen/tencent/Hunyuan3D-2mini/hunyuan3d-dit-v2-mini-turbo"
mirror_root="https://hf-mirror.com/tencent/Hunyuan3D-2mini/resolve/main/hunyuan3d-dit-v2-mini-turbo"
model_name="model.fp16.safetensors"
expected_sha256="bdbcef30dd0149a281e17d5b5b1fdad1122c904e098a42f3100e04e03c247bc4"

command -v aria2c >/dev/null || {
  echo "aria2c is required for resumable model downloads." >&2
  exit 1
}

mkdir -p "$model_dir"

env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  curl --fail --location --retry 5 --retry-all-errors \
  --output "$model_dir/config.yaml" "$mirror_root/config.yaml"

env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  aria2c \
  --continue=true \
  --split=8 \
  --max-connection-per-server=8 \
  --min-split-size=16M \
  --max-tries=20 \
  --retry-wait=3 \
  --timeout=30 \
  --connect-timeout=15 \
  --dir="$model_dir" \
  --out="$model_name" \
  "$mirror_root/$model_name"

printf '%s  %s\n' "$expected_sha256" "$model_dir/$model_name" | sha256sum --check -
