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
                    self.csv_data = pd.read_csv(csv_path, encoding=encoding, dtype=str, keep_default_na=False)
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
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.csv_data is not None and self.temp_csv_path:
                # Save without index and preserve all values as text (no scientific notation)
                self.csv_data.to_csv(self.temp_csv_path, index=False, encoding='utf-8', quoting=1)
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
    
    def apply_all_updates(self, e):
        """
        Combined function that:
        1. Applies matched filenames to existing rows
        2. Appends a new row for the CSV file itself
        3. Populates dginfo field for all rows with temp CSV filename
        """
        try:
            # Get session data
            temp_file_info = self.page.session.get("temp_file_info") or []
            csv_filenames_for_matched = self.page.session.get("csv_filenames_for_matched") or []
            temp_csv_filename = self.page.session.get("temp_csv_filename") or ""
            original_csv_path = self.page.session.get("selected_csv_file") or ""
            current_mode = self.page.session.get("selected_mode") or "Alma"
            
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
                        
                        if current_mode == "CollectionBuilder":
                            # In CollectionBuilder mode, populate Azure blob URLs
                            azure_base_url = "https://collectionbuilder.blob.core.windows.net"
                            selected_collection = self.page.session.get("selected_collection") or ""
                            
                            self.logger.info(f"CollectionBuilder mode - selected_collection: '{selected_collection}'")
                            
                            # Build derivative filenames for smalls and thumbs
                            # Remove extension from sanitized_filename and add _SMALL.jpg and _TN.jpg
                            base_name = os.path.splitext(sanitized_filename)[0]
                            small_filename = f"{base_name}_SMALL.jpg"
                            thumb_filename = f"{base_name}_TN.jpg"
                            
                            # Build blob URLs with collection prefix
                            if selected_collection:
                                obj_url = f"{azure_base_url}/objs/{selected_collection}/{sanitized_filename}"
                                small_url = f"{azure_base_url}/smalls/{selected_collection}/{small_filename}"
                                thumb_url = f"{azure_base_url}/thumbs/{selected_collection}/{thumb_filename}"
                            else:
                                obj_url = f"{azure_base_url}/objs/{sanitized_filename}"
                                small_url = f"{azure_base_url}/smalls/{small_filename}"
                                thumb_url = f"{azure_base_url}/thumbs/{thumb_filename}"
                            
                            self.logger.info(f"Generated URLs - obj: {obj_url}, small: {small_url}, thumb: {thumb_url}")
                            
                            # Update the three URL columns
                            if 'object_location' in self.csv_data.columns:
                                self.csv_data.at[row_idx, 'object_location'] = obj_url
                                self.logger.info(f"Set object_location at row {row_idx}")
                            else:
                                self.logger.warning("object_location column not found in CSV!")
                                
                            if 'image_small' in self.csv_data.columns:
                                self.csv_data.at[row_idx, 'image_small'] = small_url
                                self.logger.info(f"Set image_small at row {row_idx}")
                            else:
                                self.logger.warning("image_small column not found in CSV!")
                                
                            if 'image_thumb' in self.csv_data.columns:
                                self.csv_data.at[row_idx, 'image_thumb'] = thumb_url
                                self.logger.info(f"Set image_thumb at row {row_idx}")
                            else:
                                self.logger.warning("image_thumb column not found in CSV!")
                            
                            self.logger.info(f"Updated CollectionBuilder URLs for: '{csv_filename}'")
                        else:
                            # In Alma mode, just replace with sanitized filename
                            self.csv_data.at[row_idx, column_name] = sanitized_filename
                            self.logger.info(f"Updated CSV: '{csv_filename}' -> '{sanitized_filename}'")
                        
                        updates += 1
                    else:
                        self.logger.warning(f"No match found for csv_filename: '{csv_filename}'")
            else:
                self.logger.warning(f"Missing data - temp_file_info: {temp_file_info is not None}, csv_filenames_for_matched: {csv_filenames_for_matched is not None}")
            
            # Step 2: Append a new row for the CSV file itself (Alma mode only)
            if current_mode == "Alma":
                # Generate unique ID
                unique_id = utils.generate_unique_id(self.page)
                
                # Create new row with all empty values first
                new_row = {col: '' for col in self.csv_data.columns}
                
                # Extract numeric portion for Handle URL (e.g., "dg_1234567890" -> "1234567890")
                numeric_part = unique_id.split('_')[-1] if '_' in unique_id else unique_id
                handle_url = f"http://hdl.handle.net/11084/{numeric_part}"
                
                # Populate specific columns
                new_row['originating_system_id'] = unique_id
                new_row['dc:identifier'] = handle_url  # Use Handle URL format in Alma mode
                new_row['collection_id'] = '81342586470004641'  # CSV file record gets different collection
                new_row['dc:type'] = 'Dataset'  # CSV file is a dataset
                
                # Use the sanitized temp CSV filename for both dc:title and file_name_1
                new_row['dc:title'] = temp_csv_filename
                new_row['file_name_1'] = temp_csv_filename
                
                # Append the new row to the DataFrame
                import pandas as pd
                new_row_df = pd.DataFrame([new_row])
                self.csv_data = pd.concat([self.csv_data, new_row_df], ignore_index=True)
                
                # Also update the original to match (so comparison logic doesn't break)
                self.csv_data_original = pd.concat([self.csv_data_original, new_row_df], ignore_index=True)
                
                self.logger.info(f"Appended new row with ID: {unique_id}")
            
            # Step 3: Fill empty originating_system_id cells with unique IDs (Alma mode only)
            if current_mode == "Alma":
                filled_ids = 0
                if 'originating_system_id' in self.csv_data.columns:
                    for idx in range(len(self.csv_data)):
                        cell_value = self.csv_data.at[idx, 'originating_system_id']
                        # Check if empty (empty string, None, or NaN)
                        if pd.isna(cell_value) or str(cell_value).strip() == '':
                            new_id = utils.generate_unique_id(self.page)
                            self.csv_data.at[idx, 'originating_system_id'] = new_id
                            # Also update dc:identifier if it exists and is empty
                            if 'dc:identifier' in self.csv_data.columns:
                                dc_id_value = self.csv_data.at[idx, 'dc:identifier']
                                if pd.isna(dc_id_value) or str(dc_id_value).strip() == '':
                                    # In Alma mode, use Handle URL format
                                    numeric_part = new_id.split('_')[-1] if '_' in new_id else new_id
                                    self.csv_data.at[idx, 'dc:identifier'] = f"http://hdl.handle.net/11084/{numeric_part}"
                            filled_ids += 1
                            self.logger.info(f"Generated ID {new_id} for row {idx}")
                    if filled_ids > 0:
                        self.logger.info(f"Filled {filled_ids} empty originating_system_id cell(s)")
                else:
                    self.logger.warning("originating_system_id column not found in CSV")
            
            # Step 3.5: In Alma mode, convert dc:identifier to Handle URL format
            if current_mode == "Alma" and 'dc:identifier' in self.csv_data.columns and 'originating_system_id' in self.csv_data.columns:
                handle_count = 0
                for idx in range(len(self.csv_data)):
                    orig_id = self.csv_data.at[idx, 'originating_system_id']
                    # Extract numeric portion from originating_system_id (e.g., "dg_1234567890" -> "1234567890")
                    if not pd.isna(orig_id) and str(orig_id).strip() != '':
                        orig_id_str = str(orig_id).strip()
                        # Extract numeric part (everything after last underscore or the whole thing if no underscore)
                        if '_' in orig_id_str:
                            numeric_part = orig_id_str.split('_')[-1]
                        else:
                            numeric_part = orig_id_str
                        
                        # Only proceed if we have a numeric part
                        if numeric_part.isdigit():
                            handle_url = f"http://hdl.handle.net/11084/{numeric_part}"
                            self.csv_data.at[idx, 'dc:identifier'] = handle_url
                            handle_count += 1
                
                if handle_count > 0:
                    self.logger.info(f"Set {handle_count} dc:identifier cell(s) to Handle URL format")
            
            # Step 3.6: Fill collection_id cells with Pending Review collection (Alma mode only)
            filled_collections = 0
            if current_mode == "Alma" and 'collection_id' in self.csv_data.columns:
                pending_review_id = '81313013130004641'  # Pending Review collection
                for idx in range(len(self.csv_data)):
                    cell_value = self.csv_data.at[idx, 'collection_id']
                    # Check if empty (empty string, None, or NaN)
                    # if pd.isna(cell_value) or str(cell_value).strip() == '':   # This logic was not right, the collection_id should ALWAYS be 'pending review'!
                    if True:
                        self.csv_data.at[idx, 'collection_id'] = pending_review_id
                        filled_collections += 1
                if filled_collections > 0:
                    self.logger.info(f"Filled {filled_collections} empty collection_id cell(s) with Pending Review collection")
            
            # Step 3.65: Process Alma compound parent/child relationships
            if current_mode == "Alma" and 'compoundrelationship' in self.csv_data.columns:
                compound_updates = 0
                self.logger.info("Processing Alma compound parent/child relationships...")
                
                idx = 0
                while idx < len(self.csv_data):
                    compound = str(self.csv_data.at[idx, 'compoundrelationship']).strip()
                    
                    # Check if this is a parent
                    if compound.startswith('parent'):
                        parent_idx = idx
                        parent_pid = self.csv_data.at[parent_idx, 'originating_system_id']
                        self.logger.info(f"Found parent at row {idx} with originating_system_id: {parent_pid}")
                        
                        # Set parent's group_id to its own originating_system_id
                        if 'group_id' in self.csv_data.columns:
                            self.csv_data.at[parent_idx, 'group_id'] = parent_pid
                            self.logger.info(f"  Set parent group_id to: {parent_pid}")
                        
                        # Initialize parent's TOC and dginfo
                        toc = ""
                        dginfo_list = []
                        
                        # Count and process children
                        child_count = 0
                        child_idx = idx + 1
                        
                        # Loop through following rows to find children
                        while child_idx < len(self.csv_data):
                            child_compound = str(self.csv_data.at[child_idx, 'compoundrelationship']).strip()
                            
                            if not child_compound.startswith('child'):
                                break  # End of children
                            
                            child_count += 1
                            
                            # Get child information
                            child_title = str(self.csv_data.at[child_idx, 'dc:title']) if 'dc:title' in self.csv_data.columns else ''
                            child_type = str(self.csv_data.at[child_idx, 'dc:type']) if 'dc:type' in self.csv_data.columns else ''
                            
                            # Build TOC entry
                            if child_title and child_type:
                                toc += f"{child_title} ({child_type}) | "
                            elif child_title:
                                toc += f"{child_title} | "
                            
                            # Set child's group_id to parent's originating_system_id
                            if 'group_id' in self.csv_data.columns:
                                self.csv_data.at[child_idx, 'group_id'] = parent_pid
                            
                            # Set child rep_label and rep_public_note
                            if 'rep_label' in self.csv_data.columns:
                                self.csv_data.at[child_idx, 'rep_label'] = child_title
                            if 'rep_public_note' in self.csv_data.columns:
                                self.csv_data.at[child_idx, 'rep_public_note'] = child_type
                            
                            self.logger.info(f"  Processed child at row {child_idx}: {child_title}")
                            child_idx += 1
                        
                        # Validate we have at least 2 children
                        if child_count < 2:
                            error_msg = f"*ERROR* Parent at row {parent_idx} has only {child_count} child(ren), need at least 2!"
                            self.logger.error(error_msg)
                            if 'mms_id' in self.csv_data.columns:
                                self.csv_data.at[parent_idx, 'mms_id'] = "*ERROR* Too few children!"
                        else:
                            # Update parent record
                            if 'dcterms:tableOfContents' in self.csv_data.columns:
                                self.csv_data.at[parent_idx, 'dcterms:tableOfContents'] = toc.rstrip(' | ')
                                self.logger.info(f"  Set parent TOC: {toc.rstrip(' | ')}")
                            
                            # Set parent dc:type to 'compound'
                            if 'dc:type' in self.csv_data.columns:
                                self.csv_data.at[parent_idx, 'dc:type'] = 'compound'
                                self.logger.info(f"  Set parent dc:type to 'compound'")
                            
                            # Clear parent dcterms:type.dcterms:DCMIType
                            if 'dcterms:type.dcterms:DCMIType' in self.csv_data.columns:
                                self.csv_data.at[parent_idx, 'dcterms:type.dcterms:DCMIType'] = ''
                            
                            compound_updates += 1
                        
                        # Skip past the children we just processed
                        idx = child_idx - 1
                    
                    idx += 1
                
                if compound_updates > 0:
                    self.logger.info(f"Processed {compound_updates} compound parent/child group(s)")
                else:
                    self.logger.info("No compound parent/child relationships found")
            
            # Step 3.7: Handle parent/child relationships (CollectionBuilder mode only)
            # Copy image_small and image_thumb from first child to parent
            if current_mode == "CollectionBuilder":
                parent_child_updates = 0
                
                # Check if required columns exist
                if 'objectid' in self.csv_data.columns and 'parentid' in self.csv_data.columns:
                    self.logger.info("Processing parent/child relationships...")
                    
                    # Find all parent records (rows where parentid is empty/NaN)
                    parents_mask = self.csv_data['parentid'].isna() | (self.csv_data['parentid'] == '')
                    parent_indices = self.csv_data[parents_mask].index
                    
                    for parent_idx in parent_indices:
                        parent_objectid = self.csv_data.at[parent_idx, 'objectid']
                        
                        if pd.isna(parent_objectid) or str(parent_objectid).strip() == '':
                            continue
                            
                        # Find children (rows where parentid matches this parent's objectid)
                        children_mask = self.csv_data['parentid'] == parent_objectid
                        children_indices = self.csv_data[children_mask].index
                        
                        if len(children_indices) > 0:
                            # Get the first child
                            first_child_idx = children_indices[0]
                            
                            # Copy image_small and image_thumb from first child to parent
                            updates_made = False
                            
                            if 'image_small' in self.csv_data.columns:
                                child_small = self.csv_data.at[first_child_idx, 'image_small']
                                if not pd.isna(child_small) and str(child_small).strip() != '':
                                    self.csv_data.at[parent_idx, 'image_small'] = child_small
                                    updates_made = True
                                    self.logger.info(f"Copied image_small from child to parent (objectid={parent_objectid})")
                            
                            if 'image_thumb' in self.csv_data.columns:
                                child_thumb = self.csv_data.at[first_child_idx, 'image_thumb']
                                if not pd.isna(child_thumb) and str(child_thumb).strip() != '':
                                    self.csv_data.at[parent_idx, 'image_thumb'] = child_thumb
                                    updates_made = True
                                    self.logger.info(f"Copied image_thumb from child to parent (objectid={parent_objectid})")
                            
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
            
            # Step 4: Populate dginfo field for ALL rows with temp CSV filename (Alma mode only)
            if current_mode == "Alma":
                if 'dginfo' in self.csv_data.columns:
                    self.csv_data['dginfo'] = temp_csv_filename
                    # Also update original so dginfo doesn't show as changed
                    self.csv_data_original['dginfo'] = temp_csv_filename
                    self.logger.info(f"Set dginfo field to '{temp_csv_filename}' for all {len(self.csv_data)} rows")
                else:
                    self.logger.warning("dginfo column not found in CSV")
            
            # Save the updated CSV
            self.save_csv_data()
            self.edits_applied = True
            
            # Step 5: In Alma mode, create a copy named values.csv in temp directory
            if current_mode == "Alma":
                temp_dir = self.page.session.get("temp_directory")
                if temp_dir and self.temp_csv_path:
                    try:
                        values_csv_path = os.path.join(temp_dir, "values.csv")
                        shutil.copy2(self.temp_csv_path, values_csv_path)
                        self.logger.info(f"Created values.csv copy in temp directory: {values_csv_path}")
                    except Exception as e:
                        self.logger.error(f"Error creating values.csv copy: {e}")
            
            # Update the data table display
            if self.data_table:
                new_table = self.render_data_table()
                self.data_table.content = new_table.content
                self.data_table.update()
            
            # Success message
            message_parts = []
            if updates > 0:
                message_parts.append(f"Updated {updates} filename(s)")
            
            # Only mention CSV row addition in Alma mode
            if current_mode == "Alma":
                message_parts.append("Added CSV row with unique ID")
            
            if current_mode == "Alma" and filled_ids > 0:
                message_parts.append(f"Generated {filled_ids} ID(s)")
            if current_mode == "Alma" and filled_collections > 0:
                message_parts.append(f"Set {filled_collections} collection(s) to Pending Review")
            
            # Only mention dginfo in Alma mode
            if current_mode == "Alma":
                message_parts.append(f"Set dginfo for all rows")
            
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
    
    def append_new_row(self, e):
        """
        Append a new row to the CSV with temporary file information.
        Creates a unique ID and populates specific columns with temp file data.
        Uses the temp CSV filename that was created by FileSelector.
        """
        try:
            # Get CSV file info from session
            temp_csv_filename = self.page.session.get("temp_csv_filename") or ""
            original_csv_path = self.page.session.get("selected_csv_file") or ""
            
            if not temp_csv_filename or self.csv_data is None:
                self.logger.warning("No temp CSV filename or CSV data not loaded")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No temporary CSV file data available"),
                    bgcolor=ft.Colors.ORANGE_600
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Generate unique ID
            unique_id = utils.generate_unique_id(self.page)
            
            # Create new row with all empty values first
            new_row = {col: '' for col in self.csv_data.columns}
            
            # Extract numeric portion for Handle URL (e.g., "dg_1234567890" -> "1234567890")
            numeric_part = unique_id.split('_')[-1] if '_' in unique_id else unique_id
            handle_url = f"http://hdl.handle.net/11084/{numeric_part}"
            
            # Populate specific columns
            new_row['originating_system_id'] = unique_id
            new_row['dc:identifier'] = handle_url  # Use Handle URL format in Alma mode
            new_row['collection_id'] = '81342586470004641'  # CSV file record gets different collection
            new_row['dc:type'] = 'Dataset'  # CSV file is a dataset
            
            # Use the sanitized temp CSV filename for both dc:title and file_name_1
            new_row['dc:title'] = temp_csv_filename
            new_row['file_name_1'] = temp_csv_filename
            
            # Append the new row to the DataFrame
            import pandas as pd
            new_row_df = pd.DataFrame([new_row])
            self.csv_data = pd.concat([self.csv_data, new_row_df], ignore_index=True)
            
            # Also update the original to match (so comparison logic doesn't break)
            # The new row should be considered as part of the "before" state now
            self.csv_data_original = pd.concat([self.csv_data_original, new_row_df], ignore_index=True)
            
            # Save the updated CSV
            self.save_csv_data()
            self.edits_applied = True
            
            # Update the data table display
            if self.data_table:
                new_table = self.render_data_table()
                self.data_table.content = new_table.content
                self.data_table.update()
            
            self.logger.info(f"Appended new row with ID: {unique_id}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Added new row with ID: {unique_id}"),
                bgcolor=ft.Colors.GREEN_600
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.logger.error(f"Error appending new row: {e}")
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
        
        # Get current mode to determine column name for updates
        current_mode = utils.session_get(self.page, "selected_mode", "Alma")
        
        # Set the column to update based on mode (no selector needed)
        if current_mode == "Alma":
            self.selected_column = "file_name_1"
            button_text = "Apply Matched Files to file_name_1"
        else:  # CollectionBuilder
            # In CollectionBuilder, use the column selected by the user in File Selector
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
