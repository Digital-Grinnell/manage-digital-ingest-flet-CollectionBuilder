# CollectionBuilder + MDI Custom Icons

## Files Created

### Main Application Icon (MDI Icon)
1. **assets/mdi_icon.png** - Main app icon (256x256) - CollectionBuilder logo with "MDI" badge
2. **assets/favicon-256.png** - High quality favicon (256x256)
3. **assets/favicon-128.png** - Standard favicon (128x128)
4. **assets/favicon-64.png** - Smaller favicon (64x64)
5. **assets/favicon-32.png** - Classic favicon (32x32)
6. **assets/favicon.ico** - Windows ICO format (32x32)

### Original Files
7. **assets/cb-logo-original.png** - Original CollectionBuilder logo from website
8. **assets/cb_icon.svg** - Vector SVG version (512x512) - previous custom icon
9. **assets/cb_icon.png** - Raster PNG version (512x512) - previous custom icon

## Design Elements

The MDI icon features:

- **CollectionBuilder Logo** - Official CB logo from https://collectionbuilder.github.io/
- **Blue "MDI" badge** (#2563eb) - "Manage Digital Ingest" branding in bottom right
  - Bold white "MDI" text
  - Rounded rectangle background
  - Positioned in lower right corner for visibility

## Usage in Application

The icon is used in two places:

1. **Window Icon/Favicon** (app.py)
   ```python
   page.window.icon = "assets/mdi_icon.png"
   ```
   - Appears in the window title bar
   - Appears in the taskbar/dock
   - Appears in alt-tab switcher

2. **AppBar Leading Icon** (app.py)
   ```python
   leading=ft.Container(
       content=ft.Image(src="assets/mdi_icon.png", ...)
   )
   ```
   - Appears in the top-left of the application
   - Provides consistent branding

## Technical Details

- **Format**: PNG (RGBA) and ICO
- **Dimensions**: Multiple sizes (32x32 to 256x256)
- **Color Profile**: sRGB
- **Transparency**: Yes (RGBA)
- **File Sizes**: 
  - favicon.ico: ~5KB
  - favicon-32.png: ~2KB
  - favicon-64.png: ~6KB
  - favicon-128.png: ~16KB
  - favicon-256.png: ~31KB
  - mdi_icon.png: ~31KB

## Source

- Original CollectionBuilder logo: https://collectionbuilder.github.io/images/logo/cb-logo-solid-vgold-transparent.png
- License: CollectionBuilder is open source (MIT License)

## Credits

Created using Python Pillow library with the official CollectionBuilder logo and custom "MDI" badge overlay.

