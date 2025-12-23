"""
Update CSV View for Manage Digital Ingest Application

This module contains the UpdateCSVView class for updating CSV files with
matched filenames and metadata.
"""

import flet as ft
from views.base_view import BaseView
import os
import shutil
import pandas as pd
from datetime import datetime
import utils
import transcript_fixer


class UpdateCSVView(BaseView):
    """
    Update CSV view class for modifying CSV files with matched file data.
    Only enabled when CSV file selection is active.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the update CSV view."""
        super().__init__(page)
        self.csv_data = None
        self.csv_data_original = None  # Store original data for comparison
        self.csv_path = None
        self.temp_csv_path = None
        self.selected_column = None
        self.data_table = None
        self.edits_applied = False  # Track whether any edits have been applied
    
    def copy_csv_to_temp(self, source_path):
        """
        Copy CSV file to temporary directory with timestamp.
        
        Args:
            source_path: Path to the source CSV file
            
        Returns:
            str: Path to the copied CSV file
        """
        try:
            # Get temp directory from session
            temp_dir = self.page.session.get("temp_directory")
            if not temp_dir:
                # Create a new temp directory if one doesn't exist
                temp_dir = os.path.join("storage", "temp", f"csv_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                os.makedirs(temp_dir, exist_ok=True)
                self.page.session.set("temp_directory", temp_dir)
            
            # Get the base filename and sanitize it
            base_name = os.path.basename(source_path)
            name, ext = os.path.splitext(base_name)
            sanitized_name = utils.sanitize_filename(name)
            
            # Add timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{sanitized_name}_{timestamp}{ext}"
            
            # Create the destination path
            dest_path = os.path.join(temp_dir, new_filename)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied CSV file to: {dest_path}")
            
            return dest_path
            
        except Exception as e:
            self.logger.error(f"Error copying CSV to temp: {e}")
            return None
    
    def load_csv_data(self, csv_path):
        """
        Load CSV data into a pandas DataFrame.
        Skips comment rows (rows where first column starts with #).
        Fixes illegal quoting by handling embedded quotes.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    # Read all columns as strings to prevent scientific notation and type conversion
                    # Use quoting=csv.QUOTE_ALL to handle embedded quotes properly
                    import csv
                    self.csv_data = pd.read_csv(
                        csv_path, 
                        encoding=encoding, 
                        dtype=str, 
                        keep_default_na=False,
                        quoting=csv.QUOTE_MINIMAL,
                        on_bad_lines='warn'  # Warn but continue on bad lines
                    )
                    
                    # Store comment rows (where first column starts with #) for later restoration
                    self.comment_rows = []
                    if len(self.csv_data.columns) > 0:
                        first_col = self.csv_data.columns[0]
                        comment_mask = self.csv_data[first_col].astype(str).str.strip().str.startswith('#')
                        comment_count = comment_mask.sum()
                        
                        if comment_count > 0:
                            # Store comment rows as list of dictionaries
                            self.comment_rows = self.csv_data[comment_mask].to_dict('records')
                            self.logger.info(f"Preserved {comment_count} comment row(s) starting with '#'")
                            # Filter out comments for processing
                            self.csv_data = self.csv_data[~comment_mask]
                            # Reset index after filtering
                            self.csv_data = self.csv_data.reset_index(drop=True)
                    
                    # Fix embedded double quotes throughout the DataFrame
                    quote_fixes = 0
                    for col in self.csv_data.columns:
                        for idx in self.csv_data.index:
                            value = str(self.csv_data.at[idx, col])
                            # Look for embedded double quotes (not empty values)
                            if value and value != 'nan' and '"' in value:
                                # Replace double quotes with single quotes
                                fixed_value = value.replace('"', "'")
                                self.csv_data.at[idx, col] = fixed_value
                                quote_fixes += 1
                    
                    if quote_fixes > 0:
                        self.logger.info(f"Fixed {quote_fixes} cell(s) with embedded double quotes during load")
                    
                    # Store a copy of the original data for comparison
                    self.csv_data_original = self.csv_data.copy()
                    self.csv_path = csv_path
                    self.logger.info(f"Loaded CSV with {len(self.csv_data)} rows and {len(self.csv_data.columns)} columns")
                    return True
                except UnicodeDecodeError:
                    continue
            
            self.logger.error("Failed to load CSV with any supported encoding")
            return False
            
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
            return False
    
    def save_csv_data(self):
        """
        Save the current CSV data back to file.
        Fixes illegal quoting by replacing embedded double quotes with single quotes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.csv_data is not None and self.temp_csv_path:
                # Fix illegal quoting: replace embedded double quotes with single quotes
                quote_fixes = 0
                for col in self.csv_data.columns:
                    # Check each cell in the column
                    for idx in self.csv_data.index:
                        value = str(self.csv_data.at[idx, col])
                        # Look for embedded double quotes (not empty values)
                        if value and value != 'nan' and '"' in value:
                            # Replace double quotes with single quotes
                            fixed_value = value.replace('"', "'")
                            self.csv_data.at[idx, col] = fixed_value
                            quote_fixes += 1
                            self.logger.info(f"Fixed illegal quote in row {idx}, column '{col}': changed {value.count('\"')} double quote(s) to single quote(s)")
                
                if quote_fixes > 0:
                    self.logger.info(f"Fixed {quote_fixes} cell(s) with embedded double quotes")
                
                # Replace straight apostrophes with curly apostrophes for better CSV compatibility
                apostrophe_fixes = 0
                for col in self.csv_data.columns:
                    if self.csv_data[col].dtype == 'object':
                        mask = self.csv_data[col].astype(str).str.contains("'", na=False)
                        if mask.any():
                            for idx in self.csv_data[mask].index:
                                original = str(self.csv_data.at[idx, col])
                                if original and original != 'nan' and "'" in original:
                                    fixed = original.replace("'", "'")
                                    self.csv_data.at[idx, col] = fixed
                                    apostrophe_fixes += 1
                
                if apostrophe_fixes > 0:
                    self.logger.info(f"Converted {apostrophe_fixes} cell(s) with straight apostrophes to curly apostrophes")
                
                # Re-insert comment rows at the beginning if they exist
                if hasattr(self, 'comment_rows') and self.comment_rows:
                    import pandas as pd
                    # Create DataFrame from comment rows
                    comment_df = pd.DataFrame(self.comment_rows)
                    # Concatenate comment rows at the beginning
                    self.csv_data = pd.concat([comment_df, self.csv_data], ignore_index=True)
                    self.logger.info(f"Re-inserted {len(self.comment_rows)} comment row(s) at the beginning")
                
                # Save without index and preserve all values as text (no scientific notation)
                # Use quoting=csv.QUOTE_MINIMAL to only quote when necessary
                # Always use UTF-8 encoding (no BOM)
                import csv
                self.csv_data.to_csv(
                    self.temp_csv_path, 
                    index=False, 
                    encoding='utf-8', 
                    quoting=csv.QUOTE_MINIMAL
                )
                self.logger.info(f"Saved CSV data to: {self.temp_csv_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")
            return False
    
    def update_cell(self, row_index, column_name, new_value):
        """
        Update a specific cell in the CSV data.
        
        Args:
            row_index: The row index (0-based)
            column_name: The column name
            new_value: The new value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.csv_data is not None:
                self.csv_data.at[row_index, column_name] = new_value
                self.logger.info(f"Updated cell [{row_index}, {column_name}] = {new_value}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating cell: {e}")
            return False
    
    def auto_fix_transcripts(self):
        """
        Automatically fix transcript CSV files if any are detected in the session.
        This ensures transcript files conform to CollectionBuilder format (timestamp,speaker,words).
        """
        try:
            # Check if there are transcript files in the session
            temp_transcripts_dir = self.page.session.get("temp_transcripts_directory")
            transcript_csv_files = self.page.session.get("transcript_csv_files") or []
            
            if not temp_transcripts_dir or not transcript_csv_files:
                self.logger.info("No transcript files detected - skipping auto-fix")
                return
            
            if not os.path.exists(temp_transcripts_dir):
                self.logger.warning(f"Transcript directory not found: {temp_transcripts_dir}")
                return
            
            self.logger.info(f"Auto-fixing {len(transcript_csv_files)} transcript CSV file(s)")
            
            # Fix all transcripts in the directory
            results = transcript_fixer.fix_transcript_directory(temp_transcripts_dir, self.logger)
            
            if results['success']:
                msg = f"✓ Auto-fixed {results['fixed']} transcript file(s)"
                self.logger.info(msg)
                if results['fixed'] > 0:
                    # Show success message to user
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(msg),
                        bgcolor=ft.Colors.GREEN_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            else:
                msg = f"⚠ Transcript auto-fix had issues: {results['message']}"
                self.logger.warning(msg)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(msg),
                    bgcolor=ft.Colors.ORANGE_600
                )
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as e:
            self.logger.error(f"Error during transcript auto-fix: {e}")
            # Don't fail the entire update process if transcript fixing fails
            import traceback
            traceback.print_exc()
    
    def apply_all_updates(self, e):
        """
        Combined function that:
        1. Auto-fixes transcript CSV files (if any detected)
        2. Applies matched filenames to existing rows
        3. Appends a new row for the CSV file itself
        4. Populates dginfo field for all rows with temp CSV filename
        """
        try:
            # Step 0: Auto-fix transcript CSV files if detected
            self.auto_fix_transcripts()
            
            # Get session data
            temp_file_info = self.page.session.get("temp_file_info") or []
            csv_filenames_for_matched = self.page.session.get("csv_filenames_for_matched") or []
            temp_csv_filename = self.page.session.get("temp_csv_filename") or ""
            original_csv_path = self.page.session.get("selected_csv_file") or ""
            current_mode = self.page.session.get("selected_mode") or "CollectionBuilder"
            
            if self.csv_data is None:
                self.logger.warning("CSV data not loaded")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No CSV data available"),
                    bgcolor=ft.Colors.ORANGE_600
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            if not temp_csv_filename:
                self.logger.warning("No temp CSV filename available")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No temporary CSV file data available"),
                    bgcolor=ft.Colors.ORANGE_600
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Get the selected column name
            column_name = self.selected_column
            if not column_name:
                self.logger.warning("Target column not configured")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Target column not configured"),
                    bgcolor=ft.Colors.ORANGE_600
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Step 1: Update existing rows with matched sanitized filenames
            updates = 0
            
            # Log initial state for debugging
            self.logger.info(f"Starting Step 1: Current mode = {current_mode}")
            self.logger.info(f"Column name to match: {column_name}")
            self.logger.info(f"temp_file_info count: {len(temp_file_info) if temp_file_info else 0}")
            self.logger.info(f"csv_filenames_for_matched count: {len(csv_filenames_for_matched) if csv_filenames_for_matched else 0}")
            self.logger.info(f"CSV columns available: {list(self.csv_data.columns)}")
            
            if temp_file_info and csv_filenames_for_matched:
                for idx, file_info in enumerate(temp_file_info):
                    sanitized_filename = file_info.get('sanitized_filename', '')
                    
                    # Get the corresponding CSV filename if available
                    if idx < len(csv_filenames_for_matched):
                        csv_filename = csv_filenames_for_matched[idx]
                    else:
                        # Fall back to original_filename for file picker workflow
                        csv_filename = file_info.get('original_filename', '')
                    
                    self.logger.info(f"Processing file {idx}: csv_filename='{csv_filename}', sanitized='{sanitized_filename}'")
                    
                    # Find the row with this CSV filename
                    mask = self.csv_data[column_name] == csv_filename
                    self.logger.info(f"Mask matches: {mask.sum()} rows")
                    
                    if mask.any():
                        row_idx = self.csv_data[mask].index[0]
                        self.logger.info(f"Found match at row index: {row_idx}")
                        
                        # Check if this is a compound object or multiple display template FIRST
                        # These have no object content of their own, so we should skip them entirely
                        display_template = ""
                        if 'display_template' in self.csv_data.columns:
                            display_template = str(self.csv_data.at[row_idx, 'display_template']).strip().lower()
                        
                        is_compound_or_multiple = display_template in ['compound_object', 'multiple']
                        
                        if is_compound_or_multiple:
                            self.logger.info(f"Row {row_idx} has display_template='{display_template}' - skipping this row entirely (no object content)")
                            continue  # Skip to next file
                        
                        if current_mode == "CollectionBuilder":
                            # In CollectionBuilder mode, populate Azure blob URLs
                            azure_base_url = "https://collectionbuilder.blob.core.windows.net"
                            selected_collection = self.page.session.get("selected_collection") or ""
                            
                            self.logger.info(f"CollectionBuilder mode - selected_collection: '{selected_collection}'")
                            
                            # Check if this is a media file
                            file_ext = os.path.splitext(sanitized_filename)[1].lower()
                            is_media_file = file_ext in ['.mp3', '.mp4', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mov', '.avi', '.mkv']
                            
                            # Build derivative filenames for smalls and thumbs
                            # Remove extension from sanitized_filename and add _SMALL.jpg and _TN.jpg
                            base_name = os.path.splitext(sanitized_filename)[0]
                            
                            # For media files, use default Azure media placeholders
                            if is_media_file:
                                small_filename = "gc_media_SMALL.jpeg"
                                thumb_filename = "gc_media_TN.jpeg"
                                self.logger.info(f"Media file detected ({file_ext}) - using default Azure placeholders for derivatives")
                            else:
                                small_filename = f"{base_name}_SMALL.jpg"
                                thumb_filename = f"{base_name}_TN.jpg"
                            
                            # Build blob URLs with collection prefix
                            if selected_collection:
                                obj_url = f"{azure_base_url}/objs/{selected_collection}/{sanitized_filename}"
                                if is_media_file:
                                    # Default media placeholders are not collection-specific
                                    small_url = f"{azure_base_url}/smalls/{small_filename}"
                                    thumb_url = f"{azure_base_url}/thumbs/{thumb_filename}"
                                else:
                                    small_url = f"{azure_base_url}/smalls/{selected_collection}/{small_filename}"
                                    thumb_url = f"{azure_base_url}/thumbs/{selected_collection}/{thumb_filename}"
                            else:
                                obj_url = f"{azure_base_url}/objs/{sanitized_filename}"
                                small_url = f"{azure_base_url}/smalls/{small_filename}"
                                thumb_url = f"{azure_base_url}/thumbs/{thumb_filename}"
                            
                            self.logger.info(f"Generated URLs - obj: {obj_url}, small: {small_url}, thumb: {thumb_url}")
                            
                            # Update the three URL columns
                            # For subset processing: only update if the URLs are empty or contain the old filename pattern
                            # This prevents accidentally clearing URLs when processing subsets of files
                            if 'object_location' in self.csv_data.columns:
                                existing_obj_url = str(self.csv_data.at[row_idx, 'object_location']).strip()
                                should_update = (
                                    not existing_obj_url or 
                                    existing_obj_url == 'nan' or 
                                    existing_obj_url == '' or
                                    csv_filename in existing_obj_url  # Update if URL contains the current filename
                                )
                                
                                if should_update:
                                    self.csv_data.at[row_idx, 'object_location'] = obj_url
                                    self.logger.info(f"Updated object_location at row {row_idx}: {obj_url}")
                                else:
                                    self.logger.info(f"Preserved existing object_location at row {row_idx}: {existing_obj_url}")
                            else:
                                self.logger.warning("object_location column not found in CSV!")
                                
                            if 'image_small' in self.csv_data.columns:
                                existing_small_url = str(self.csv_data.at[row_idx, 'image_small']).strip()
                                should_update = (
                                    not existing_small_url or 
                                    existing_small_url == 'nan' or 
                                    existing_small_url == '' or
                                    csv_filename in existing_small_url  # Update if URL contains the current filename
                                )
                                
                                if should_update:
                                    self.csv_data.at[row_idx, 'image_small'] = small_url
                                    self.logger.info(f"Updated image_small at row {row_idx}: {small_url}")
                                else:
                                    self.logger.info(f"Preserved existing image_small at row {row_idx}: {existing_small_url}")
                            else:
                                self.logger.warning("image_small column not found in CSV!")
                                
                            if 'image_thumb' in self.csv_data.columns:
                                existing_thumb_url = str(self.csv_data.at[row_idx, 'image_thumb']).strip()
                                should_update = (
                                    not existing_thumb_url or 
                                    existing_thumb_url == 'nan' or 
                                    existing_thumb_url == '' or
                                    csv_filename in existing_thumb_url  # Update if URL contains the current filename
                                )
                                
                                if should_update:
                                    self.csv_data.at[row_idx, 'image_thumb'] = thumb_url
                                    self.logger.info(f"Updated image_thumb at row {row_idx}: {thumb_url}")
                                else:
                                    self.logger.info(f"Preserved existing image_thumb at row {row_idx}: {existing_thumb_url}")
                            else:
                                self.logger.warning("image_thumb column not found in CSV!")
                            
                            # Update object_transcript column for transcript records
                            if 'object_transcript' in self.csv_data.columns and 'display_template' in self.csv_data.columns:
                                display_template = str(self.csv_data.at[row_idx, 'display_template']).strip().lower()
                                existing_transcript = str(self.csv_data.at[row_idx, 'object_transcript']).strip()
                                
                                # Only update if display_template is 'transcript' and object_transcript is empty
                                if display_template == 'transcript' and (not existing_transcript or existing_transcript == 'nan' or existing_transcript == ''):
                                    # Generate transcript CSV filename from objectid
                                    # Format: objectid.csv (e.g., dg_1750784116.csv)
                                    transcript_csv_filename = f"{csv_filename}.csv"
                                    self.csv_data.at[row_idx, 'object_transcript'] = transcript_csv_filename
                                    self.logger.info(f"Updated object_transcript at row {row_idx}: {transcript_csv_filename}")
                                elif display_template == 'transcript' and existing_transcript:
                                    self.logger.info(f"Preserved existing object_transcript at row {row_idx}: {existing_transcript}")
                            
                            self.logger.info(f"Updated CollectionBuilder URLs for: '{csv_filename}'")
                        
                        updates += 1
                    else:
                        self.logger.warning(f"No match found for csv_filename: '{csv_filename}'")
            else:
                self.logger.warning(f"Missing data - temp_file_info: {temp_file_info is not None}, csv_filenames_for_matched: {csv_filenames_for_matched is not None}")
            
            # Step 3.7: Handle parent/child relationships (CollectionBuilder mode only)
            # Copy image_small and image_thumb from first child to parent for compound_object and multiple display templates
            if current_mode == "CollectionBuilder":
                parent_child_updates = 0
                
                # Check if required columns exist
                if 'objectid' in self.csv_data.columns and 'parentid' in self.csv_data.columns:
                    self.logger.info("Processing parent/child relationships for compound_object and multiple display templates...")
                    
                    # Find all parent records (rows where parentid is empty/NaN)
                    parents_mask = self.csv_data['parentid'].isna() | (self.csv_data['parentid'] == '')
                    parent_indices = self.csv_data[parents_mask].index
                    
                    for parent_idx in parent_indices:
                        parent_objectid = self.csv_data.at[parent_idx, 'objectid']
                        
                        if pd.isna(parent_objectid) or str(parent_objectid).strip() == '':
                            continue
                        
                        # Check if this parent has compound_object or multiple display_template
                        display_template = ""
                        if 'display_template' in self.csv_data.columns:
                            display_template = str(self.csv_data.at[parent_idx, 'display_template']).strip().lower()
                        
                        # Only process if display_template is compound_object or multiple
                        if display_template not in ['compound_object', 'multiple']:
                            continue
                        
                        self.logger.info(f"Processing parent with display_template='{display_template}', objectid={parent_objectid}")
                            
                        # Find children (rows where parentid matches this parent's objectid)
                        children_mask = self.csv_data['parentid'] == parent_objectid
                        children_indices = self.csv_data[children_mask].index
                        
                        if len(children_indices) > 0:
                            # Get the first child
                            first_child_idx = children_indices[0]
                            
                            # Copy image_small and image_thumb from first child to parent
                            # ONLY if parent's fields are empty
                            updates_made = False
                            
                            if 'image_small' in self.csv_data.columns:
                                parent_small = self.csv_data.at[parent_idx, 'image_small']
                                parent_small_empty = pd.isna(parent_small) or str(parent_small).strip() == ''
                                
                                if parent_small_empty:
                                    child_small = self.csv_data.at[first_child_idx, 'image_small']
                                    if not pd.isna(child_small) and str(child_small).strip() != '':
                                        self.csv_data.at[parent_idx, 'image_small'] = child_small
                                        updates_made = True
                                        self.logger.info(f"Copied image_small from child to parent (objectid={parent_objectid})")
                                else:
                                    self.logger.info(f"Skipped image_small copy - parent already has value (objectid={parent_objectid})")
                            
                            if 'image_thumb' in self.csv_data.columns:
                                parent_thumb = self.csv_data.at[parent_idx, 'image_thumb']
                                parent_thumb_empty = pd.isna(parent_thumb) or str(parent_thumb).strip() == ''
                                
                                if parent_thumb_empty:
                                    child_thumb = self.csv_data.at[first_child_idx, 'image_thumb']
                                    if not pd.isna(child_thumb) and str(child_thumb).strip() != '':
                                        self.csv_data.at[parent_idx, 'image_thumb'] = child_thumb
                                        updates_made = True
                                        self.logger.info(f"Copied image_thumb from child to parent (objectid={parent_objectid})")
                                else:
                                    self.logger.info(f"Skipped image_thumb copy - parent already has value (objectid={parent_objectid})")

                            
                            if updates_made:
                                parent_child_updates += 1
                    
                    if parent_child_updates > 0:
                        self.logger.info(f"Updated {parent_child_updates} parent record(s) with child derivative URLs")
                    else:
                        self.logger.info("No parent/child updates needed")
                else:
                    if 'objectid' not in self.csv_data.columns:
                        self.logger.warning("objectid column not found in CSV - skipping parent/child processing")
                    if 'parentid' not in self.csv_data.columns:
                        self.logger.warning("parentid column not found in CSV - skipping parent/child processing")
            
            # Save the updated CSV
            self.save_csv_data()
            self.edits_applied = True
            
            # Update the data table display
            if self.data_table:
                new_table = self.render_data_table()
                self.data_table.content = new_table.content
                self.data_table.update()
            
            # Success message
            message_parts = []
            if updates > 0:
                message_parts.append(f"Updated {updates} filename(s)")
            
            self.logger.info("Apply All Updates completed successfully")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(" | ".join(message_parts)),
                bgcolor=ft.Colors.GREEN_600
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.logger.error(f"Error applying all updates: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def render_data_table(self):
        """
        Render the CSV data as before/after comparison tables.
        Before edits are applied, shows only the "Before" table full-width.
        After edits, shows side-by-side "Before" and "After" tables.
        
        Returns:
            ft.Container: Container with the data table(s)
        """
        colors = self.get_theme_colors()
        
        if self.csv_data is None or self.csv_data_original is None:
            return ft.Container(
                content=ft.Text("No CSV data loaded", color=colors['secondary_text']),
                padding=20
            )
        
        # Limit to first 5 rows for display
        display_data_before = self.csv_data_original.head(5)
        display_data_after = self.csv_data.head(5)
        
        # Create "Before" table
        before_columns = [
            ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD, size=12))
            for col in display_data_before.columns
        ]
        
        before_rows = []
        for idx, row in display_data_before.iterrows():
            cells = [
                ft.DataCell(ft.Text(str(val), size=11))
                for val in row
            ]
            before_rows.append(ft.DataRow(cells=cells))
        
        before_table = ft.DataTable(
            columns=before_columns,
            rows=before_rows,
            border=ft.border.all(1, colors['border']),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, colors['border']),
            heading_row_color=ft.Colors.GREY_200,
            column_spacing=10,
            data_row_min_height=30,
            data_row_max_height=35,
            heading_row_height=40,
        )
        
        # If no edits have been applied yet, show only the Before table full-width
        if not self.edits_applied:
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"Showing first 5 of {len(self.csv_data)} rows",
                           size=12, italic=True, color=colors['secondary_text']),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("CSV Data:", size=14, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([before_table], scroll=ft.ScrollMode.AUTO)
                                ], scroll=ft.ScrollMode.AUTO),
                                border=ft.border.all(1, colors['border']),
                                border_radius=10,
                                padding=10,
                            )
                        ], spacing=5),
                    ),
                    # Show no changes yet
                    ft.Container(
                        content=ft.Text(
                            "No changes applied yet. Click 'Apply Matched Files' to update the CSV.",
                            size=13,
                            italic=True,
                            color=colors['secondary_text']
                        ),
                        padding=ft.padding.only(top=10),
                    ),
                ], spacing=10),
                expand=True
            )
        
        # After edits have been applied, show Before/After comparison
        # Count total changes across all rows (not just displayed ones)
        total_changes = 0
        for idx in range(len(self.csv_data)):
            for col in self.csv_data.columns:
                original_val = str(self.csv_data_original.iloc[idx][col])
                current_val = str(self.csv_data.iloc[idx][col])
                if original_val != current_val:
                    total_changes += 1
        
        # Create "After" table with changed cells highlighted
        after_columns = [
            ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD, size=12))
            for col in display_data_after.columns
        ]
        
        after_rows = []
        for idx, row in display_data_after.iterrows():
            cells = []
            for col_idx, (col, val) in enumerate(row.items()):
                # Check if value changed from original
                original_val = display_data_before.iloc[idx, col_idx]
                if str(val) != str(original_val):
                    # Highlight changed cells with bold green text
                    cells.append(
                        ft.DataCell(
                            ft.Text(str(val), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
                        )
                    )
                else:
                    cells.append(ft.DataCell(ft.Text(str(val), size=11)))
            after_rows.append(ft.DataRow(cells=cells))
        
        after_table = ft.DataTable(
            columns=after_columns,
            rows=after_rows,
            border=ft.border.all(1, colors['border']),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, colors['border']),
            heading_row_color=ft.Colors.GREY_200,
            column_spacing=10,
            data_row_min_height=30,
            data_row_max_height=35,
            heading_row_height=40,
        )
        
        # Create side-by-side layout with scrolling
        return ft.Container(
            content=ft.Column([
                ft.Text(f"Showing first 5 of {len(self.csv_data)} rows",
                       size=12, italic=True, color=colors['secondary_text']),
                ft.Row([
                    # Before table
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Before:", size=14, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([before_table], scroll=ft.ScrollMode.AUTO)
                                ], scroll=ft.ScrollMode.AUTO),
                                border=ft.border.all(1, colors['border']),
                                border_radius=10,
                                padding=10,
                            )
                        ], spacing=5),
                        expand=1
                    ),
                    # After table
                    ft.Container(
                        content=ft.Column([
                            ft.Text("After:", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([after_table], scroll=ft.ScrollMode.AUTO)
                                ], scroll=ft.ScrollMode.AUTO),
                                border=ft.border.all(2, ft.Colors.GREEN_700),
                                border_radius=10,
                                padding=10,
                            )
                        ], spacing=5),
                        expand=1
                    ),
                ], spacing=10, expand=True),
                # Show change count
                ft.Container(
                    content=ft.Text(
                        f"Total changes: {total_changes} cell{'s' if total_changes != 1 else ''} modified across {len(self.csv_data)} rows",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_700 if total_changes > 0 else colors['secondary_text']
                    ),
                    padding=ft.padding.only(top=10),
                ),
            ], spacing=10),
            expand=True
        )
    
    def render(self) -> ft.Column:
        """
        Render the Update CSV view content.
        
        Returns:
            ft.Column: The Update CSV page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Check if CSV mode is selected
        file_option = self.page.session.get("selected_file_option")
        
        if file_option != "CSV":
            return ft.Column([
                *self.create_page_header("Update CSV"),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.WARNING_AMBER, size=64, color=ft.Colors.ORANGE_600),
                        ft.Container(height=20),
                        ft.Text(
                            "CSV Update is only available when CSV file selection is active.",
                            size=16,
                            color=colors['primary_text'],
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            "Please go to Settings and select 'CSV' as your file selector option.",
                            size=14,
                            color=colors['secondary_text'],
                            text_align=ft.TextAlign.CENTER
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    alignment=ft.alignment.center
                )
            ], alignment="start", expand=True, spacing=0)
        
        # Get CSV file path from session (set by FileSelector)
        original_csv_path = self.page.session.get("selected_csv_file")
        
        # Check if no CSV file is selected (FilePicker was used)
        if not original_csv_path:
            return ft.Column([
                *self.create_page_header("Update CSV"),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_600),
                        ft.Container(height=20),
                        ft.Text(
                            "No CSV file selected.",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text'],
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            "Please select a CSV file in the File Selector view before using Update CSV.",
                            size=14,
                            color=colors['secondary_text'],
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            "Note: FilePicker mode does not provide a CSV file to update.",
                            size=12,
                            italic=True,
                            color=colors['secondary_text'],
                            text_align=ft.TextAlign.CENTER
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    alignment=ft.alignment.center
                )
            ], alignment="start", expand=True, spacing=0)
        
        # Automatically load CSV if not already loaded
        if self.csv_data is None and original_csv_path:
            # Check if FileSelector already created a temp copy
            temp_csv_from_selector = self.page.session.get("temp_csv_file")
            
            if temp_csv_from_selector and os.path.exists(temp_csv_from_selector):
                # Use the existing temp copy from FileSelector
                self.temp_csv_path = temp_csv_from_selector
                self.logger.info(f"Using existing temp CSV from FileSelector: {self.temp_csv_path}")
            else:
                # Create our own temp copy (fallback for backward compatibility)
                self.temp_csv_path = self.copy_csv_to_temp(original_csv_path)
                if not self.temp_csv_path:
                    self.logger.error("Failed to copy CSV to temp directory")
            
            # Load the CSV data
            if self.temp_csv_path:
                if not self.load_csv_data(self.temp_csv_path):
                    self.logger.error("Failed to load CSV file")
        
        # CollectionBuilder mode: use the column selected by the user in File Selector
        self.selected_column = self.page.session.get("selected_csv_column") or "filename"
        button_text = f"Apply Matched Files to CollectionBuilder URLs"
        
        # Build the UI - Status information controls
        status_info_controls = []
        
        if original_csv_path:
            status_info_controls.extend([
                ft.Text(f"Source CSV: {os.path.basename(original_csv_path)}", 
                       size=14, weight=ft.FontWeight.BOLD, color=colors['container_text']),
                ft.Text(f"Path: {original_csv_path}", 
                       size=11, color=colors['container_text'], selectable=True),
            ])
        
        if self.temp_csv_path:
            if status_info_controls:
                status_info_controls.append(ft.Container(height=10))
            status_info_controls.extend([
                ft.Text(f"Working Copy: {os.path.basename(self.temp_csv_path)}", 
                       size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                ft.Text(f"Path: {self.temp_csv_path}", 
                       size=11, color=colors['container_text'], selectable=True),
            ])
        
        content = [
            *self.create_page_header("Update CSV"),
        ]
        
        # Add status info container if we have any
        if status_info_controls:
            content.append(
                ft.Container(
                    content=ft.Column(status_info_controls, spacing=2),
                    padding=ft.padding.all(10),
                    border=ft.border.all(1, colors['border']),
                    border_radius=10,
                    bgcolor=colors['container_bg'],
                    margin=ft.margin.symmetric(vertical=5)
                )
            )
        
        # Action buttons
        button_row_controls = []
        
        if self.csv_data is not None:
            button_row_controls.extend([
                ft.ElevatedButton(
                    "Apply All Updates",
                    icon=ft.Icons.PUBLISHED_WITH_CHANGES,
                    on_click=self.apply_all_updates,
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE
                ),
                ft.ElevatedButton(
                    "Save CSV",
                    icon=ft.Icons.SAVE,
                    on_click=lambda e: self.save_csv_data() and self.logger.info("CSV saved")
                ),
            ])
        
        if button_row_controls:
            content.extend([
                ft.Row(button_row_controls, spacing=10, wrap=True, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=5),
            ])
        
        # Data table section
        if self.csv_data is not None:
            # Store the data table container so we can update it later
            self.data_table = self.render_data_table()
            content.extend([
                ft.Text("CSV Data:", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Container(height=5),
                self.data_table
            ])
        else:
            content.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED_400),
                        ft.Container(height=10),
                        ft.Text(
                            "Failed to load CSV file.",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Container(height=5),
                        ft.Text(
                            "Please check the log for details.",
                            size=12,
                            color=colors['secondary_text']
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        
        return ft.Column(content, alignment="start", expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)
