"""
Transcript CSV Fixer Module

This module provides utility functions to fix transcript CSV files to conform
to CollectionBuilder format (timestamp,speaker,words).
"""

import csv
import io
from pathlib import Path


def fix_transcript_file(filepath, logger=None):
    """
    Fix a single transcript CSV file to CollectionBuilder format.
    
    Args:
        filepath: Path to the transcript CSV file (str or Path object)
        logger: Optional logger object for logging operations
        
    Returns:
        tuple: (success: bool, message: str, row_count: int)
    """
    filepath = Path(filepath)
    
    if logger:
        logger.info(f"Processing transcript file: {filepath.name}")
    
    try:
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            msg = f"Warning: {filepath.name} is empty"
            if logger:
                logger.warning(msg)
            return False, msg, 0
        
        lines = content.strip().split('\n')
        header = lines[0]
        
        # Detect delimiter from header
        delimiter = ';' if header.count(';') > header.count(',') else ','
        
        # Parse the CSV
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        
        # Prepare output rows
        output_rows = []
        
        for row in reader:
            # Handle empty column name (leading comma/semicolon)
            if '' in row and not row[''].strip():
                del row['']
            
            # Map various column names to the standard format
            timestamp = ''
            speaker = ''
            words = ''
            
            # Find timestamp (prefer Start Timestamp over End Timestamp)
            for key in ['timestamp', 'Timestamp', 'Start Timestamp', 'start timestamp']:
                if key in row and row[key]:
                    timestamp = row[key].strip()
                    break
            
            # Find speaker
            for key in ['speaker', 'Speaker']:
                if key in row and row[key]:
                    speaker = row[key].strip()
                    break
            
            # Find words/transcript
            for key in ['words', 'Transcript', 'transcript']:
                if key in row and row[key]:
                    words = row[key].strip()
                    break
            
            # Skip completely empty rows
            if not timestamp and not speaker and not words:
                continue
                
            output_rows.append({
                'timestamp': timestamp,
                'speaker': speaker,
                'words': words
            })
        
        # Write back to file with comma delimiter
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'speaker', 'words'])
            writer.writeheader()
            writer.writerows(output_rows)
        
        msg = f"Fixed {filepath.name} ({len(output_rows)} rows)"
        if logger:
            logger.info(msg)
        
        return True, msg, len(output_rows)
        
    except Exception as e:
        msg = f"Error processing {filepath.name}: {str(e)}"
        if logger:
            logger.error(msg)
        return False, msg, 0


def fix_transcript_directory(directory_path, logger=None):
    """
    Fix all transcript CSV files in a directory.
    
    Args:
        directory_path: Path to directory containing transcript CSV files
        logger: Optional logger object for logging operations
        
    Returns:
        dict: Results dictionary with counts and messages
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists() or not directory_path.is_dir():
        msg = f"Directory not found: {directory_path}"
        if logger:
            logger.error(msg)
        return {
            'success': False,
            'message': msg,
            'fixed': 0,
            'failed': 0,
            'total': 0
        }
    
    csv_files = list(directory_path.glob('*.csv'))
    
    if not csv_files:
        msg = f"No CSV files found in {directory_path}"
        if logger:
            logger.info(msg)
        return {
            'success': True,
            'message': msg,
            'fixed': 0,
            'failed': 0,
            'total': 0
        }
    
    results = {
        'success': True,
        'message': '',
        'fixed': 0,
        'failed': 0,
        'total': len(csv_files),
        'details': []
    }
    
    for csv_file in csv_files:
        success, msg, row_count = fix_transcript_file(csv_file, logger)
        if success:
            results['fixed'] += 1
        else:
            results['failed'] += 1
            results['success'] = False
        results['details'].append(msg)
    
    results['message'] = f"Processed {results['total']} files: {results['fixed']} fixed, {results['failed']} failed"
    
    return results
