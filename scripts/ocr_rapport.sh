#!/bin/bash
# Texte natif par page ; OCR (fra+deu+eng, 200 dpi) seulement pour les 6 premières et 2 dernières pages sans texte.
f="$1"; outdir="$2"; rel="${f#./}"; b=$(echo "$rel" | sed 's#/#__#g; s#\.[pP][dD][fF]$##'); out="$outdir/$b.txt"
[ -s "$out" ] && exit 0
tmp=$(mktemp -d); n=$(pdfinfo "$f" 2>/dev/null | awk '/^Pages/{print $2}'); n=${n:-0}
for ((p=1;p<=n;p++)); do
  t=$(pdftotext -layout -f $p -l $p "$f" - 2>/dev/null)
  if [ $(echo "$t" | tr -d '[:space:]' | wc -c) -gt 200 ]; then echo "$t" > "$tmp/$p.txt"
  elif [ $p -le 6 ] || [ $p -gt $((n-2)) ]; then
       pdftoppm -r 200 -gray -f $p -l $p -png "$f" "$tmp/img" >/dev/null 2>&1
       img=$(ls "$tmp"/img*.png 2>/dev/null | head -1)
       if [ -n "$img" ]; then tesseract "$img" - -l fra+deu+eng 2>/dev/null > "$tmp/$p.txt"; rm -f "$tmp"/img*.png; else : > "$tmp/$p.txt"; fi
  else echo "[[page non OCRisée]]" > "$tmp/$p.txt"; fi
done
for ((p=1;p<=n;p++)); do cat "$tmp/$p.txt"; printf '\f'; done > "$out.part" && mv "$out.part" "$out"
rm -rf "$tmp"
