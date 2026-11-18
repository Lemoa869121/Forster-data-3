#!/bin/bash
# Usage : scripts/ocr_pdf.sh <fichier.pdf> [dossier_sortie]   (requiert poppler-utils + tesseract-ocr-fra)
# Lot : ls PV/*.pdf | xargs -d "\n" -I{} -P 2 scripts/ocr_pdf.sh "{}" ocr_txt
# OCR d'un PDF : texte natif par page si présent, sinon tesseract (fra, 200 dpi). Sortie : pages séparées par \f
f="$1"; b=$(basename "$f" .pdf); outdir="${2:-ocr_txt}"; mkdir -p "$outdir"; out="$outdir/$b.txt"
[ -s "$out" ] && exit 0
tmp=$(mktemp -d); n=$(pdfinfo "$f" 2>/dev/null | awk '/^Pages/{print $2}')
for ((p=1;p<=n;p++)); do
  t=$(pdftotext -layout -f $p -l $p "$f" - 2>/dev/null)
  if [ $(echo "$t" | tr -d '[:space:]' | wc -c) -gt 300 ]; then echo "$t" > "$tmp/$p.txt"
  else pdftoppm -r 200 -gray -f $p -l $p -png "$f" "$tmp/img" >/dev/null 2>&1
       img=$(ls "$tmp"/img*.png 2>/dev/null | head -1)
       if [ -n "$img" ]; then tesseract "$img" - -l fra 2>/dev/null > "$tmp/$p.txt"; rm -f "$tmp"/img*.png; else echo "" > "$tmp/$p.txt"; fi
  fi
done
for ((p=1;p<=n;p++)); do cat "$tmp/$p.txt"; printf '\f'; done > "$out.part" && mv "$out.part" "$out"
rm -rf "$tmp"; echo "ok $b $n"
