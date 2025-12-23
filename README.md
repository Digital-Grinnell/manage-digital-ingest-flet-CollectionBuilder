# Manage Digital Ingest: CollectionBuilder Edition

A Flet-based Python application for managing Grinnell College ingest of digital objects to CollectionBuilder static sites.

## 🚀 Quick Start

### Running the Application

#### macOS/Linux

Use the provided `run.sh` script:

```bash
./run.sh
```

**First-time setup:**
```bash
chmod +x run.sh  # Make the script executable (only needed once)
./run.sh         # Run the application
```

#### Windows

Use the provided `run.bat` script:

```cmd
run.bat
```

**What the scripts do:**
1. Check if a Python virtual environment (`.venv`) exists
2. Create the virtual environment if it doesn't exist
3. Activate the virtual environment
4. Install/upgrade required dependencies from `python-requirements.txt`
5. Launch the Flet application

**Requirements:**
- Python 3.7 or higher
- macOS, Linux, or Windows

## 📖 Overview

This CollectionBuilder-specific version of Manage Digital Ingest helps you:

- Prepare digital image collections for CollectionBuilder static sites
- Match CSV metadata with corresponding image files using fuzzy search
- Generate derivative images (thumbnails and small versions)
- Update CSV files with CollectionBuilder-specific metadata (object IDs, parent/child relationships)
- Upload files to Azure Blob storage for CollectionBuilder
- Maintain session state across multiple work sessions

## 🎯 Key Features for CollectionBuilder

- **CollectionBuilder Workflow**: Configured specifically for CollectionBuilder static sites
- **Multi-Directory Fuzzy Search**: Search across multiple directories to match images to CSV metadata entries
- **CB Derivative Generation**: Creates thumbnails (400x400) and small images (800x800)
- **Collection Selection**: Choose target CollectionBuilder collection
- **Parent/Child Relationships**: Manages compound objects and multiple display templates
- **Azure Blob Storage**: Upload files to CollectionBuilder Azure storage
- **CSV Quality Assurance**: 
  - Preserves comment rows (lines starting with #)
  - Converts straight apostrophes to curly apostrophes for CSV parser compatibility
  - Enforces UTF-8 encoding (no BOM)
  - Uses QUOTE_MINIMAL quoting strategy
- **Transcript Workflow**: 
  - **Auto-fixes transcript CSV files** at the start of Update CSV operations
  - Converts various formats (Whisper, Otter.ai, etc.) to CollectionBuilder standard
  - Standardizes headers to `timestamp,speaker,words`
  - Handles different delimiters (comma/semicolon) and encodings
  - Auto-corrects encoding and apostrophes
  - Auto-populates `object_transcript` column
  - Copies corrected transcript CSVs to deployment package
- **Deployment Strategy**:
  - Creates timestamped CSV for record-keeping
  - Creates deployment CSV with original filename
  - Automatically updates `_config.yml` with correct metadata reference
- **Session Preservation**: Save your work and resume later
- **Compound Object Support**: Properly handles compound_object and multiple display templates

## 📋 CollectionBuilder Workflow

1. **Settings**: App is pre-configured for CollectionBuilder mode, select target collection
2. **File Selector**: 
   - Load CSV with CB metadata
   - Add one or more search directories
   - Launch fuzzy search to match image files
   - Review matches and create symbolic links
3. **Create Derivatives**: Generate CB thumbnails (_TN.jpg) and small images (_SMALL.jpg)
4. **Update CSV**: Apply CollectionBuilder-specific metadata updates
   - **Automatically fixes transcript CSV files** (if detected) to standard format
   - Converts headers like `Timestamp,Speaker,Transcript` to `timestamp,speaker,words`
   - Handles semicolon vs comma delimiters and various encoding issues
   - Preserves comment rows (lines starting with #)
   - Populates `object_transcript` column for transcript records
   - Converts straight apostrophes to curly apostrophes for CSV compatibility
5. **Azure Storage**: Upload files to Azure Blob storage for your CB collection (excludes transcript CSVs)
6. **Instructions**: Generate deployment script that:
   - Copies timestamped CSV to `_data/` for record-keeping
   - Creates deployment CSV with original filename
   - Updates `_config.yml` with correct metadata reference
   - Copies transcript CSV files to `_data/transcripts/`

## 📄 Required CSV Columns for CollectionBuilder

See `_data/verified_CSV_headings_for_GCCB_projects.csv` for the complete list of valid column headings for CollectionBuilder workflows.

## 🔧 Configuration

The app automatically sets the mode to "CollectionBuilder" - no mode selection needed. Configure:
- Target CollectionBuilder collection
- Search directories for fuzzy file matching
- Azure storage settings
- Theme (Light/Dark)

## 📚 Additional Documentation

- **Thumbnail Migration**: See `THUMBNAIL_MIGRATION.md` for details on the ImageMagick to Pillow/PyMuPDF migration
- **Pillow Quick Start**: See `PILLOW_QUICKSTART.md` for getting started with the new thumbnail system
- **PyMuPDF vs pdf2image**: See `PYMUPDF_VS_PDF2IMAGE.md` for PDF rendering comparison

## 🛡️ Subset Processing Safeguard

**Important: Existing Azure URLs are Protected**

When processing a subset of files through MDI, the application now includes intelligent safeguards to prevent accidental data loss:

### How It Works

The Update CSV function uses **smart URL preservation logic** when updating Azure blob URLs (`object_location`, `image_small`, `image_thumb`):

**URLs are Updated when:**
- ✅ The field is empty or contains no data
- ✅ The existing URL contains the filename you're currently processing
- ✅ The field contains `NaN` or an empty string

**URLs are Preserved when:**
- 🔒 The existing URL contains a different filename (not in current batch)
- 🔒 Files from previous processing runs maintain their URLs
- 🔒 Non-matching rows keep their existing Azure links intact
- 🔒 Compound objects (`display_template: compound_object` or `multiple`) are never modified

### Compound Object Protection

Rows with `display_template` set to `compound_object` or `multiple` are **completely skipped** during URL updates because:
- They have no object content of their own
- Their `object_location` should remain empty
- Their `image_small` and `image_thumb` may contain custom representations (e.g., poster images)
- Child objects provide the actual content

### Example Scenario

```
Your CSV has 100 rows with Azure URLs from previous processing.
You select 5 new images to process.

Result:
- The 5 matching rows get updated with new Azure URLs ✅
- The other 95 rows keep their existing Azure URLs unchanged 🔒
```

### Benefits

- **Safe Subset Processing**: Process files in batches without losing previous work
- **No Accidental Deletions**: Existing Azure URLs won't be cleared
- **Flexible Workflows**: Update specific files while preserving the rest
- **Detailed Logging**: Check `mdi.log` to see which URLs were updated vs. preserved

This safeguard ensures you can confidently work with subsets of your collection without accidentally clearing metadata from files not included in the current processing batch.

## 🏢 About

Developed for Grinnell College Libraries to streamline the digital object ingest process for CollectionBuilder static sites.

## 🔗 Related Repository

For Alma Digital workflows, see the **manage-digital-ingest-flet-Alma** repository.
