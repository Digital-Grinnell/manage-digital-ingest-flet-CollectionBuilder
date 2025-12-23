# Quick Start Guide: Fixing Transcript CSV Files

## What This Script Does

The `fix_transcripts.py` script converts transcript CSV files from various formats (like those from Whisper, Otter.ai, or other transcription services) into the CollectionBuilder-compatible format.

## ✅ Successful Test Results

The script has been tested and works correctly with:

1. **Capitalized headers** (`Timestamp,Speaker,Transcript`) → converted to lowercase
2. **Semicolon delimiters** → converted to commas
3. **Alternative column names** (e.g., `Start Timestamp`) → mapped to standard names
4. **Multiple formats at once** → batch processing

### Example Test Run

```bash
$ python3 utilities/fix_transcripts.py

Processing transcript directory: /Users/.../manage-digital-ingest-flet-CollectionBuilder/_data/transcripts
Processing sample_interview.csv...
  ✓ Fixed sample_interview.csv (4 rows)
Processing test_semicolon.csv...
  ✓ Fixed test_semicolon.csv (3 rows)

Done!
```

## How to Use

### Step 1: Place your transcript CSV files

Put your transcript CSV files in one of these locations:
- `_data/transcripts/` (recommended - this is where CollectionBuilder looks)
- Any other directory (you'll specify the path when running the script)

### Step 2: Run the script

**Option A: Fix all transcripts in the default location**
```bash
python3 utilities/fix_transcripts.py
```

**Option B: Fix a specific file**
```bash
python3 utilities/fix_transcripts.py path/to/your/transcript.csv
```

**Option C: Fix all CSV files in a specific directory**
```bash
python3 utilities/fix_transcripts.py path/to/directory/
```

### Step 3: Verify the results

Check the output - the script will tell you:
- Which files were processed
- How many rows were in each file
- Any errors encountered

## What Gets Fixed

### Before (various formats):
```csv
Timestamp,Speaker,Transcript
Start Timestamp;Speaker;Transcript
timestamp;speaker;words
```

### After (standardized):
```csv
timestamp,speaker,words
```

## Common Scenarios

### Scenario 1: Whisper Transcription Output
Your auto-transcribed file has headers like `Start Timestamp,Speaker,Transcript`

**Solution:**
```bash
python3 utilities/fix_transcripts.py your_whisper_output.csv
```

### Scenario 2: Batch Processing Multiple Interviews
You have 10 interview transcripts in a folder

**Solution:**
```bash
python3 utilities/fix_transcripts.py path/to/interviews/
```

### Scenario 3: Single File Quick Fix
You have one transcript that needs fixing

**Solution:**
```bash
python3 utilities/fix_transcripts.py _data/transcripts/interview_2024.csv
```

## Supported Input Formats

The script recognizes these variations:

| Field | Recognized Variations |
|-------|----------------------|
| timestamp | `timestamp`, `Timestamp`, `Start Timestamp`, `start timestamp` |
| speaker | `speaker`, `Speaker` |
| words | `words`, `Transcript`, `transcript` |

## Notes

- The script **overwrites** the original file with the fixed version
- Empty rows are automatically removed
- Extra whitespace is trimmed
- The output always uses comma delimiters, regardless of input
- UTF-8 encoding is used

## Next Steps

After fixing your transcript CSVs:

1. Make sure the files are in `_data/transcripts/`
2. Ensure your metadata CSV references these transcripts correctly
3. The transcript files will now work with CollectionBuilder's transcript templates

## Need Help?

See the full documentation in [utilities/README.md](README.md)
