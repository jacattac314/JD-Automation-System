#!/usr/bin/env python3
"""
SVG Icon Generator for JD Automation System

Generates SVG placeholder icons that can be converted to PNG.
No dependencies required!

To convert to PNG:
  - Use ImageMagick: convert icon.svg -resize 512x512 icon.png
  - Use Inkscape: inkscape icon.svg --export-png=icon.png -w 512 -h 512
  - Use online tool: https://convertio.co/svg-png/
  - Use browser: Open SVG, screenshot, crop in any image editor
"""

import os
from pathlib import Path

def create_svg_icon(size, text="JD"):
    """Create an SVG icon with gradient background and text."""
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background with rounded corners -->
  <rect width="{size}" height="{size}" rx="{size * 0.15}" ry="{size * 0.15}" fill="url(#gradient)"/>

  <!-- Text -->
  <text
    x="50%"
    y="50%"
    dominant-baseline="middle"
    text-anchor="middle"
    font-family="Arial, Helvetica, sans-serif"
    font-size="{size * 0.4}"
    font-weight="bold"
    fill="#ffffff"
    filter="url(#shadow)">
    {text}
  </text>
</svg>'''
    return svg

def save_svg_icon(size, output_path, text="JD"):
    """Save SVG icon to file."""
    svg_content = create_svg_icon(size, text)
    output_path.write_text(svg_content)
    print(f"  ✓ Created {output_path.name}")
    return output_path

def create_desktop_icons():
    """Create desktop app icons as SVG."""
    print("\n📦 Creating Desktop Icons (SVG)...")

    desktop_dir = Path(__file__).parent.parent / "electron" / "assets"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    # Create SVG source
    svg_path = desktop_dir / "icon.svg"
    save_svg_icon(1024, svg_path, "JD")

    print(f"\n  📝 To create PNG:")
    print(f"     Open {svg_path} in a browser")
    print(f"     Take a screenshot or use online converter")
    print(f"     Save as: {desktop_dir}/icon.png (1024x1024)")

def create_pwa_icons():
    """Create PWA icons as SVG."""
    print("\n📱 Creating PWA Icons (SVG)...")

    pwa_dir = Path(__file__).parent.parent / "ui" / "icons"
    pwa_dir.mkdir(parents=True, exist_ok=True)

    # Create master SVG
    master_svg = pwa_dir / "icon-master.svg"
    save_svg_icon(512, master_svg, "JD")

    # Create shortcut SVGs
    print("\n🔗 Creating Shortcut Icons (SVG)...")
    shortcuts = [
        ("shortcut-new.svg", "N"),
        ("shortcut-history.svg", "H"),
        ("shortcut-settings.svg", "S"),
    ]

    for filename, letter in shortcuts:
        save_svg_icon(96, pwa_dir / filename, letter)

    print(f"\n  📝 To create PNG icons:")
    print(f"     Use online tool: https://cloudconvert.com/svg-to-png")
    print(f"     Or install ImageMagick and run:")
    print(f"       cd {pwa_dir}")
    print(f"       for size in 72 96 128 144 152 192 384 512; do")
    print(f"         convert icon-master.svg -resize ${{size}}x${{size}} icon-${{size}}x${{size}}.png")
    print(f"       done")

def create_auto_converter():
    """Create a bash script to auto-convert SVG to PNG if ImageMagick is available."""
    print("\n🔧 Creating auto-converter script...")

    script_content = '''#!/bin/bash
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
'''

    script_path = Path(__file__).parent.parent / "scripts" / "convert-icons.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)

    print(f"  ✓ Created {script_path.name}")
    print(f"  Run with: ./scripts/convert-icons.sh")

def create_readme():
    """Create icon guide."""
    content = '''# Icon Guide

## Quick Start

### Option 1: Use Generated SVG Icons (Recommended for testing)

SVG icons have been created in:
- Desktop: `electron/assets/icon.svg`
- PWA: `ui/icons/*.svg`

**Convert to PNG:**

1. **Using ImageMagick (Automated):**
   ```bash
   ./scripts/convert-icons.sh
   ```

2. **Using Online Tool:**
   - Go to https://cloudconvert.com/svg-to-png
   - Upload SVG files
   - Download PNG versions
   - Place in correct folders

3. **Using Browser:**
   - Open SVG in browser
   - Take screenshot
   - Crop and save as PNG

### Option 2: Create Custom Icons (Recommended for production)

**Best Tools:**
- **Figma** (Free): https://figma.com
- **Canva** (Free): https://canva.com
- **Adobe Illustrator** (Paid)

**Design Tips:**
- Keep it simple and recognizable
- Use your brand colors
- Test at small sizes (16x16)
- Use high contrast
- Avoid fine details

**Required Sizes:**

Desktop (Electron):
- `electron/assets/icon.png` - 1024x1024
  (electron-builder auto-generates .ico and .icns)

PWA:
- `ui/icons/icon-72x72.png`
- `ui/icons/icon-96x96.png`
- `ui/icons/icon-128x128.png`
- `ui/icons/icon-144x144.png`
- `ui/icons/icon-152x152.png`
- `ui/icons/icon-192x192.png`
- `ui/icons/icon-384x384.png`
- `ui/icons/icon-512x512.png`

Shortcuts (Optional):
- `ui/icons/shortcut-new.png` - 96x96
- `ui/icons/shortcut-history.png` - 96x96
- `ui/icons/shortcut-settings.png` - 96x96

### Option 3: Use Icon Generator Websites

1. **RealFaviconGenerator** (Recommended)
   - https://realfavicongenerator.net/
   - Upload one image, get all sizes
   - Automatically generates correct formats

2. **PWA Builder**
   - https://www.pwabuilder.com/imageGenerator
   - Specifically for PWA icons

3. **Favicon.io**
   - https://favicon.io/
   - Generate from text, emoji, or image

## Verification

After adding icons, verify:

```bash
# Check desktop icon exists
ls -lh electron/assets/icon.png

# Check PWA icons exist
ls -lh ui/icons/*.png

# Build and test
npm run build
```

## Tips

- **File Format:** PNG with transparency
- **Background:** Include background color (not transparent for app icons)
- **Safety Area:** Keep important elements within 80% of center
- **Testing:** Test icons at actual size (especially 16x16, 32x32)
- **Consistency:** Use same design across all sizes

## Current Status

Run `python3 scripts/generate-icons-svg.py` to create placeholder SVG icons.
Then convert them to PNG or replace with your custom designs.
'''

    readme_path = Path(__file__).parent.parent / "electron" / "assets" / "ICON_GUIDE.md"
    readme_path.write_text(content)
    print(f"\n  ✓ Created {readme_path.name}")

def main():
    """Main function."""
    print("=" * 70)
    print("  JD Automation System - SVG Icon Generator")
    print("=" * 70)

    try:
        create_desktop_icons()
        create_pwa_icons()
        create_auto_converter()
        create_readme()

        print("\n" + "=" * 70)
        print("✓ SVG icons created successfully!")
        print("=" * 70)
        print("\n📝 Next Steps:")
        print("  1. Convert SVG to PNG:")
        print("     • Run: ./scripts/convert-icons.sh (if ImageMagick installed)")
        print("     • Or use: https://cloudconvert.com/svg-to-png")
        print("     • Or replace with custom icons")
        print()
        print("  2. Verify icons:")
        print("     • Desktop: electron/assets/icon.png (1024x1024)")
        print("     • PWA: ui/icons/*.png (various sizes)")
        print()
        print("  3. Build your app:")
        print("     npm run build")
        print()
        print("💡 For production, create custom icons with:")
        print("   • Figma: https://figma.com")
        print("   • Canva: https://canva.com")
        print("   • Or use: https://realfavicongenerator.net/")
        print()
        print("📖 Full guide: electron/assets/ICON_GUIDE.md")

        return 0

    except Exception as e:
        print(f"\n❌ Error creating icons: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
