#!/usr/bin/env node
/**
 * SVG to PNG Converter
 *
 * Converts SVG icons to PNG format using Node.js
 * Requires: sharp package (npm install sharp)
 *
 * If sharp fails to install, you can:
 * 1. Use online converter: https://cloudconvert.com/svg-to-png
 * 2. Use ImageMagick: convert icon.svg icon.png
 * 3. Open SVG in browser and screenshot
 */

const fs = require('fs');
const path = require('path');

async function convertSvgToPng() {
    let sharp;

    try {
        sharp = require('sharp');
    } catch (error) {
        console.log('\n❌ Sharp package not installed');
        console.log('\nInstall with: npm install sharp');
        console.log('\nAlternatives:');
        console.log('  1. Online: https://cloudconvert.com/svg-to-png');
        console.log('  2. ImageMagick: convert icon.svg icon.png');
        console.log('  3. Browser: Open SVG, screenshot, save as PNG');
        process.exit(1);
    }

    console.log('='.repeat(70));
    console.log('  Converting SVG Icons to PNG');
    console.log('='.repeat(70));

    const projectRoot = path.join(__dirname, '..');

    // Convert desktop icon
    console.log('\n📦 Converting Desktop Icon...');
    const desktopSvg = path.join(projectRoot, 'electron', 'assets', 'icon.svg');
    const desktopPng = path.join(projectRoot, 'electron', 'assets', 'icon.png');

    if (fs.existsSync(desktopSvg)) {
        await sharp(desktopSvg)
            .resize(1024, 1024)
            .png()
            .toFile(desktopPng);
        console.log(`  ✓ Created icon.png (1024x1024)`);
    } else {
        console.log(`  ⚠ ${desktopSvg} not found`);
    }

    // Convert PWA icons
    console.log('\n📱 Converting PWA Icons...');
    const iconsDir = path.join(projectRoot, 'ui', 'icons');
    const masterSvg = path.join(iconsDir, 'icon-master.svg');

    if (fs.existsSync(masterSvg)) {
        const sizes = [72, 96, 128, 144, 152, 192, 384, 512];

        for (const size of sizes) {
            const outputPath = path.join(iconsDir, `icon-${size}x${size}.png`);
            await sharp(masterSvg)
                .resize(size, size)
                .png()
                .toFile(outputPath);
            console.log(`  ✓ Created icon-${size}x${size}.png`);
        }
    } else {
        console.log(`  ⚠ ${masterSvg} not found`);
    }

    // Convert shortcut icons
    console.log('\n🔗 Converting Shortcut Icons...');
    const shortcuts = ['shortcut-new.svg', 'shortcut-history.svg', 'shortcut-settings.svg'];

    for (const filename of shortcuts) {
        const svgPath = path.join(iconsDir, filename);
        if (fs.existsSync(svgPath)) {
            const pngPath = svgPath.replace('.svg', '.png');
            await sharp(svgPath)
                .resize(96, 96)
                .png()
                .toFile(pngPath);
            console.log(`  ✓ Created ${filename.replace('.svg', '.png')}`);
        }
    }

    console.log('\n' + '='.repeat(70));
    console.log('✓ All icons converted successfully!');
    console.log('='.repeat(70));
    console.log('\n📝 Next Steps:');
    console.log('  1. Review icons in electron/assets/ and ui/icons/');
    console.log('  2. (Optional) Replace with custom designs');
    console.log('  3. Build your app: npm run build');
}

// Run conversion
convertSvgToPng().catch(error => {
    console.error('\n❌ Error converting icons:', error.message);
    console.log('\nTry alternative methods:');
    console.log('  1. Online: https://cloudconvert.com/svg-to-png');
    console.log('  2. Install ImageMagick: brew install imagemagick (macOS)');
    console.log('  3. Use browser: Open SVG files and screenshot');
    process.exit(1);
});
