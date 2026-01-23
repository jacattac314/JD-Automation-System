# Building JD Automation System

Complete guide to building and distributing JD Automation System as a desktop application (Windows, Mac, Linux) and Progressive Web App (PWA).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Desktop App (Electron)](#desktop-app-electron)
  - [Quick Start](#quick-start)
  - [Platform-Specific Builds](#platform-specific-builds)
  - [Understanding the Build Process](#understanding-the-build-process)
- [Progressive Web App (PWA)](#progressive-web-app-pwa)
- [Distribution](#distribution)
- [Auto-Updates](#auto-updates)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Node.js 16+**
   - Download: https://nodejs.org/
   - Verify: `node --version`

2. **Python 3.10+**
   - Download: https://www.python.org/
   - Verify: `python --version` (or `python3 --version`)

3. **Git**
   - Download: https://git-scm.com/
   - Verify: `git --version`

### Platform-Specific Requirements

#### Windows
- Windows 10 or later
- Visual Studio Build Tools (optional, for native modules)

#### macOS
- macOS 10.13 or later
- Xcode Command Line Tools: `xcode-select --install`
- For code signing: Apple Developer account

#### Linux
- Modern Linux distribution (Ubuntu 18.04+, Fedora 30+, etc.)
- Build essentials: `sudo apt install build-essential` (Debian/Ubuntu)

---

## Desktop App (Electron)

### Quick Start

The easiest way to build for your current platform:

```bash
# 1. Install npm dependencies
npm install

# 2. Bundle Python runtime
python3 scripts/bundle-python.py

# 3. Build for your platform
npm run build
```

Your installer will be in the `dist/` folder.

### Platform-Specific Builds

#### Build for Windows (on any platform)

```bash
# Using build script (Windows)
scripts\build-windows.bat

# Or manually
npm run build:win
```

**Output:**
- `JD Automation System-1.0.0-win-x64.exe` - NSIS installer
- `JD Automation System-1.0.0-portable.exe` - Portable version (no install needed)

#### Build for macOS (must be on macOS)

```bash
# Using build script
./scripts/build-mac.sh

# Or manually
npm run build:mac
```

**Output:**
- `JD Automation System-1.0.0-mac-x64.dmg` - Intel Macs
- `JD Automation System-1.0.0-mac-arm64.dmg` - Apple Silicon
- `JD Automation System-1.0.0-mac-x64.zip` - Intel Macs (archive)
- `JD Automation System-1.0.0-mac-arm64.zip` - Apple Silicon (archive)

#### Build for Linux (on any platform)

```bash
# Using build script
./scripts/build-linux.sh

# Or manually
npm run build:linux
```

**Output:**
- `JD Automation System-1.0.0-linux-x64.AppImage` - Universal Linux (recommended)
- `JD Automation System-1.0.0-linux-x64.deb` - Debian/Ubuntu
- `JD Automation System-1.0.0-linux-x64.rpm` - Fedora/RedHat

#### Build for All Platforms (macOS only)

```bash
npm run build:all
```

This creates installers for Windows, macOS, and Linux. **Note:** Code signing only works when building on the target platform.

### Understanding the Build Process

The build process has three main steps:

#### 1. Bundle Python Runtime

```bash
python3 scripts/bundle-python.py
```

This creates a standalone Python environment in `python-dist/` containing:
- Python interpreter
- All dependencies from `requirements.txt`
- Optimized (removes unnecessary files)

**Why?** Users don't need Python installed. The app bundles everything.

#### 2. Install Node Dependencies

```bash
npm install
```

Installs:
- `electron` - Desktop app framework
- `electron-builder` - Packaging and installer creation
- `electron-updater` - Auto-update support
- `electron-log` - Logging

#### 3. Build and Package

```bash
npm run build
```

electron-builder:
1. Copies app files into ASAR archive
2. Bundles Python runtime from `python-dist/`
3. Creates platform-specific installer
4. Signs code (if certificates configured)
5. Outputs to `dist/` folder

---

## Progressive Web App (PWA)

The app is already PWA-enabled! No build step required.

### How It Works

When users visit your web app:

1. **Service Worker** (`ui/service-worker.js`) is registered
2. **Install prompt** appears after a few visits
3. Users can install to home screen (mobile) or desktop

### Features

- ✅ Offline support (cached pages)
- ✅ Installable to home screen/desktop
- ✅ App-like experience (no browser UI)
- ✅ Auto-updates on reload
- ✅ Push notifications (ready for future use)

### Deploying PWA

Just deploy your web app normally. The PWA features work automatically when served over HTTPS:

```bash
# Start the server
python start.py
```

Users can install from:
- **Chrome/Edge:** Three-dot menu → "Install JD Automation System"
- **Safari (iOS):** Share → "Add to Home Screen"
- **In-app prompt:** Custom banner appears automatically

### Testing PWA Locally

1. Start the server: `python start.py`
2. Open in Chrome: http://127.0.0.1:8000
3. Open DevTools → Application → Service Workers
4. Check "Update on reload" and "Offline" to test

---

## Distribution

### Hosting Installers

#### Option 1: GitHub Releases (Recommended)

1. Create a release on GitHub:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. Upload installers from `dist/` folder to the release

3. Auto-updater will automatically check GitHub for new versions

#### Option 2: Custom Server

Update `package.json`:
```json
"publish": {
  "provider": "generic",
  "url": "https://your-server.com/releases"
}
```

Place installers at: `https://your-server.com/releases/`

### Auto-Updates

Auto-update is **already configured** and works out of the box:

- Checks GitHub Releases for new versions
- Downloads updates in background
- Prompts user to restart and install
- Uses `electron-updater` with differential updates (small download)

#### Testing Auto-Updates

1. Build version 1.0.0
2. Install it
3. Change version in `package.json` to 1.0.1
4. Build and publish to GitHub Releases
5. Open app → It will detect and download update

#### Disabling Auto-Updates

In `electron/main.js`, comment out:
```javascript
// autoUpdater.checkForUpdatesAndNotify();
```

---

## Code Signing

### Why Sign Your App?

- **macOS:** Required for apps to run without warnings
- **Windows:** Prevents SmartScreen warnings
- **Trust:** Users trust signed apps more

### macOS Signing

1. Get an Apple Developer account ($99/year)
2. Create signing certificates in Xcode
3. Export as `.p12` file
4. Set environment variables:

```bash
export CSC_LINK=/path/to/certificate.p12
export CSC_KEY_PASSWORD=your-password
export APPLE_ID=your-apple-id@email.com
export APPLE_ID_PASSWORD=app-specific-password
```

5. Build: `npm run build:mac`

### Windows Signing

1. Purchase code signing certificate (DigiCert, Sectigo, etc.)
2. Export as `.pfx` file
3. Set environment variables:

```bash
set CSC_LINK=C:\path\to\certificate.pfx
set CSC_KEY_PASSWORD=your-password
```

4. Build: `npm run build:win`

### Skip Signing (Development)

```bash
# Skip code signing for testing
export CSC_IDENTITY_AUTO_DISCOVERY=false
npm run build
```

---

## File Structure

After building, here's what goes into the app:

```
JD Automation System.app/  (or .exe on Windows)
├── electron/              # Electron main process
│   ├── main.js           # App entry point
│   ├── preload.js        # Security bridge
│   └── assets/           # Icons
├── ui/                   # Web interface
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── pwa-init.js
├── api/                  # Python backend
│   └── server.py
├── modules/              # Business logic
├── core/                 # Core orchestration
└── resources/
    ├── python/           # Bundled Python runtime
    └── app/              # Python source files
```

---

## Customization

### Change App Name

Edit `package.json`:
```json
"name": "your-app-name",
"productName": "Your App Display Name"
```

### Change App Icon

Replace icons in `electron/assets/`:
- `icon.png` - 1024x1024 source (electron-builder auto-generates others)
- `icon.ico` - Windows
- `icon.icns` - macOS

Generate icons: https://github.com/electron-userland/electron-builder#icons

### Change Version

Edit `package.json`:
```json
"version": "1.0.0"
```

Follows Semantic Versioning: MAJOR.MINOR.PATCH

### Build Configuration

All build settings are in `package.json` under the `build` key:

- **File inclusion:** `build.files`
- **Extra resources:** `build.extraResources`
- **Platform targets:** `build.win`, `build.mac`, `build.linux`
- **Installer options:** `build.nsis`, `build.dmg`, etc.

---

## Troubleshooting

### "Python not found" error

**Solution:** Make sure Python 3.10+ is installed and in your PATH:
```bash
python3 --version  # Should show 3.10 or higher
```

### "electron-builder" command not found

**Solution:** Install dependencies:
```bash
npm install
```

### Build fails with "Cannot find module"

**Solution:** Clean and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

### App won't start: "Port 8000 already in use"

**Solution:** Kill existing Python server:
```bash
# macOS/Linux
killall python

# Windows
taskkill /F /IM python.exe
```

### macOS: "App is damaged and can't be opened"

**Solution:** Clear quarantine attribute:
```bash
xattr -cr "/Applications/JD Automation System.app"
```

Or sign your app properly (see Code Signing section).

### Windows SmartScreen warning

**Solution:**
- For testing: Click "More info" → "Run anyway"
- For distribution: Sign your app with a code signing certificate

### Large app size (200+ MB)

**Normal.** The app bundles:
- Electron runtime (~100 MB)
- Python runtime (~50-80 MB)
- Dependencies (~20-50 MB)

**Reduce size:**
1. Remove unused Python packages from `requirements.txt`
2. Enable compression: `"compression": "maximum"` (already set)
3. Use `asar` archive: `"asar": true` (already set)

### Service Worker not registering (PWA)

**Solution:** PWA only works over HTTPS or localhost. Check:
```bash
# Open browser console
# Look for: "[PWA] Service Worker registered"
```

If missing, check that you're accessing via `https://` or `http://localhost`.

---

## Development Mode

### Run Without Building

```bash
# Terminal 1: Start Python backend
python start.py

# Terminal 2: Start Electron (in dev mode)
npm run dev
```

This is faster for development - no build step needed.

### Hot Reload

The web UI auto-reloads when you change files:
1. Save changes to `ui/app.js` or `ui/styles.css`
2. Reload window: `Cmd+R` (Mac) or `Ctrl+R` (Windows/Linux)

For Electron changes (`electron/main.js`), restart the app.

---

## Publishing Checklist

Before releasing:

- [ ] Update version in `package.json`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Test on all target platforms
- [ ] Create icons (if not already done)
- [ ] Set up code signing (for production)
- [ ] Build all platforms: `npm run build:all` (on Mac) or separately
- [ ] Create GitHub Release with tag (e.g., `v1.0.0`)
- [ ] Upload installers to release
- [ ] Test auto-updater with older version
- [ ] Update README with download links

---

## Advanced Topics

### Custom Python Dependencies

Add to `requirements.txt`, then rebuild:
```bash
python3 scripts/bundle-python.py
npm run build
```

### Custom Electron Settings

Edit `electron/main.js` to customize:
- Window size and position
- Menu items
- Keyboard shortcuts
- Tray icon
- Multiple windows

### Build on CI/CD

Example GitHub Actions workflow:

```yaml
name: Build
on: [push]
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: npm install
      - run: python3 scripts/bundle-python.py
      - run: npm run build
      - uses: actions/upload-artifact@v3
        with:
          name: installers-${{ matrix.os }}
          path: dist/*
```

---

## Resources

- **Electron Documentation:** https://www.electronjs.org/docs
- **electron-builder:** https://www.electron.build/
- **PWA Guide:** https://web.dev/progressive-web-apps/
- **Service Workers:** https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/jacattac314/JD-Automation-System/issues
- Email: your-email@example.com

---

**Happy Building! 🚀**
