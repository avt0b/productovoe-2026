#!/bin/sh
# Обновляет шрифты в public/fonts.
#
# Material Symbols качается сабсетом — только иконки из scripts/icon-names.txt
# (полный шрифт весит 4 МБ, сабсет — около 170 КБ). Добавили в приложении новую
# иконку — допишите её имя в список и прогоните скрипт заново.
set -e
cd "$(dirname "$0")/.."
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
mkdir -p public/fonts

NAMES=$(cat scripts/icon-names.txt)
CSS=$(curl -s -G --data-urlencode "icon_names=$NAMES" \
  --data-urlencode "family=Material Symbols Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" \
  --data-urlencode "display=block" -A "$UA" "https://fonts.googleapis.com/css2")
URL=$(printf '%s' "$CSS" | grep -o "https://fonts.gstatic.com[^)]*" | head -1)
case "$URL" in
  *"/l/font"*) ;;
  *) echo "Google отдал полный шрифт, а не сабсет — проверьте scripts/icon-names.txt" >&2; exit 1 ;;
esac
curl -s -A "$UA" -o public/fonts/material-symbols-outlined.woff2 "$URL"

# Manrope — переменное начертание 400..800, по подмножествам Unicode.
MANROPE=$(curl -s -A "$UA" "https://fonts.googleapis.com/css2?family=Manrope:wght@400..800&display=swap")
for subset in cyrillic cyrillic-ext latin latin-ext; do
  URL=$(printf '%s' "$MANROPE" | awk -v s="/* $subset */" 'index($0, s){found=1} found && /fonts.gstatic.com/{print; exit}' | grep -o "https://[^)]*")
  curl -s -A "$UA" -o "public/fonts/manrope-$subset.woff2" "$URL"
done

ls -l public/fonts
