#!/bin/bash
# PPTX → 슬라이드별 PNG (검수용). 사용: bash scripts/render_pptx.sh <파일.pptx> [출력디렉터리] [dpi]
# 요구: LibreOffice(brew install --cask libreoffice) + python3 -m pip install pymupdf --break-system-packages
set -e
SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
PPTX="${1:-SSGI_상세기획서_심사위원용.pptx}"
OUT="${2:-render_out}"
DPI="${3:-130}"
mkdir -p "$OUT"
TMP_PPTX="/tmp/_render_$$.pptx"
cp "$PPTX" "$TMP_PPTX"
"$SOFFICE" --headless --convert-to pdf --outdir /tmp "$TMP_PPTX" >/dev/null 2>&1
PDF="/tmp/_render_$$.pdf"
python3 - "$PDF" "$OUT" "$DPI" <<'PY'
import sys, fitz
pdf, out, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = fitz.open(pdf)
for i, pg in enumerate(d):
    pg.get_pixmap(dpi=dpi).save(f"{out}/s{i+1:02d}.png")
print(f"{len(d)} slides → {out}/s01..s{len(d):02d}.png @ {dpi}dpi")
PY
rm -f "$TMP_PPTX" "$PDF"
