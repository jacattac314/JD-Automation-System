#!/bin/bash
# Auto-convert SVG icons to PNG using ImageMagick

set -e

if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick not installed"
    echo "Install with:"
    echo "  macOS: brew install imagemagick"
    echo "  Ubuntu: sudo apt install imagemagick"
    echo "  Fedora: sudo dnf install imagemagick"
    exit 1
fi

echo "Converting Desktop Icon..."
cd electron/assets
if [ -f icon.svg ]; then
    convert icon.svg -resize 1024x1024 icon.png
    echo "✓ Created icon.png (1024x1024)"
fi

echo ""
echo "Converting PWA Icons..."
cd ../../ui/icons

if [ -f icon-master.svg ]; then
    for size in 72 96 128 144 152 192 384 512; do
        convert icon-master.svg -resize ${size}x${size} icon-${size}x${size}.png
        echo "✓ Created icon-${size}x${size}.png"
    done
fi

# Convert shortcuts
for file in shortcut-*.svg; do
    if [ -f "$file" ]; then
        name="${file%.svg}"
        convert "$file" -resize 96x96 "${name}.png"
        echo "✓ Created ${name}.png"
    fi
done

cd ../..
echo ""
echo "✓ All icons converted successfully!"
echo "Icons are ready for building the app."
