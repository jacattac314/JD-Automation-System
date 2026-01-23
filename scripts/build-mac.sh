#!/bin/bash
# Build script for macOS

set -e  # Exit on error

echo "=========================================="
echo " Building JD Automation System - macOS"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed!"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

echo "[1/4] Installing npm dependencies..."
npm install

echo ""
echo "[2/4] Bundling Python runtime..."
python3 scripts/bundle-python.py

echo ""
echo "[3/4] Building Electron app for macOS..."
npm run build:mac

echo ""
echo "[4/4] Build complete!"
echo ""
echo "=========================================="
echo " Build successful!"
echo "=========================================="
echo ""
echo "Your installers are in the 'dist' folder:"
ls -lh dist/*.dmg dist/*.zip 2>/dev/null || echo "No installers found"
echo ""
