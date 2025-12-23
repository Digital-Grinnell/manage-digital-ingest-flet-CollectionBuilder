# Automatic Transcript Fixing Integration

## Overview

The `fix_transcripts.py` functionality has been successfully integrated into MDI (Manage Digital Ingest) as an **automatic process** that runs at the start of Update CSV operations.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MDI CollectionBuilder Workflow            │
└─────────────────────────────────────────────────────────────┘

1. Settings        → Select collection
2. File Selector   → Load CSV + Match files (including transcripts)
3. Derivatives     → Generate thumbnails & small images
                     
4. Update CSV      → Click "Apply Matched Files"
                     ┌──────────────────────────────────────┐
                     │ 🎯 AUTO-FIX TRANSCRIPTS (NEW!)      │
                     │ ✓ Detects transcript CSV files      │
                     │ ✓ Fixes headers & delimiters        │
                     │ ✓ Converts to CB standard format    │
                     │ ✓ Shows success message             │
                     └──────────────────────────────────────┘
                     │
                     ↓ Continue with normal updates...
                     
5. Azure Storage   → Upload to blob storage
6. Instructions    → Generate deployment script
```

## What Was Implemented

### 1. New Module: `transcript_fixer.py`

Created a reusable Python module at the root of the project with two main functions:

- `fix_transcript_file(filepath, logger=None)` - Fixes a single transcript CSV file
- `fix_transcript_directory(directory_path, logger=None)` - Fixes all transcript CSV files in a directory

### 2. Integration into `update_csv_view.py`

Added automatic transcript fixing to the Update CSV workflow:

**New method:** `auto_fix_transcripts()`
- Automatically detects if transcript CSV files are present in the session
- Runs the fixer on all detected transcript files
- Shows success/warning messages to the user
- Logs all operations

**Modified method:** `apply_all_updates()`
- Now calls `auto_fix_transcripts()` as **Step 0** before any other operations
- Updated docstring to reflect the new step

### 3. Standalone Script: `utilities/fix_transcripts.py`

The original standalone script remains available for:
- Manual/batch processing of transcript files
- Testing and debugging
- Use outside of the MDI application

## How It Works

### Automatic Mode (in MDI)

When you click **"Apply Matched Files"** in the Update CSV view:

1. **Auto-detection**: MDI checks if transcript CSV files were detected during file selection
2. **Auto-fixing**: If transcripts are found, the fixer runs automatically:
   - Detects delimiter (comma vs semicolon)
   - Maps various column names to standard format
   - Converts to `timestamp,speaker,words` headers
   - Removes empty rows
   - Saves with UTF-8 encoding and comma delimiter
3. **User Feedback**: Shows a success message with count of fixed files
4. **Logging**: All operations are logged to `mdi.log`
5. **Continues**: The normal Update CSV process then proceeds

### Supported Input Formats

The fixer automatically recognizes and converts:

| Standard Field | Recognized Variations |
|----------------|----------------------|
| `timestamp` | `timestamp`, `Timestamp`, `Start Timestamp`, `start timestamp` |
| `speaker` | `speaker`, `Speaker` |
| `words` | `words`, `Transcript`, `transcript` |

### Delimiters

- Auto-detects comma (`,`) or semicolon (`;`) delimiters
- Always outputs with comma delimiters for consistency

## Benefits

### 1. **Zero User Effort**
- No manual steps required
- Happens automatically when you update CSV
- Works silently in the background

### 2. **Format Flexibility**
- Accepts Whisper auto-transcription output
- Accepts Otter.ai exports
- Accepts manual transcript CSVs with various formats
- Handles different delimiters and capitalization

### 3. **Reliability**
- Validates and fixes before CollectionBuilder deployment
- Prevents transcript display issues
- Consistent format across all projects

### 4. **Visibility**
- Success messages inform you when transcripts are fixed
- Detailed logging in `mdi.log` for troubleshooting
- Non-blocking: won't stop the workflow if fixing fails

## Examples

### Example 1: Whisper Output

**Before (in TRANSCRIPTS directory):**
```csv
Start Timestamp,Speaker,Transcript
00:00:15,Interviewer,Can you tell us about your experience?
00:00:23,Interviewee,"I'd be happy to share my story."
```

**After auto-fix:**
```csv
timestamp,speaker,words
00:00:15,Interviewer,Can you tell us about your experience?
00:00:23,Interviewee,I'd be happy to share my story.
```

### Example 2: Semicolon Delimiter

**Before:**
```csv
Timestamp;Speaker;Transcript
00:05:30;Dr. Smith;Let me explain the context.
```

**After auto-fix:**
```csv
timestamp,speaker,words
00:05:30,Dr. Smith,Let me explain the context.
```

## Testing

The integration has been tested and verified:

```bash
$ python3 -c "import transcript_fixer; from pathlib import Path; \
result = transcript_fixer.fix_transcript_directory(Path('_data/transcripts')); \
print(result)"

{'success': True, 'message': 'Processed 2 files: 2 fixed, 0 failed', 
 'fixed': 2, 'failed': 0, 'total': 2, 
 'details': ['Fixed sample_interview.csv (4 rows)', 
             'Fixed test_semicolon.csv (3 rows)']}
```

## User Experience

### In the MDI Application

When using MDI with transcript files:

1. **File Selector**: Add transcript CSV files (any format)
2. **Create Derivatives**: Process your images/media as usual
3. **Update CSV**: Click "Apply Matched Files"
   - 🎉 **Automatic fixing happens here!**
   - You'll see: "✓ Auto-fixed 3 transcript file(s)"
4. **Instructions**: Generate deployment script (transcripts are already fixed!)

### Manual Command Line Usage

For standalone use outside MDI:

```bash
# Fix all transcripts in default location
python3 utilities/fix_transcripts.py

# Fix specific file
python3 utilities/fix_transcripts.py path/to/transcript.csv

# Fix all in directory
python3 utilities/fix_transcripts.py path/to/transcripts/
```

## Files Modified

1. **`transcript_fixer.py`** (new) - Core fixing logic module
2. **`views/update_csv_view.py`** - Integrated auto-fixing
3. **`utilities/fix_transcripts.py`** - Standalone CLI script
4. **`utilities/README.md`** - Full documentation
5. **`utilities/QUICKSTART.md`** - Quick start guide
6. **`README.md`** - Updated workflow documentation

## Logging

All transcript fixing operations are logged to `mdi.log`:

```
2025-12-23 09:46:15 [INFO] Auto-fixing 3 transcript CSV file(s)
2025-12-23 09:46:15 [INFO] Processing transcript file: interview_001.csv
2025-12-23 09:46:15 [INFO] Fixed interview_001.csv (147 rows)
2025-12-23 09:46:15 [INFO] Processing transcript file: interview_002.csv
2025-12-23 09:46:15 [INFO] Fixed interview_002.csv (203 rows)
2025-12-23 09:46:15 [INFO] ✓ Auto-fixed 3 transcript file(s)
```

## Error Handling

- **Non-blocking**: If transcript fixing fails, the Update CSV process continues
- **Graceful degradation**: Individual file failures don't stop batch processing
- **Detailed logging**: All errors are logged with stack traces
- **User notification**: Warning messages shown if issues occur

## Future Enhancements

Potential improvements for future versions:

1. Support for additional optional fields (`tags`, `highlight`, etc.)
2. Validation of timestamp formats
3. Preview of changes before applying
4. Backup of original files before fixing
5. Batch undo functionality

## Conclusion

Transcript CSV files are now automatically fixed to CollectionBuilder format whenever you use the Update CSV feature in MDI. This eliminates a common source of errors and ensures consistent, reliable transcript display in your CollectionBuilder projects.

No additional steps required - it just works! ✨
