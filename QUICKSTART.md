# Quick Start Guide

Get your distributable app built in 5 minutes.

## Prerequisites Check

```bash
# Check Node.js (need 16+)
node --version

# Check Python (need 3.10+)
python3 --version

# Check Git
git --version
```

Don't have them? Install from:
- Node.js: https://nodejs.org/
- Python: https://www.python.org/
- Git: https://git-scm.com/

## Build Your First Desktop App

### Step 1: Install Dependencies
```bash
npm install
```
*Takes 2-3 minutes*

### Step 2: Bundle Python Runtime
```bash
# macOS/Linux:
python3 scripts/bundle-python.py

# Windows:
python scripts\bundle-python.py
```
*Takes 1-2 minutes*

### Step 3: Build!
```bash
npm run build
```
*Takes 3-5 minutes*

### Step 4: Find Your Installer
```bash
ls dist/
```

**You'll see:**
- Windows: `.exe` files
- macOS: `.dmg` files
- Linux: `.AppImage`, `.deb`, `.rpm` files

**Install and test it!**

## Deploy PWA (Even Faster!)

### Already Done!
Your app is PWA-ready. Just deploy:

```bash
# Start local server
python start.py
```

Open in Chrome → Click install icon in address bar → Done!

## Platform-Specific Builds

### Windows Only
```bash
npm run build:win
```

### macOS Only
```bash
npm run build:mac
```

### Linux Only
```bash
npm run build:linux
```

## Testing Your Build

### Option 1: Install and Run
1. Find installer in `dist/` folder
2. Double-click to install
3. Launch the app
4. Test all features

### Option 2: Development Mode (Faster)
```bash
# Terminal 1: Start Python backend
python start.py

# Terminal 2: Start Electron in dev mode
npm run dev
```

Changes reload instantly - no rebuild needed!

## First Release Checklist

- [ ] Build installers
- [ ] Test on your platform
- [ ] Create GitHub Release (tag: v1.0.0)
- [ ] Upload installers to release
- [ ] Share download link

## Troubleshooting

**"Python not found"**
```bash
# Make sure Python is in PATH
which python3  # macOS/Linux
where python   # Windows
```

**"npm install fails"**
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
```

**"Build fails"**
```bash
# Check logs in dist/.electron-builder.log
# Common issue: Missing Python in PATH
```

## File Sizes

**Installers:**
- Windows: ~150 MB
- macOS: ~160 MB
- Linux: ~145-170 MB

**Why so large?**
Includes Python runtime + all dependencies. Users don't need Python installed!

## Next Steps

- Read [BUILDING.md](BUILDING.md) for detailed build instructions
- Read [DISTRIBUTION.md](DISTRIBUTION.md) for release strategies
- Add your app icons to `electron/assets/icon.png`
- Customize app name in `package.json`

## Get Help

- Build issues? Check [BUILDING.md](BUILDING.md) Troubleshooting section
- Distribution questions? See [DISTRIBUTION.md](DISTRIBUTION.md)
- Report bugs: GitHub Issues

---

**That's it! Your app is ready to distribute. 🎉**
