# Standard Library Modules Fix for Flet macOS Builds

## Problem

When building Flet apps for macOS, the `serious_python` framework that bundles Python doesn't include all standard library modules. This causes `ModuleNotFoundError` for stdlib modules that your dependencies need.

## Affected Modules Discovered

- `wsgiref` - Used by `azure.storage.blob`

## Solution

Copy missing stdlib modules from your system Python into the project directory so they get packaged with your app.

### Steps to Add Missing Stdlib Module

1. Find the module in system Python:
```bash
python3 -c "import wsgiref; print(wsgiref.__file__)"
```

2. Copy it to your project root:
```bash
cp -r /opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/lib/python3.13/wsgiref .
```

3. Rebuild the app:
```bash
./build-macos.sh
```

## Why This Happens

The `serious_python_darwin` framework used by Flet includes:
- Python interpreter
- Core stdlib modules (os, sys, io, etc.)
- **NOT all stdlib modules** (wsgiref, email, http, etc.)

Third-party packages (like Azure SDK) assume the full Python stdlib is available, causing import failures.

## Long-term Solutions

### Option 1: Bundle More Stdlib Modules
Create a script to copy commonly needed stdlib modules:

```bash
# Add to project
for module in wsgiref email http urllib smtplib; do
    cp -r $(python3 -c "import $module; print($module.__path__[0])") .
done
```

### Option 2: Use Flet Web Version
The web version doesn't have this issue since it runs in the browser with Pyodide, which includes the full stdlib.

### Option 3: Lazy Import
Defer imports of packages that need missing stdlib modules until they're actually used:

```python
# In storage_view.py
def get_blob_client():
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient(...)
```

This way, if the user doesn't use Azure storage features, the app doesn't crash.

## Prevention

Add to `pyproject.toml`:
```toml
[tool.flet.app]
exclude = [
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    "*.pyc",
]
# wsgiref and other stdlib modules will be in project root
```

## Current Status

- ✅ `dotenv` - Fixed by proper dependency bundling
- ✅ `wsgiref` - Fixed by copying to project
- ⏳ May need more stdlib modules as errors appear

## Testing

After adding stdlib modules and rebuilding:

```bash
open build/macos/MDI.app
```

Check logs for any new `ModuleNotFoundError` messages.
