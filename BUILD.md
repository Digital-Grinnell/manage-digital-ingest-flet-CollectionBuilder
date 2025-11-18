# Building Manage Digital Ingest with Flet

This document explains how to build standalone executables for the Manage Digital Ingest application using `flet build`.

## Prerequisites

- Python 3.9 or higher
- Virtual environment activated (`.venv`)
- All dependencies installed from `python-requirements.txt`
- **For macOS builds**: Xcode Command Line Tools (`xcode-select --install`)
- **For web builds**: No additional requirements!

## Icon Configuration

The application uses custom icons for different platforms:

- **icon.png** - Default icon (256x256) - CollectionBuilder logo with MDI badge
- **icon_macos.png** - macOS-specific icon
- **icon_windows.png** - Windows-specific icon
- **icon_windows.ico** - Windows ICO format
- **icon_web.png** - Web application icon
- **favicon-*.png** - Multiple favicon sizes for web deployment

All icon files are located in the `assets/` directory and feature the official CollectionBuilder logo with a blue "MDI" badge.

## Building for Different Platforms

### Web Application (Recommended - No Xcode Required!)

Build a web application that runs in any browser:

```bash
.venv/bin/flet build web
```

The built web app will be in `build/web/`. You can serve it locally with:

```bash
python -m http.server -d build/web
```

Then open http://localhost:8000 in your browser.

### macOS (Requires Xcode Command Line Tools)

First, ensure Xcode Command Line Tools are installed:

```bash
xcode-select --install
```

Then build a standalone macOS application:

```bash
.venv/bin/flet build macos
```

The built app will be in `build/macos/`.

### Windows

Build a Windows executable (requires running on Windows or WSL):

```bash
.venv/bin/flet build windows
```

The built executable will be in `build/windows/`.

### Linux

Build a Linux application:

```bash
.venv/bin/flet build linux
```

The built app will be in `build/linux/`.

### Web Application

Build a web application:

```bash
.venv/bin/flet build web
```

The built web app will be in `build/web/`.

## Build Options

### Custom Output Directory

```bash
.venv/bin/flet build macos -o /path/to/output
```

### Verbose Output

For debugging build issues:

```bash
.venv/bin/flet build macos -v
```

Or for even more detail:

```bash
.venv/bin/flet build macos -vv
```

### Build Number and Version

```bash
.venv/bin/flet build macos --build-version 1.0.0 --build-number 1
```

## Project Structure

The build process uses the following structure:

```
manage-digital-ingest-flet-CollectionBuilder/
├── pyproject.toml          # Project metadata and build configuration
├── app.py                  # Main application entry point
├── assets/                 # Icons and other assets
│   ├── icon.png           # Default icon
│   ├── icon_macos.png     # macOS icon
│   ├── icon_windows.png   # Windows icon
│   ├── icon_windows.ico   # Windows ICO icon
│   ├── icon_web.png       # Web icon
│   └── favicon-*.png      # Web favicons
├── views/                  # Application views
├── utils.py               # Utility functions
└── logger.py              # Logging configuration
```

## Icon Specifications

- **macOS**: Recommended minimum 1024x1024 px
- **Windows**: ICO format, 256px size
- **Web**: Recommended minimum 512x512 px
- **Android/iOS**: Not currently configured (requires mobile build setup)

The current icons are 256x256 PNG files with transparent backgrounds, featuring:
- Official CollectionBuilder logo
- Blue "MDI" badge (#2563eb) in bottom right corner
- Professional appearance suitable for all platforms

## Troubleshooting

### Xcode Command Line Tools Error (macOS)

If you see an error like:
```
xcrun: error: unable to find utility "xcodebuild", not a developer tool or in PATH
```

This means Xcode Command Line Tools are not properly installed. Fix it with:

```bash
# Install or reinstall Command Line Tools
xcode-select --install

# If that doesn't work, reset the path:
sudo xcode-select --reset
xcode-select --install
```

**Alternative**: Build for web instead, which doesn't require Xcode:
```bash
.venv/bin/flet build web
```

### Flutter SDK Not Found

The first build will automatically download and install Flutter SDK to `~/flutter/{version}`. This may take some time.

### Build Fails

Try clearing the cache and rebuilding:

```bash
.venv/bin/flet build macos --clear-cache
```

### Icon Not Showing

Ensure icon files exist in `assets/` directory and have the correct names:
- `icon.png` for default
- `icon_macos.png`, `icon_windows.png`, etc. for platform-specific

## Additional Resources

- [Flet Build Documentation](https://flet.dev/docs/publish)
- [Project Homepage](https://github.com/Digital-Grinnell/manage-digital-ingest-flet-CollectionBuilder)
