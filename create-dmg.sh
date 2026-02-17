#!/bin/bash
# Create a macOS DMG installer for MDI

set -e

echo "📦 Creating DMG installer for MDI..."

APP_PATH="build/macos/MDI.app"
DMG_NAME="MDI-Installer.dmg"
VOLUME_NAME="MDI Installer"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: $APP_PATH not found. Run ./build-macos.sh first."
    exit 1
fi

# Remove old DMG if exists
if [ -f "$DMG_NAME" ]; then
    echo "🗑️  Removing old $DMG_NAME..."
    rm "$DMG_NAME"
fi

# Create temporary DMG directory
TEMP_DMG_DIR=$(mktemp -d)
echo "📁 Creating temporary directory: $TEMP_DMG_DIR"

# Copy app to temp directory
echo "📋 Copying MDI.app..."
cp -R "$APP_PATH" "$TEMP_DMG_DIR/"

# Create a symbolic link to Applications folder
echo "🔗 Creating Applications link..."
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# Create README
cat > "$TEMP_DMG_DIR/README.txt" << 'EOF'
MDI - Manage Digital Ingest for CollectionBuilder
===================================================

INSTALLATION:
1. Drag MDI.app to the Applications folder
2. Open MDI.app from Applications
3. If you see a security warning, go to System Settings > 
   Privacy & Security and click "Open Anyway"

REQUIREMENTS:
- macOS 10.15 or later
- No Python installation needed (bundled)

DOCUMENTATION:
See README.md in the project repository

Copyright (C) 2025 Digital Grinnell
EOF

# Create DMG
echo "💿 Creating DMG..."
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$TEMP_DMG_DIR" \
    -ov -format UDZO \
    "$DMG_NAME"

# Clean up
echo "🧹 Cleaning up..."
rm -rf "$TEMP_DMG_DIR"

# Get DMG info
DMG_SIZE=$(du -sh "$DMG_NAME" | cut -f1)

echo ""
echo "✅ DMG created successfully!"
echo "📦 File: $DMG_NAME"
echo "📏 Size: $DMG_SIZE"
echo ""
echo "📤 To share with your associate:"
echo "   1. Upload $DMG_NAME to file sharing service (Dropbox, Google Drive, etc.)"
echo "   2. Share the download link"
echo "   3. They double-click to mount, then drag MDI.app to Applications"
echo ""
