# Icon Guide

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
