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
            tmp_out="${file}.tmp.pdf"
            compressed=0

            # Tier 1: Ghostscript aggressive downsampling (100 DPI)
            if command -v gs &> /dev/null; then
                echo "Attempting Tier 1 (Ghostscript aggressive downsampling)..."
                gs -sDEVICE=pdfwrite \
                   -dCompatibilityLevel=1.4 \
                   -dNOPAUSE -dBATCH -dQUIET \
                   -dDownsampleColorImages=true \
                   -dColorImageResolution=100 \
                   -dColorImageDownsampleType=/Bicubic \
                   -dDownsampleGrayImages=true \
                   -dGrayImageResolution=100 \
                   -dDownsampleMonoImages=true \
                   -dMonoImageResolution=100 \
                   -sOutputFile="$tmp_out" "$file" > /dev/null 2>&1

                new_size_bytes=$(stat -c%s "$tmp_out" 2>/dev/null || echo 999999999)
                if [ "$new_size_bytes" -le "$MAX_BYTES" ] && [ "$new_size_bytes" -lt "$orig_size_bytes" ]; then
                    compressed=1
                else
                    echo "Tier 1 result: $(du -h "$tmp_out" 2>/dev/null | cut -f1) (exceeds ${MAX_SIZE_MB}MB)."
                fi
            fi

            # Tier 2: pdftoppm + img2pdf fallback (120 DPI JPEG rasterization)
            if [ "$compressed" -eq 0 ] && command -v pdftoppm &> /dev/null && command -v img2pdf &> /dev/null; then
                echo "Attempting Tier 2 (pdftoppm + img2pdf rasterization)..."
                tmp_dir=$(mktemp -d)
                pdftoppm -jpeg -r 120 -jpegopt quality=75 "$file" "$tmp_dir/page" > /dev/null 2>&1
                img2pdf "$tmp_dir"/*.jpg -o "$tmp_out" > /dev/null 2>&1
                rm -rf "$tmp_dir"

                new_size_bytes=$(stat -c%s "$tmp_out" 2>/dev/null || echo 999999999)
                if [ "$new_size_bytes" -le "$MAX_BYTES" ] && [ "$new_size_bytes" -lt "$orig_size_bytes" ]; then
                    compressed=1
                else
                    echo "Tier 2 result: $(du -h "$tmp_out" 2>/dev/null | cut -f1) (exceeds ${MAX_SIZE_MB}MB)."
                fi
            fi

            # Apply compressed file or fallback to .cloudflareignore
            if [ "$compressed" -eq 1 ]; then
                mv "$tmp_out" "$file"
                echo "Compressed: $file -> $(du -h "$file" | cut -f1)"
            else
                rm -f "$tmp_out"
                echo "Unable to compress $file under ${MAX_SIZE_MB}MB."

                # Exclude file from Cloudflare build as last resort
                ignore_path="${file#public-pages/}"
                if ! grep -qF "$ignore_path" .cloudflareignore 2>/dev/null; then
                    echo "$ignore_path" >> .cloudflareignore
                    echo "Added $ignore_path to .cloudflareignore"
                fi
            fi
            ;;

        png|jpg|jpeg)
            if command -v magick &> /dev/null; then
                magick "$file" -resize 75% -quality 70 "$file"
                echo "Compressed image: $file -> $(du -h "$file" | cut -f1)"
            elif command -v convert &> /dev/null; then
                convert "$file" -resize 75% -quality 70 "$file"
                echo "Compressed image: $file -> $(du -h "$file" | cut -f1)"
            fi
            ;;
    esac
done

echo "Scan complete."
