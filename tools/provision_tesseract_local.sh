#!/usr/bin/env bash
# =============================================================================
# CarbonTally — local Tesseract OCR runtime provisioning (no root required)
#
# pytesseract needs the `tesseract` binary on PATH (or at $TESSERACT_CMD) plus
# its shared libraries. This script downloads the Ubuntu .debs and extracts
# them into a local prefix, then emits a small env-file you can source.
#
# WHY NOT `apt-get install`? The dev/test boxes may not grant sudo. Extracting
# the .deb payloads into a user prefix is reproducible and needs no privileges.
#
# Usage:
#   bash tools/provision_tesseract_local.sh [target_root]
#   source "$(dirname "$0")/tesseract-env.sh"   # or: source <prefix>/tesseract-env.sh
#
# Environment variables produced:
#   TESSERACT_CMD      pytesseract binary path (consumed by backend/pdf_engine.py)
#   TESSDATA_PREFIX    tessdata directory (eng.traineddata)
#   LD_LIBRARY_PATH    libtesseract5 + libleptonica shared libraries
#
# For container/Render provisioning the equivalent apt steps are:
#   apt-get update && apt-get install -y --no-install-recommends \
#       tesseract-ocr tesseract-ocr-eng libtesseract5 poppler-utils
# =============================================================================
set -euo pipefail

PREFIX="${1:-/tmp/ct_tess}"
DEBS="$PREFIX/debs"
ROOT="$PREFIX/root"

mkdir -p "$DEBS" "$ROOT"

echo "[1/3] Downloading tesseract .debs into $DEBS"
cd "$DEBS"
apt-get download tesseract-ocr libtesseract5 libleptonica6 tesseract-ocr-eng

echo "[2/3] Extracting into $ROOT"
for f in "$DEBS"/*.deb; do
  dpkg-deb -x "$f" "$ROOT"
done

BIN="$ROOT/usr/bin/tesseract"
TESSDATA="$ROOT/usr/share/tesseract-ocr/5/tessdata"
LIBS="$ROOT/usr/lib/x86_64-linux-gnu"

if [ ! -x "$BIN" ]; then
  echo "ERROR: tesseract binary not found after extraction" >&2
  exit 1
fi
if [ ! -f "$TESSDATA/eng.traineddata" ]; then
  echo "ERROR: eng.traineddata not found after extraction" >&2
  exit 1
fi

echo "[3/3] Writing $PREFIX/tesseract-env.sh"
cat > "$PREFIX/tesseract-env.sh" <<EOF
# Source this file to make tesseract available to the CarbonTally backend:
#   source "$PREFIX/tesseract-env.sh"
export TESSERACT_CMD="$BIN"
export TESSDATA_PREFIX="$TESSDATA"
export LD_LIBRARY_PATH="$LIBS\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
EOF

echo
echo "Provisioned. Verify with:"
echo "  source $PREFIX/tesseract-env.sh"
echo "  tesseract --version"
echo "  TESSDATA_PREFIX='$TESSDATA' LD_LIBRARY_PATH='$LIBS' '$BIN' --version"
