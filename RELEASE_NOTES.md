# MDI v1.0.0 - macOS Application Release

## 📦 Easy Installation for macOS Users

This release provides a standalone macOS application that requires **no Python installation** or dependency management.

### Download & Install

1. Download `MDI-Installer.dmg` below
2. Double-click to open
3. Drag **MDI.app** to your Applications folder
4. Run from Applications (see security note below)

### 🔐 First Launch Security Note

macOS will show a security warning since this app isn't code-signed:
1. Go to **System Settings** > **Privacy & Security**
2. Find "MDI was blocked from use"
3. Click **Open Anyway**
4. Confirm by clicking **Open**

## ✨ What's New

### Features
- **Automatic Transcript Fixing** - Smart handling of CSV transcript data
- **Enhanced Fuzzy Search** - Better matching for files without extensions
- **Improved CSV Handling** - Better quote and delimiter management
- **Python 3.10+ Compatibility** - Updated dependencies for modern Python

### Improvements
- Standalone macOS app bundle (no installation hassles)
- All dependencies bundled
- CollectionBuilder custom icon with MDI badge
- ~163 MB installer (app expands to ~360 MB)

### Requirements
- **macOS**: 10.15 (Catalina) or later
- **Python**: Not required (bundled)
- **Disk Space**: ~400 MB

## 🐛 Known Issues

- Security warning on first launch (macOS Gatekeeper) - see instructions above
- App is not code-signed or notarized (requires manual security approval)

## 📚 Documentation

See [DISTRIBUTION_INSTRUCTIONS.md](DISTRIBUTION_INSTRUCTIONS.md) for:
- Detailed installation steps
- Building from source
- Creating releases
- Troubleshooting

## 🛠️ Technical Details

- **Flet**: 0.28.2
- **Flutter**: 3.29.2
- **Python Runtime**: 3.14.3 (bundled)
- **Build System**: Custom script with webview dependency fix

## 💾 Downloads

Download **MDI-Installer.dmg** from the assets below.

---

**Full Changelog**: https://github.com/Digital-Grinnell/manage-digital-ingest-flet-CollectionBuilder/commits/v1.0.0
