# Transcript CSV Fixer for CollectionBuilder

This utility script fixes transcript CSV files to conform to the CollectionBuilder format.

## Purpose

CollectionBuilder transcript templates expect transcript CSV files to have specific lowercase field names:
- `timestamp` - The timestamp for the transcript line
- `speaker` - The name of the speaker  
- `words` - The actual transcript text

This script converts various transcript CSV formats to this standard format.

## Common Issues Fixed

- ❌ Capitalized headers: `Timestamp,Speaker,Transcript`
- ❌ Wrong field name: `Transcript` instead of `words`
- ❌ Different delimiters (semicolon vs comma)
- ❌ Extra empty columns
- ✅ Converts to correct format: `timestamp,speaker,words`

## Usage

### Process all CSV files in the default transcripts directory
```bash
python3 utilities/fix_transcripts.py
```

This looks for transcript CSV files in `_data/transcripts/`

### Process a specific transcript CSV file
```bash
python3 utilities/fix_transcripts.py path/to/transcript.csv
```

### Process all CSV files in a directory
```bash
python3 utilities/fix_transcripts.py path/to/directory/
```

## Supported Input Formats

The script can recognize and convert the following column names:

**Timestamp columns:**
- `timestamp` (already correct)
- `Timestamp` (capitalized)
- `Start Timestamp` (Whisper output)
- `start timestamp` (lowercase variant)

**Speaker columns:**
- `speaker` (already correct)
- `Speaker` (capitalized)

**Words/transcript columns:**
- `words` (already correct)
- `Transcript` (capitalized - common in auto-transcription tools)
- `transcript` (lowercase)

## Examples

### Example 1: Fix a single transcript
```bash
python3 utilities/fix_transcripts.py _data/transcripts/dg_1752254695.csv
```

Output:
```
Processing dg_1752254695.csv...
  ✓ Fixed dg_1752254695.csv (147 rows)
Done!
```

### Example 2: Process a directory of transcripts
```bash
python3 utilities/fix_transcripts.py storage/temp/transcripts/
```

Output:
```
Processing directory: storage/temp/transcripts/
Processing interview_001.csv...
  ✓ Fixed interview_001.csv (203 rows)
Processing interview_002.csv...
  ✓ Fixed interview_002.csv (156 rows)
Done!
```

## What the Script Does

1. **Detects delimiter** - Automatically detects whether the CSV uses commas or semicolons
2. **Maps column names** - Finds timestamp, speaker, and words columns regardless of capitalization
3. **Removes empty columns** - Cleans up leading delimiters that create empty columns
4. **Standardizes output** - Always outputs with comma delimiters and lowercase headers
5. **Preserves data** - Keeps all transcript content while fixing format issues

## Transcript CSV Format Reference

After processing, your transcript CSV files will have this format:

```csv
timestamp,speaker,words
00:00:15,Interviewer,Can you tell us about your experience?
00:00:23,Interviewee,I'd be happy to share my story...
00:01:45,Interviewer,That's fascinating. What happened next?
```

### Optional Fields

CollectionBuilder also supports these optional fields in transcript CSVs:
- `tags` - Semicolon-separated tags for filtering
- `highlight` - Mark important sections
- `timelink` - Custom time linking

## Notes

- The script creates backups by writing the fixed version directly over the original file
- Empty rows (no timestamp, speaker, or words) are automatically removed
- Whitespace is trimmed from all fields
- UTF-8 encoding is used for all file operations

## Troubleshooting

**Q: My transcripts aren't displaying in CollectionBuilder**
A: Run this script on your transcript CSV files to ensure they have the correct format.

**Q: I get an encoding error**
A: The script expects UTF-8 encoded files. Convert your CSV to UTF-8 before processing.

**Q: The script says "no CSV files found"**  
A: Make sure your transcript CSV files are in `_data/transcripts/` or specify the directory path.

## Source

This script was adapted from the [GCCB-Georgia-Dentel-Project](https://github.com/Digital-Grinnell/GCCB-Georgia-Dentel-Project) repository's `utilities/fix_transcripts.py` script.
