# MDI Distribution Instructions

## For End Users (Your Associate)

### Installation Steps

1. **Download** the DMG installer from the latest GitHub release:
   - Go to: https://github.com/Digital-Grinnell/manage-digital-ingest-flet-CollectionBuilder/releases
   - Download `MDI-Installer.dmg`

2. **Install** the application:
   - Double-click `MDI-Installer.dmg` to mount it
   - Drag `MDI.app` to the `Applications` folder
   - Eject the DMG installer

3. **First Launch**:
   - Open `MDI` from your Applications folder
   - If you see a security warning about an unidentified developer:
     - Go to **System Settings** > **Privacy & Security**
     - Scroll down to find "MDI was blocked from use"
     - Click **Open Anyway**
     - Click **Open** in the confirmation dialog

4. **Start Using MDI**:
   - No Python installation required
   - No dependencies to install
   - Everything is bundled in the app

### System Requirements

- **macOS Version**: 10.15 (Catalina) or later
- **Disk Space**: ~400 MB
- **Architecture**: Universal (Intel & Apple Silicon)

### Troubleshooting

**Q: The app says it's damaged or can't be opened**  
A: This is macOS Gatekeeper. Follow the "First Launch" security steps above.

**Q: The app opens but immediately closes**  
A: Check Console.app for crash logs. Report the issue with logs attached.

**Q: How do I uninstall?**  
A: Simply drag MDI.app from Applications to Trash.

---

## For Developers

### Building from Source

#### Prerequisites

- **Python**: 3.10 or later (3.14+ recommended)
- **Homebrew**: For installing dependencies
- **Xcode Command Line Tools**: `xcode-select --install`

#### Build Process

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Digital-Grinnell/manage-digital-ingest-flet-CollectionBuilder.git
   cd manage-digital-ingest-flet-CollectionBuilder
   ```

2. **Set up Python environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip setuptools wheel
   pip install -r python-requirements.txt
   ```

3. **Build the macOS app**:
   ```bash
   ./build-macos.sh
   ```
   
   This script:
   - Runs `flet build macos`
   - Fixes webview_flutter_android version incompatibility
   - Compiles with Flutter
   - Outputs to `build/macos/MDI.app`

4. **Create distributable DMG**:
   ```bash
   ./create-dmg.sh
   ```
   
   This creates `MDI-Installer.dmg` ready for distribution.

### Creating a GitHub Release

#### Option 1: Using GitHub CLI (Recommended)

```bash
# Create a new version tag
VERSION="v1.0.0"  # Update version number

# Create and push tag
git tag -a $VERSION -m "Release $VERSION"
git push origin $VERSION

# Create release with DMG
gh release create $VERSION \
  MDI-Installer.dmg \
  --title "MDI $VERSION" \
  --notes "Release notes here"
```

#### Option 2: Manual Upload

1. Go to: https://github.com/Digital-Grinnell/manage-digital-ingest-flet-CollectionBuilder/releases/new
2. Click "Choose a tag" → Create new tag (e.g., `v1.0.0`)
3. Fill in release title and notes
4. Drag `MDI-Installer.dmg` to the attachments area
5. Click "Publish release"

### Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

- [ ] Test the app thoroughly
- [ ] Update version in `pyproject.toml`
- [ ] Update HISTORY.md or CHANGELOG.md
- [ ] Run `./build-macos.sh`
- [ ] Run `./create-dmg.sh`
- [ ] Test the DMG installer
- [ ] Create Git tag
- [ ] Upload to GitHub releases
- [ ] Notify users

### Build Troubleshooting

**Issue**: Flet build fails with dependency errors  
**Solution**: The `build-macos.sh` script handles this automatically by fixing `webview_flutter_android` version.

**Issue**: "Flutter not found"  
**Solution**: Flet installs Flutter automatically. If issues persist, delete `build/flutter` and re-run.

**Issue**: Xcode errors during build  
**Solution**: Ensure Xcode Command Line Tools are installed: `xcode-select --install`

### Technical Details

- **Flet Version**: 0.28.2
- **Flutter Version**: 3.29.2 (managed by Flet)
- **Python Runtime**: Bundled in app
- **App Size**: ~300-400 MB (includes Python + all dependencies)

### File Structure

```
build/
├── macos/
│   └── MDI.app              # Final application
└── flutter/                 # Flutter build directory
    ├── pubspec.yaml         # Modified by build script
    └── ...

MDI-Installer.dmg            # Distributable installer
```

### Known Issues

1. **WebView Dependency**: Flet 0.28.2 has an incompatibility with Flutter 3.29.2's webview_flutter_android version. The `build-macos.sh` script automatically fixes this.

2. **First Build Takes Long**: Flutter downloads dependencies on first build (~5-10 minutes). Subsequent builds are faster.

3. **Gatekeeper Warnings**: Users will see security warnings since the app isn't code-signed. Provide clear instructions for bypass.

### Future Improvements

- [ ] Code signing for easier installation
- [ ] Notarization for Gatekeeper
- [ ] Auto-update mechanism
- [ ] Reduce app size through optimization
- [ ] Windows and Linux builds

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/Digital-Grinnell/manage-digital-ingest-flet-CollectionBuilder/issues
- Email: digital@grinnell.edu
