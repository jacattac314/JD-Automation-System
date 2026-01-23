#!/usr/bin/env python3
"""
Icon Generator for JD Automation System

Generates placeholder icons for both Desktop (Electron) and PWA.
Replace these with your custom icons later.

Requirements:
    pip install Pillow
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Colors matching the app theme
BG_COLOR = '#6366f1'  # Indigo (accent color)
TEXT_COLOR = '#ffffff'
GRADIENT_START = '#6366f1'
GRADIENT_END = '#8b5cf6'

def create_gradient_background(size):
    """Create a gradient background image."""
    image = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(image)

    # Create gradient
    for y in range(size):
        # Calculate color for this row
        ratio = y / size
        r = int(99 + (139 - 99) * ratio)
        g = int(102 + (92 - 102) * ratio)
        b = int(241 + (246 - 241) * ratio)

        draw.line([(0, y), (size, y)], fill=(r, g, b))

    return image

def create_icon(size, output_path, text="JD"):
    """Create a single icon with text."""
    print(f"  Creating {size}x{size} icon...")

    # Create gradient background
    img = create_gradient_background(size)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    try:
        # Try different font paths for different systems
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]

        font_size = int(size * 0.4)
        font = None

        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break

        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # Draw text in center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size - text_width) // 2, (size - text_height) // 2 - int(size * 0.05))

    # Draw shadow for depth
    shadow_offset = int(size * 0.01)
    draw.text((position[0] + shadow_offset, position[1] + shadow_offset),
              text, fill=(0, 0, 0, 128), font=font)

    # Draw main text
    draw.text(position, text, fill=TEXT_COLOR, font=font)

    # Add rounded corners for modern look (for larger icons)
    if size >= 512:
        # Create a mask for rounded corners
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        radius = int(size * 0.15)
        mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=255)

        # Apply mask
        img.putalpha(mask)

    # Save
    img.save(output_path, 'PNG')
    return output_path

def create_desktop_icons():
    """Create desktop app icons."""
    print("\n📦 Creating Desktop Icons...")

    desktop_dir = Path(__file__).parent.parent / "electron" / "assets"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    # Create main icon (1024x1024) - will be resized by electron-builder
    icon_path = desktop_dir / "icon.png"
    create_icon(1024, icon_path, "JD")

    print(f"✓ Desktop icon created: {icon_path}")
    print(f"  electron-builder will auto-generate .ico (Windows) and .icns (macOS)")

def create_pwa_icons():
    """Create PWA icons in multiple sizes."""
    print("\n📱 Creating PWA Icons...")

    pwa_dir = Path(__file__).parent.parent / "ui" / "icons"
    pwa_dir.mkdir(parents=True, exist_ok=True)

    # Required PWA icon sizes
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    for size in sizes:
        icon_path = pwa_dir / f"icon-{size}x{size}.png"
        create_icon(size, icon_path, "JD")

    print(f"✓ Created {len(sizes)} PWA icons in {pwa_dir}")

    # Create shortcut icons (smaller, single letter)
    print("\n🔗 Creating Shortcut Icons...")
    shortcuts = [
        ("shortcut-new.png", "N"),
        ("shortcut-history.png", "H"),
        ("shortcut-settings.png", "S"),
    ]

    for filename, letter in shortcuts:
        create_icon(96, pwa_dir / filename, letter)

    print(f"✓ Created {len(shortcuts)} shortcut icons")

def create_favicon():
    """Create favicon for web app."""
    print("\n🌐 Creating Favicon...")

    ui_dir = Path(__file__).parent.parent / "ui"

    # Create 32x32 favicon
    favicon_path = ui_dir / "favicon.ico"

    # Create multiple sizes for .ico
    sizes = [16, 32, 48]
    images = []

    for size in sizes:
        img = Image.new('RGB', (size, size))
        draw = ImageDraw.Draw(img)

        # Simple gradient background
        for y in range(size):
            ratio = y / size
            r = int(99 + (139 - 99) * ratio)
            g = int(102 + (92 - 102) * ratio)
            b = int(241 + (246 - 241) * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b))

        images.append(img)

    # Save as .ico with multiple sizes
    images[0].save(favicon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])

    # Also create a simple PNG favicon
    create_icon(32, ui_dir / "favicon.png", "JD")

    print(f"✓ Favicon created: {favicon_path}")

def main():
    """Main function."""
    print("=" * 60)
    print("  JD Automation System - Icon Generator")
    print("=" * 60)

    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("\n❌ Error: Pillow not installed")
        print("Install with: pip install Pillow")
        return 1

    try:
        # Create all icons
        create_desktop_icons()
        create_pwa_icons()
        create_favicon()

        print("\n" + "=" * 60)
        print("✓ All icons created successfully!")
        print("=" * 60)
        print("\n📝 Next Steps:")
        print("  1. (Optional) Replace generated icons with custom designs")
        print("  2. Build your app: npm run build")
        print("  3. Icons will be automatically included in installers")
        print("\n💡 Tips:")
        print("  - Use a design tool (Figma, Canva) for custom icons")
        print("  - Keep icons simple and recognizable at small sizes")
        print("  - Maintain consistent branding across all sizes")
        print("\n🎨 Recommended Tools:")
        print("  - https://realfavicongenerator.net/ - Generate all sizes")
        print("  - https://www.figma.com/ - Design custom icons")
        print("  - https://www.canva.com/ - Easy icon creation")

        return 0

    except Exception as e:
        print(f"\n❌ Error creating icons: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
