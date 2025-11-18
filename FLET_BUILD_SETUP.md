# Flet Build Setup - Quick Reference

## What Changed

Your CollectionBuilder application now supports building standalone executables using `flet build`. This is the **only way** to properly embed custom icons/favicons into built applications.

## Key Files Added

### 1. pyproject.toml
Project metadata file required by `flet build`. Contains:
- Application name, version, and description
- Dependencies list
- Organization and company information
- Build configuration

### 2. BUILD.md
Complete documentation for building the application for different platforms (macOS, Windows, Linux, Web).

### 3. Icon Files in assets/
- **icon.png** - Default icon (used as fallback)
- **icon_macos.png** - macOS-specific icon
- **icon_windows.png** - Windows PNG icon
- **icon_windows.ico** - Windows ICO format
- **icon_web.png** - Web application icon

All icons feature the official CollectionBuilder logo with "MDI" badge.

## How It Works

### Development Mode (current)
When you run `./run.sh` or `flet run app.py`:
- Uses `assets/mdi_icon.png` set in app.py
- Icon appears in window title bar and taskbar
- Quick iteration and testing

### Production Build
When you run `.venv/bin/flet build <platform>`:
1. Flet reads `pyproject.toml` for project configuration
2. Looks for icon files in `assets/` directory
3. Generates platform-specific icons automatically
4. Embeds icons into the built application
5. Creates standalone executable in `build/<platform>/`

## Building the Application

### ⚠️ macOS Build Requires Xcode
Building for macOS requires Xcode Command Line Tools:
```bash
# Install Xcode Command Line Tools first (if not installed):
xcode-select --install

# Then build for macOS:
.venv/bin/flet build macos
```

### ✅ Easiest Option: Web Build (No Xcode Required)
Web builds don't require Xcode and work on any platform:
```bash
.venv/bin/flet build web
```

The web app will be in `build/web/` and can be:
- Served locally with `python -m http.server -d build/web`
- Deployed to any web hosting service
- Run in any modern browser

### For Windows (requires Windows or WSL):
```bash
.venv/bin/flet build windows
```

### For Linux:
```bash
.venv/bin/flet build linux
```

The built applications will have your custom MDI icon properly embedded!

## Important Notes

1. **First build takes time**: Flutter SDK will be automatically downloaded (~2GB)
2. **Icon naming is critical**: Files must be named exactly as shown (icon.png, icon_macos.png, etc.)
3. **Development vs Production**: 
   - During development: `page.window.icon` in app.py controls the icon
   - After building: Icon files in `assets/` control the icon
4. **Build output**: Check `build/<platform>/` for the executable

## Testing the Icon

After building, the icon will appear:
- macOS: In Finder, Dock, About window
- Windows: In Explorer, Taskbar, title bar
- Web: As favicon in browser tab
- Linux: In application launcher and window decorations

## Documentation

- **BUILD.md**: Complete build instructions and troubleshooting
- **assets/ICON_README.md**: Icon specifications and design details
- **pyproject.toml**: Build configuration settings

## Next Steps

1. Try a build: `.venv/bin/flet build macos -v` (verbose mode for first time)
2. Check output in `build/macos/`
3. Test the built app to verify icon appears correctly
4. Adjust settings in `pyproject.toml` if needed (version, company name, etc.)
