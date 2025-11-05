# Manage Digital Ingest: CollectionBuilder Edition

A Flet-based Python application for managing Grinnell College ingest of digital objects to CollectionBuilder static sites.

## 🚀 Quick Start

### Running the Application

The easiest way to run the application is using the provided `run.sh` script:

```bash
./run.sh
```

**What it does:**
1. Checks if a Python virtual environment (`.venv`) exists
2. Creates the virtual environment if it doesn't exist
3. Activates the virtual environment
4. Installs/upgrades required dependencies from `python-requirements.txt`
5. Launches the Flet application

**First-time setup:**
```bash
chmod +x run.sh  # Make the script executable (only needed once)
./run.sh         # Run the application
```

**Requirements:**
- Python 3.7 or higher
- Bash shell (macOS, Linux, or Windows with Git Bash/WSL)

## 📖 Overview

This CollectionBuilder-specific version of Manage Digital Ingest helps you:

- Prepare digital image collections for CollectionBuilder static sites
- Match CSV metadata with corresponding image files using fuzzy search
- Generate derivative images (thumbnails and small versions)
- Update CSV files with CollectionBuilder-specific metadata (object IDs, parent/child relationships)
- Upload files to Azure Blob storage for CollectionBuilder
- Maintain session state across multiple work sessions

## 🎯 Key Features for CollectionBuilder

- **CollectionBuilder Workflow Only**: Configured specifically for CollectionBuilder workflows
- **Fuzzy Filename Matching**: Automatically matches images to CSV metadata entries
- **CB Derivative Generation**: Creates thumbnails (400x400) and small images (800x800)
- **Collection Selection**: Choose target CollectionBuilder collection
- **Parent/Child Relationships**: Manages object relationships for CollectionBuilder
- **Azure Blob Storage**: Upload files to CollectionBuilder Azure storage
- **Session Preservation**: Save your work and resume later

## 📋 CollectionBuilder Workflow

1. **Settings**: App is pre-configured for CollectionBuilder mode, select target collection
2. **File Selector**: Load CSV with CB metadata, select and match image files
3. **Create Derivatives**: Generate CB thumbnails (_TN.jpg) and small images (_SMALL.jpg)
4. **Update CSV**: Apply CollectionBuilder-specific metadata updates (object IDs, parent/child)
5. **Azure Storage**: Upload files to Azure Blob storage for your CB collection
6. **Instructions**: View final workflow instructions

## 📄 Required CSV Columns for CollectionBuilder

See `_data/verified_CSV_headings_for_GCCB_projects.csv` for the complete list of valid column headings for CollectionBuilder workflows.

## 🔧 Configuration

The app automatically sets the mode to "CollectionBuilder" - no mode selection needed. Configure:
- Target CollectionBuilder collection
- File selection method (FilePicker or CSV)
- Azure storage settings
- Theme (Light/Dark)

## 📚 Documentation

- **Parent/Child Changes**: See `PARENT-CHILD-CHANGES.md` for details on parent/child object processing
- **Development History**: See `HISTORY.md` for feature development timeline

## 🏢 About

Developed for Grinnell College Libraries to streamline the digital object ingest process for CollectionBuilder static sites.

## 🔗 Related

For Alma Digital workflows, see the separate **Manage Digital Ingest: Alma Edition** application.
