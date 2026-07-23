#!/usr/bin/env bash

ASSETS_DIR="assets"
MAX_SIZE_MB=24
MAX_BYTES=$((MAX_SIZE_MB * 1024 * 1024))

# Fallback check for nested export folder structure
if [ ! -d "$ASSETS_DIR" ] && [ -d "public-pages/assets" ]; then
    ASSETS_DIR="public-pages/assets"
fi

if [ ! -d "$ASSETS_DIR" ]; then
    echo "Error: Directory '$ASSETS_DIR' not found."
    exit 1
fi

echo "Scanning '$ASSETS_DIR' for files > ${MAX_SIZE_MB}MB..."

find "$ASSETS_DIR" -type f -size +${MAX_SIZE_MB}M | while read -r file; do
    orig_size_bytes=$(stat -c%s "$file")
    orig_size_h=$(du -h "$file" | cut -f1)
    echo "Found large file: $file ($orig_size_h)"

    ext="${file##*.}"
    ext_lc=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    case "$ext_lc" in
        pdf)
            if command -v gs &> /dev/null; then
                tmp_out="${file}.tmp.pdf"

                # Attempt 1: /ebook (150 DPI)
                echo "Compressing PDF (preset: /ebook)..."
                gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
                   -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$tmp_out" "$file" > /dev/null 2>&1

                new_size_bytes=$(stat -c%s "$tmp_out" 2>/dev/null || echo 999999999)

                # Attempt 2: If /ebook inflated or is still > 24MB, try /screen (72 DPI)
                if [ "$new_size_bytes" -ge "$orig_size_bytes" ] || [ "$new_size_bytes" -gt "$MAX_BYTES" ]; then
                    echo "/ebook yielded $(du -h "$tmp_out" 2>/dev/null | cut -f1). Retrying with /screen..."
                    gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
                       -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$tmp_out" "$file" > /dev/null 2>&1
                    new_size_bytes=$(stat -c%s "$tmp_out" 2>/dev/null || echo 999999999)
                fi

                # Check if result is smaller AND fits Cloudflare's limit
                if [ "$new_size_bytes" -lt "$orig_size_bytes" ] && [ "$new_size_bytes" -le "$MAX_BYTES" ]; then
                    mv "$tmp_out" "$file"
                    echo "Compressed: $file -> $(du -h "$file" | cut -f1)"
                else
                    rm -f "$tmp_out"
                    echo "Unable to compress $file under ${MAX_SIZE_MB}MB."

                    # Exclude file from Cloudflare build to avoid upload error
                    ignore_path="${file#public-pages/}"
                    if ! grep -qF "$ignore_path" .cloudflareignore 2>/dev/null; then
                        echo "$ignore_path" >> .cloudflareignore
                        echo "Added $ignore_path to .cloudflareignore"
                    fi
                fi
            else
                echo "Error: Ghostscript ('gs') is not installed."
            fi
            ;;

        png|jpg|jpeg)
            if command -v magick &> /dev/null; then
                magick "$file" -resize 80% -quality 75 "$file"
                echo "Compressed image: $file -> $(du -h "$file" | cut -f1)"
            elif command -v convert &> /dev/null; then
                convert "$file" -resize 80% -quality 75 "$file"
                echo "Compressed image: $file -> $(du -h "$file" | cut -f1)"
            fi
            ;;
    esac
done

echo "Scan complete."
