# Development History - CollectionBuilder Edition

## Overview
This document tracks the development history of the manage-digital-ingest-flet-CollectionBuilder application, focusing on features and enhancements specific to CollectionBuilder static site workflows.

**Note**: This application is a specialized fork focusing exclusively on CollectionBuilder workflows. For the original dual-mode (Alma/CollectionBuilder) version, see the manage-digital-ingest-flet-oo repository.

---

## February 2026 - Temp Directory Relocation

### Fixed Path Issue with Spaces
**Date**: February 17, 2026

**Problem**: Application failed when project directory path contained spaces because temp files were created in `storage/temp/` subdirectory.

**Solution**: Relocated all temporary file operations to `~/Downloads/MDI_temp/`

**Files Modified**:
- `views/file_selector_view.py` - Updated `copy_files_to_temp_directory()` method (2 locations)
- `views/update_csv_view.py` - Updated CSV temp directory creation
- `utilities/README.md` - Updated example paths

**Benefits**:
- Eliminates path-with-spaces errors
- User-accessible temp location in Downloads folder
- Cleaner separation of app and working files

---

## November 2025 - CollectionBuilder Fork and Specialization

### Alma Removal and CollectionBuilder Focus
**Date**: November 12-17, 2025

**Major Changes**:
- Removed all Alma-specific code and UI elements
- Deleted `modes.json` configuration file and mode-switching logic
- Removed Alma-specific data files from `_data/` directory
- Updated all documentation to focus on CollectionBuilder workflows
- Streamlined application to single-purpose CollectionBuilder tool

**Files Modified**:
- `views/update_csv_view.py` - Removed Alma Steps 2-3.65
- `views/settings_view.py` - Removed mode selection, hardcoded CollectionBuilder
- `views/derivatives_view.py` - Removed Alma UI elements
- `views/instructions_view.py` - Removed mode display
- `README.md` - Updated with CollectionBuilder-only instructions
- `_data/` - Removed: `alma_aws_s3.md`, `alma_aws_s3.sh`, `alma_storage.md`, `verified_CSV_headings_for_Alma-D.csv`, `modes.json`

**Impact**: Simplified codebase, clearer user experience, easier maintenance

### Multi-Directory Fuzzy Search
**Date**: November 12, 2025

**Feature**: Extended fuzzy search to support multiple directory selection

**Implementation**:
- Added `search_directories` list to session state
- Created "Add Search Directory" button in File Selector view
- Individual directory removal buttons
- Combined search results across all selected directories
- Separate "Launch Search" button with rocket icon (🚀)
- Fuzzy matching across multiple directory trees
- Best match selection prioritizes higher similarity scores

**User Benefits**:
- Select files from multiple collection folders simultaneously
- Useful when processing files scattered across different directories
- Reduces need for manual directory switching
- Visual feedback showing all active search paths

**Files Modified**:
- `views/file_selector_view.py` - Multi-directory search logic, UI components

### Compound Object Protection
**Date**: November 12, 2025

**Enhancement**: Added safeguards to prevent URL overwrites for compound objects

**Logic**:
- During Step 1 (file matching/URL updates), skip rows with:
  - `display_template == 'compound_object'`
  - `display_template == 'multiple'`
- Compound objects have no object content of their own
- Prevents accidental overwriting of custom parent images
- Parent derivative URLs populated in Step 3.7 from first child

**Protection Mechanism**:
```python
# Check if this row is a compound object parent
display_template = str(row.get('display_template', '')).strip()
if display_template in ['compound_object', 'multiple']:
    logger.info(f"Skipping compound object parent: objectid={row.get('objectid', 'unknown')}")
    continue  # Skip this row, do not update URLs
```

**Files Modified**:
- `views/update_csv_view.py` - Compound object detection and skip logic

### Parent/Child Derivative Safeguards
**Date**: November 3, 2025

**Enhancement**: Improved parent/child derivative copying logic

**Previous Behavior**:
- Always copied first child's `image_small` and `image_thumb` to parent
- Overwrote custom parent images (e.g., poster images)

**New Behavior**:
- Only copy to parent **if parent fields are empty**
- Preserves custom images set by metadata curators
- Logs when copies are skipped due to existing values

**Example**:
```python
# Only copy if parent field is empty
if pd.isna(parent_row['image_small']) or parent_row['image_small'] == '':
    parent_row['image_small'] = first_child['image_small']
    logger.info(f"Copied image_small from child to parent (objectid={parent_objectid})")
else:
    logger.info(f"Skipped image_small copy - parent already has value (objectid={parent_objectid})")
```

**Files Modified**:
- `views/update_csv_view.py` - Step 3.7 parent/child logic

**Documentation**:
- Created `PARENT-CHILD-CHANGES.md` detailing this functionality

---

## October 2025 - Original Development (CollectionBuilder Features)

### Session 8 - Enhanced Documentation
**Date**: October 17, 2025, 7:45 PM - 8:15 PM

**Focus**: Comprehensive documentation overhaul

**Updates**:
1. Created detailed `INSTRUCTIONS.md` with:
   - Before You Begin section
   - Step-by-step workflow
   - CSV column requirements
   - Azure storage setup
   - Troubleshooting guide
   
2. Enhanced `README.md` with:
   - Quick start guide
   - Installation instructions
   - macOS and Windows support
   - Dependencies and setup
   
3. Documented derivative generation workflow:
   - Supported image formats (PNG, JPEG, TIFF, GIF)
   - PDF first-page conversion
   - Thumbnail and small derivative creation
   - Pillow and PyMuPDF integration

**Files Created/Modified**:
- `INSTRUCTIONS.md` - Created comprehensive workflow guide
- `README.md` - Enhanced with installation and quick start
- `_data/home.md` - Updated welcome text
- `_data/picker.md` - Enhanced file selector instructions

**Impact**: Significantly improved onboarding for new users

### Session 7 - Session State Preservation
**Date**: October 17, 2025, 6:30 PM - 7:30 PM

**Problem**: Application lost all state on window resize or navigation

**Solution**: Implemented persistent session state management

**Implementation**:
1. Created `persistent.json` in `_data/` directory
2. Save state on every significant action:
   - CSV file selection
   - Collection selection
   - Search directory changes
   - CSV modifications
   
3. Restore state on application startup
4. Graceful handling of missing/corrupted state file

**Files Modified**:
- `app.py` - State save/restore on app lifecycle
- `views/update_csv_view.py` - Save state after CSV operations
- `views/file_selector_view.py` - Save state after directory changes
- `views/storage_view.py` - Save state after collection selection

**User Experience Improvement**:
- No more lost work on accidental window resize
- Seamless navigation between views
- Application remembers last used CSV and collection

### Session 5 - CSV Row Management Enhancement
**Date**: October 17, 2025, 2:00 PM - 3:15 PM

**Feature**: Delete duplicate or unwanted rows from CSV

**Implementation**:
1. Added "Delete Row" button for each CSV row in UpdateCSV view
2. Confirmation dialog before deletion
3. Immediate CSV file update on disk
4. DataTable refresh to show current state
5. Logger notification of deletion

**Safety Features**:
- Confirmation required ("Are you sure?")
- Preserves CSV formatting and encoding
- UTF-8 support maintained
- Logs all deletions for audit trail

**Files Modified**:
- `views/update_csv_view.py` - Delete row button, confirmation dialog, file update logic

**User Benefits**:
- Quick removal of test rows
- Easy cleanup of duplicate entries
- No need for external CSV editor

### Session 4 - Unique ID Error Resolution
**Date**: October 17, 2025, 11:45 AM - 1:30 PM

**Issue**: Unique ID generation failing for UpdateCSV view

**Root Cause**: Dictionary comprehension creating duplicate keys when multiple rows had same objectid

**Solution**:
```python
# OLD (broken):
row_dict = {row['objectid']: row for _, row in df.iterrows()}  # Duplicates overwrite

# NEW (fixed):
rows_list = [row for _, row in df.iterrows()]  # Preserve all rows
```

**Additional Improvements**:
1. Enhanced error handling for missing CSV files
2. Better error messages for missing columns
3. Validation of required CollectionBuilder columns
4. Graceful degradation when columns missing

**Files Modified**:
- `views/update_csv_view.py` - Row dictionary to list conversion

**Testing**: Verified with CSVs containing duplicate objectids

### Session 3 - UpdateCSV View Enhancements
**Date**: October 16, 2025, 4:00 PM - 6:00 PM

**Major Feature**: Interactive CSV editing and derivative URL management

**Functionality**:
1. **CSV Display**:
   - DataTable showing all CSV rows
   - Key columns: objectid, filename, object_location, image_small, image_thumb
   - Responsive layout with scrolling
   
2. **Apply All Updates Button**:
   - Matches CSV rows to Azure-uploaded files
   - Populates `object_location` URLs
   - Generates `image_small` and `image_thumb` URLs
   - Handles parent/child relationships for compound objects
   - Saves updated CSV to disk
   
3. **File Matching Logic**:
   - Fuzzy matching between `filename` column and uploaded files
   - Supports various file extensions
   - Handles missing file extensions in metadata
   - High similarity threshold to avoid false matches
   
4. **CollectionBuilder URL Structure**:
   ```
   object_location: https://collectionbuilder.blob.core.windows.net/{container}/{collection}/{filename}
   image_small: https://collectionbuilder.blob.core.windows.net/{container}/{collection}/{filename}_SMALL.jpg
   image_thumb: https://collectionbuilder.blob.core.windows.net/{container}/{collection}/{filename}_TN.jpg
   ```

**Files Created/Modified**:
- `views/update_csv_view.py` - Complete UpdateCSV view implementation
- `utils.py` - Fuzzy matching utilities

**User Workflow**:
1. Upload derivatives to Azure
2. Select CSV file with metadata
3. Click "Apply All Updates"
4. Review populated URLs in table
5. Export updated CSV for CollectionBuilder ingestion

---

## Key Technologies

### Pillow + PyMuPDF (November 2025)
**Replaced**: ImageMagick/Wand (unreliable cross-platform)

**Benefits**:
- Pure Python dependencies
- Better Windows support
- No external binary dependencies
- Reliable PDF thumbnail generation

**Implementation**:
- Pillow for image format conversion and resizing
- PyMuPDF for PDF first-page extraction
- Consistent derivative quality

### Flet Framework
**Version**: 0.24+

**Usage**:
- Cross-platform desktop UI (macOS, Windows, Linux)
- Python-based declarative UI
- Reactive state management
- Native-like user experience

### Pandas
**Version**: 2.3.3

**Configuration**:
```python
dtype=str  # All columns as strings
keep_default_na=False  # Preserve empty strings
quoting=csv.QUOTE_MINIMAL  # Clean CSV output
```

### Azure Blob Storage
**SDK**: azure-storage-blob

**Features**:
- Hierarchical container/collection structure
- Direct upload from application
- Public access URLs for CollectionBuilder
- Progress tracking on large uploads

---

## Development Principles

### CollectionBuilder Focus
- All features designed for static site workflows
- Metadata structure follows CB conventions
- Compound object support built-in
- CSV column naming matches CB requirements

### User Experience
- Minimal clicks for common workflows
- Persistent state across sessions
- Clear error messages and logging
- Comprehensive help documentation

### Code Quality
- Extensive logging for debugging
- Error handling at all critical points
- Type safety (Pandas dtype=str)
- Modular view architecture

### Documentation
- Inline code comments
- Separate documentation files
- User-facing help text
- Development history tracking

---

## Future Roadmap

### Planned Enhancements
1. **Batch Operations**:
   - Delete multiple rows at once
   - Bulk file selection
   - Multi-collection upload
   
2. **Validation**:
   - CSV column validation before processing
   - Required field checking
   - URL format verification
   - Duplicate objectid detection
   
3. **Advanced Compound Objects**:
   - Choose which child for parent derivative
   - Multi-level parent/child hierarchies
   - Custom parent image upload
   
4. **Metadata Editing**:
   - Edit CSV values directly in DataTable
   - Add new rows from UI
   - Import/export subsets

5. **Performance**:
   - Async file uploads
   - Progress indicators for large CSVs
   - Caching for repeated operations

### CollectionBuilder Integration
- Direct git push to CB repository
- Automatic _config.yml updates
- Preview site generation
- Metadata validation against CB schema

---

## Contributors
Development led by Mark McFate and the Digital.Grinnell team at Grinnell College Libraries.

## License
This project maintains the same license as the original manage-digital-ingest-flet-oo repository.

## Related Documentation
- `README.md` - Quick start and installation
- `PARENT-CHILD-CHANGES.md` - Compound object handling details
- `_data/home.md` - Application welcome screen
- `_data/verified_CSV_headings_for_GCCB_projects.csv` - Supported CSV columns
