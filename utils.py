import flet as ft
import os
import utils
from thumbnail import generate_thumbnail
from subprocess import call
# from azure.identity import DefaultAzureCredential
# from azure.storage.blob import BlobServiceClient
import json
import sys
import logging
import time

# Unique ID generation
# ----------------------------------------------------------------------
def generate_unique_id(page):
    """
    Generate a unique ID based on current epoch time.
    Checks session storage to ensure no duplicates exist.
    If a duplicate is found, increments the epoch value until unique.
    
    Args:
        page: The Flet page object containing session data
    
    Returns:
        str: Unique ID formatted as "dg_<epoch_time>"
    
    Example:
        >>> generate_unique_id(page)
        'dg_1729123456'
    """
    # Initialize the set of generated IDs in session if not present
    if not hasattr(page.session, 'generated_ids'):
        page.session.generated_ids = set()
    
    # Start with current epoch time
    epoch_time = int(time.time())
    unique_id = f"dg_{epoch_time}"
    
    # Increment until we find a unique ID
    while unique_id in page.session.generated_ids:
        epoch_time += 1
        unique_id = f"dg_{epoch_time}"
    
    # Store the new ID in session
    page.session.generated_ids.add(unique_id)
    
    return unique_id

# Simple string matching functions
# ----------------------------------------------------------------------
def calculate_string_similarity(str1, str2):
    """
    Calculate similarity between two strings using a simple approach.
    Returns a percentage (0-100) of how similar the strings are.
    """
    if str1 == str2:
        return 100
    
    # Simple substring matching approach
    if str1 in str2 or str2 in str1:
        # Calculate ratio based on length overlap
        overlap = min(len(str1), len(str2))
        total = max(len(str1), len(str2))
        return int((overlap / total) * 100)
    
    # Count common characters
    common_chars = 0
    str1_chars = list(str1)
    str2_chars = list(str2)
    
    for char in str1_chars:
        if char in str2_chars:
            common_chars += 1
            str2_chars.remove(char)
    
    # Calculate similarity based on common characters
    total_chars = max(len(str1), len(str2))
    if total_chars == 0:
        return 0
    
    return int((common_chars / total_chars) * 100)

def sanitize_filename(filename):
    """
    Sanitize a filename by replacing spaces and special characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename with spaces replaced by underscores,
             special characters removed, and hyphens cleaned up
    """
    import re
    # Replace spaces with underscores
    sanitized = filename.replace(' ', '_')
    # Remove or replace other problematic characters (keep word chars, hyphens, underscores, dots)
    sanitized = re.sub(r'[^\w\-_\.]', '_', sanitized)
    # Clean up multiple underscores around hyphens: _-_ or -_ or _- becomes just -
    sanitized = re.sub(r'_*-_*', '-', sanitized)
    # Clean up any remaining multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized

def perform_fuzzy_search(base_path, target_filename, threshold=90):
    """
    Recursively search for files in base_path and find the best match for target_filename
    using simple string matching.
    
    Args:
        base_path (str): The directory to start searching from
        target_filename (str): The filename to match against
        threshold (int): The minimum match percentage to consider a match (0-100)
        
    Returns:
        tuple: (best_match_path, best_match_ratio) or (None, 0) if no match found
    """
    try:
        best_match_path = None
        best_match_ratio = 0
        
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                # Calculate simple string similarity ratio
                ratio = calculate_string_similarity(filename.lower(), target_filename.lower())
                
                # Update best match if this ratio is higher
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_path = os.path.join(root, filename)
                    
                    # If we found a perfect match, we can return immediately
                    if ratio == 100:
                        return (best_match_path, ratio)
        
        # Always return the best match path and ratio found, regardless of threshold
        # The caller will decide whether to accept it based on the threshold
        return (best_match_path, best_match_ratio)
            
    except Exception as e:
        logging.error(f"Error in fuzzy search: {str(e)}")
        return (None, 0)


def perform_fuzzy_search_batch(base_path, target_filenames, threshold=90, progress_callback=None, cancel_check=None):
    """
    Perform fuzzy search for multiple filenames sequentially with progress tracking and cancellation support.
    
    Args:
        base_path (str): The directory to start searching from
        target_filenames (list): List of filenames to match against
        threshold (int): The minimum fuzzy match ratio to consider a match (0-100)
        progress_callback (callable): Optional callback function to report progress (0.0 to 1.0)
        cancel_check (callable): Optional function that returns True if search should be cancelled
        
    Returns:
        dict: Dictionary mapping target filenames to (match_path, ratio) tuples, or None if cancelled
    """
    results = {}
    total_files = len(target_filenames)
    
    if progress_callback:
        # Start with 0% progress
        progress_callback(0)
    
    for index, filename in enumerate(target_filenames):
        # Check for cancellation
        if cancel_check and cancel_check():
            logging.info("Fuzzy search cancelled by user")
            return None
            
        logging.info(f"Searching for match to '{filename}' ({index + 1}/{total_files})")
        
        # Update progress after each file
        if progress_callback:
            progress = (index + 1) / total_files
            progress_callback(progress)
            
        match_path, ratio = perform_fuzzy_search(base_path, filename, threshold)
        results[filename] = (match_path, ratio)
        
        # Log the result
        if match_path and ratio >= threshold:
            logging.info(f"Found match for '{filename}': {match_path} ({ratio}% match)")
        else:
            logging.info(f"No match found for '{filename}' meeting {threshold}% threshold")
    
    # Only show 100% if we completed the search (not cancelled)
    if progress_callback:
        progress_callback(1.0)
        
    return results

# # Example AppBar component
# def build_app_bar( ):
#     return ft.AppBar(title=ft.Text("My App"), actions=[
#         ft.IconButton(icon=ft.Icons.MENU),
#         ]
#     )

# # Example AppBar component
# def get_app_bar(page=None):
#     if page:
#         page.appbar=ft.AppBar(
#                 title=ft.Text("Flet-X: Manage Digital Ingest"),
#                 actions=[
#                     ft.FilledButton(
#                         text="Home",
#                         # on_click=data.go(data.route_init),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Counter",
#                         # on_click=data.go("/counter/test/0"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Picker",
#                         # on_click=data.go("/picker"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Mode",
#                         # on_click=data.go("/mode"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Show Data",
#                         # on_click=data.go("/show_data"),
#                     ),
#                     ft.VerticalDivider(opacity=0),
#                     ft.FilledButton(
#                         text="Exit",
#                         # on_click=data.go("/exit"),
#                     ),
#                     # One more divider for better button spacing
#                     ft.VerticalDivider(opacity=0),
#                 ],
#                 bgcolor="#121113",
#             )
#         return pageappbar





# Read markdown file from _data directory
# ------------------------------------------------------------------------------
def read_markdown(filename):
    """
    Read markdown content from a file.
    
    Args:
        filename (str): The filename (with path) to read
        
    Returns:
        str: The markdown content
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Markdown file not found: {filename}")
        return f"# Error\n\nMarkdown file not found: {filename}"
    except Exception as e:
        logging.error(f"Error reading markdown file {filename}: {e}")
        return f"# Error\n\nError reading markdown file: {str(e)}"


# Read config from _data/config.json and return as 'config'
# ------------------------------------------------------------------------------
def read_config(page=None):
    # Load configuration from _data/config.json
    with open('_data/config.json', 'r') as config_file:
        config = json.load(config_file) 

    # Print config values to console for debugging and store them in page.session
    print(f"Values from _data/config.json... ")
    for key, value in config.items( ):
        print(f"{key}: {value}")
        # Store config values in page session if needed
        if page:
            page.session.set(key, value)  

    return config


# Helper function to get session value with default
# ------------------------------------------------------------------------------
def session_get(page, key, default=None):
    """
    Get a value from page.session with a default fallback.
    
    Args:
        page: The Flet page object
        key (str): The session key to retrieve
        default: The default value to return if key is not found or is None
        
    Returns:
        The session value or the default value
    """
    value = page.session.get(key)
    return value if value is not None else default


# Helper function to display message in the SnackBar
# ------------------------------------------------------------
def show_message(page, text, is_error=False):
    """Helper function to update and show the SnackBar."""
    logger = page.session.get("logger")
    if is_error:
        logger.error(text)
    else:
        logger.info(text)
    
    # Ensure snackbar exists
    if not hasattr(page, 'snack_bar') or page.snack_bar is None:
        page.snack_bar = ft.SnackBar(content=ft.Text(text))
    
    page.snack_bar.content.value = text
    page.snack_bar.bgcolor = ft.Colors.RED_600 if is_error else ft.Colors.GREEN_600
    page.open(page.snack_bar)
    page.update()


# Validate CSV headings against verified heading files
# ------------------------------------------------------------
def validate_csv_headings(csv_file_path, mode):
    """
    Validate CSV file headings against verified heading files based on mode.
    
    Args:
        csv_file_path: Path to the CSV file to validate
        mode: Either 'Alma' or 'CollectionBuilder'
        
    Returns:
        tuple: (is_valid: bool, unmatched_headings: list, error_message: str or None)
        - is_valid: True if all headings match (for Alma) or if file is valid (for CB)
        - unmatched_headings: List of headings that don't match verified list
        - error_message: Error message if there was a problem, None otherwise
        
    Notes:
        - For Alma mode: ALL headings in the CSV must exactly match verified headings.
          Returns unmatched headings if any are found.
        - For CollectionBuilder mode: CSV headings are checked against verified list,
          but extra headings are allowed (more permissive).
        - Order of headings does not matter, only the names.
    """
    import pandas as pd
    
    # Determine which verified headings file to use
    if mode == 'Alma':
        verified_file = os.path.join("_data", "verified_CSV_headings_for_Alma-D.csv")
    elif mode == 'CollectionBuilder':
        verified_file = os.path.join("_data", "verified_CSV_headings_for_GCCB_projects.csv")
    else:
        return (False, [], f"Invalid mode '{mode}'. Must be 'Alma' or 'CollectionBuilder'.")
    
    # Check if verified file exists
    if not os.path.exists(verified_file):
        return (False, [], f"Verified headings file not found: {verified_file}")
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        return (False, [], f"CSV file not found: {csv_file_path}")
    
    try:
        # Read the verified headings (first row only)
        verified_df = pd.read_csv(verified_file, nrows=0, dtype=str, keep_default_na=False)
        verified_headings = set(verified_df.columns.tolist())
        
        # Read the CSV file headings (first row only) with multiple encodings
        csv_df = None
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                # Read all columns as strings to prevent scientific notation
                csv_df = pd.read_csv(csv_file_path, nrows=0, encoding=encoding, dtype=str, keep_default_na=False)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if csv_df is None:
            return (False, [], f"Could not read CSV file with any supported encoding")
        
        csv_headings = set(csv_df.columns.tolist())
        
        # Find headings in CSV that are NOT in verified list
        unmatched_headings = list(csv_headings - verified_headings)
        
        # For Alma mode, be strict - no unmatched headings allowed
        if mode == 'Alma':
            if unmatched_headings:
                return (False, unmatched_headings, None)
            else:
                return (True, [], None)
        
        # For CollectionBuilder mode, be more permissive - just report unmatched
        # but don't fail validation (extra headings are OK)
        elif mode == 'CollectionBuilder':
            return (True, unmatched_headings, None)
            
    except Exception as e:
        return (False, [], f"Error validating CSV headings: {str(e)}")


def generate_alma_s3_script(temp_directory, temp_csv_filename=None):
    """
    Generate a personalized Alma AWS S3 upload script with the temp directory filled in.
    
    Args:
        temp_directory: Path to the temporary directory containing OBJS folder
        temp_csv_filename: Name of the temporary CSV file to upload (optional)
        
    Returns:
        str: The bash script content with temp_directory replaced
    """
    # Default Profile ID for Alma uploads
    default_profile_id = "6496776180004641"
    
    # Determine the CSV file reference for the script
    if temp_csv_filename:
        csv_file_path = f"{temp_directory}/{temp_csv_filename}"
    else:
        # Fallback to wildcard if filename not provided
        csv_file_path = f"{temp_directory}/*.csv"
    
    script_template = """#!/bin/bash

# Alma AWS S3 Upload Script
# This script helps upload files from the temporary directory to Alma's AWS S3 storage
# Profile ID: {profile_id} (default)
# Replace <import-id> with the value from the Alma Digital Uploader

# Step 1: Print the name and contents of the upload bucket
echo "Step 1: Listing contents of Alma S3 upload bucket..."
# List all files in the upload bucket to find your <import-id>
aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/ --recursive

echo ""
echo "Copy/paste the '/<import-id>/' portion from the output above"
echo "Then edit this script and replace <import-id> in the commands below"
echo ""
read -p "Press Enter when ready to continue with the copy commands..."

# Step 2a: Copy temporary CSV file to S3
# Using Profile ID: {profile_id}
# Note: values.csv is handled automatically by Alma and should not be uploaded
echo ""
echo "Step 2a: Copying temporary CSV file to Alma S3 storage..."
# Upload the metadata CSV file containing digital object information
aws s3 cp {csv_file_path} s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/{profile_id}/<import-id>/

# Step 2b: Copy OBJS directory to S3
echo ""
echo "Step 2b: Copying OBJS directory to Alma S3 storage..."
# Upload all master/original digital object files from the OBJS directory
aws s3 cp {temp_directory}/OBJS/ s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/{profile_id}/<import-id>/ --recursive

# Step 2c: Copy TN directory to S3
echo ""
echo "Step 2c: Copying TN directory to Alma S3 storage..."
# Upload all thumbnail images from the TN directory
aws s3 cp {temp_directory}/TN/ s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/{profile_id}/<import-id>/ --recursive

# Step 3: Verify the upload
echo ""
echo "Step 3: Verifying upload..."
# List all uploaded files to confirm successful transfer
aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/{profile_id}/ --recursive

echo ""
echo "Once verified, return to Alma to complete the import operation"
echo ""
echo "Optional: After Alma import is complete, you can clean up the S3 bucket:"
echo ""
# Remove all files from the upload bucket after successful import (optional cleanup)
aws s3 rm s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/{profile_id}/ --recursive
"""
    
    # Replace the placeholders
    return script_template.format(
        temp_directory=temp_directory, 
        profile_id=default_profile_id,
        csv_file_path=csv_file_path
    )
