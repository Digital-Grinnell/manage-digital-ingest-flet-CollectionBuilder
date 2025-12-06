"""
File Selector View for Manage Digital Ingest Application

This module contains the base FileSelectorView class and two specific implementations:
- FilePickerSelectorView: For file picker functionality
- CSVSelectorView: For CSV file functionality
"""

import flet as ft
from views.base_view import BaseView
import os
import utils
import re
import shutil
import tempfile
import uuid
from datetime import datetime


class FileSelectorView(BaseView):
    """
    Base file selector view class for handling file selection operations.
    This is an abstract base class that should be subclassed for specific implementations.
    """
    
    def __init__(self, page: ft.Page, selector_type: str):
        """
        Initialize the file selector view.
        
        Args:
            page: The Flet page object
            selector_type: The type of selector (e.g., "FilePicker", "CSV")
        """
        super().__init__(page)
        self.selector_type = selector_type
    
    def sanitize_file_path(self, file_path):
        """
        Sanitize a file path by replacing spaces with underscores and 
        handling spaces adjacent to dashes.
        
        Args:
            file_path: The original file path
            
        Returns:
            str: The sanitized file path
        """
        if not file_path:
            return file_path
        
        # Split path into directory and filename
        directory, filename = os.path.split(file_path)
        
        # Apply sanitization rules to filename only
        # Strip leading and trailing whitespace from the entire filename
        filename = filename.strip()
        
        # Split filename and extension to handle them separately
        name_part, ext_part = os.path.splitext(filename)
        
        # Strip the name part as well to handle trailing spaces before extension
        name_part = name_part.strip()
        
        # Sanitize the name part (before extension)
        # Replace space-dash-space pattern with double dash first
        name_part = re.sub(r'\s+-\s+', '--', name_part)
        
        # Replace remaining space-dash and dash-space patterns with double dashes
        name_part = re.sub(r'\s+-', '--', name_part)  # space followed by dash
        name_part = re.sub(r'-\s+', '--', name_part)  # dash followed by space
        
        # Replace remaining spaces with underscores
        name_part = re.sub(r'\s+', '_', name_part)
        
        # Reconstruct filename (extension is kept as-is after stripping)
        sanitized_filename = name_part + ext_part.strip()
        
        # Rejoin the path
        return os.path.join(directory, sanitized_filename) if directory else sanitized_filename
    
    def copy_transcript_files_to_temp_directory(self, transcript_paths, temp_dir):
        """
        Create symbolic links for transcript CSV files in TRANSCRIPTS subdirectory.
        
        Args:
            transcript_paths: List of transcript CSV file paths to link
            temp_dir: The temporary directory base path
            
        Returns:
            list: List of created symbolic link paths in TRANSCRIPTS directory
        """
        import os
        
        try:
            # Create TRANSCRIPTS subdirectory
            transcripts_dir = os.path.join(temp_dir, "TRANSCRIPTS")
            os.makedirs(transcripts_dir, exist_ok=True)
            self.logger.info(f"Using TRANSCRIPTS directory: {transcripts_dir}")
            
            transcript_temp_files = []
            
            for source_path in transcript_paths:
                if not os.path.exists(source_path):
                    self.logger.warning(f"Transcript file not found: {source_path}")
                    continue
                
                # Get the filename
                filename = os.path.basename(source_path)
                
                # Create the destination path in TRANSCRIPTS subdirectory
                dest_path = os.path.join(transcripts_dir, filename)
                
                # Remove existing link/file if present
                if os.path.exists(dest_path) or os.path.islink(dest_path):
                    os.remove(dest_path)
                
                # Create symbolic link
                try:
                    os.symlink(source_path, dest_path)
                    transcript_temp_files.append(dest_path)
                    self.logger.info(f"Created transcript link: {filename}")
                except Exception as link_error:
                    self.logger.error(f"Failed to create transcript link for {filename}: {link_error}")
            
            # Store transcript directory in session
            self.page.session.set("temp_transcripts_directory", transcripts_dir)
            
            self.logger.info(f"Successfully created {len(transcript_temp_files)} transcript symbolic links in TRANSCRIPTS/ directory")
            return transcript_temp_files
            
        except Exception as e:
            self.logger.error(f"Error creating transcript links: {e}")
            return []
    
    def copy_files_to_temp_directory(self, file_paths):
        """
        Create symbolic links with sanitized names in a temporary directory that reference the original files.
        
        Args:
            file_paths: List of file paths to link
            
        Returns:
            tuple: (temp_file_paths: list, temp_file_info: list, temp_directory: str)
        """
        if not file_paths:
            return [], [], None
        
        try:
            # Check if temp directory already exists in session (e.g., from CSV selection)
            temp_dir = self.page.session.get("temp_directory")
            
            if not temp_dir or not os.path.exists(temp_dir):
                # Create base temp directory if it doesn't exist
                temp_base_dir = os.path.join(os.getcwd(), "storage", "temp")
                os.makedirs(temp_base_dir, exist_ok=True)
                
                # Create a unique subdirectory for this session
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
                temp_dir = os.path.join(temp_base_dir, f"file_selector_{session_id}")
                os.makedirs(temp_dir, exist_ok=True)
                
                self.logger.info(f"Created new temporary directory: {temp_dir}")
            else:
                self.logger.info(f"Reusing existing temporary directory: {temp_dir}")
            
            # Create or verify OBJS subdirectory for source files
            objs_dir = os.path.join(temp_dir, "OBJS")
            os.makedirs(objs_dir, exist_ok=True)
            
            # Create or verify TN and SMALL subdirectories for derivatives
            tn_dir = os.path.join(temp_dir, "TN")
            small_dir = os.path.join(temp_dir, "SMALL")
            os.makedirs(tn_dir, exist_ok=True)
            os.makedirs(small_dir, exist_ok=True)
            
            # Only log directory structure if we just created it
            temp_was_already_set = bool(self.page.session.get("temp_directory"))
            if not temp_was_already_set:
                self.logger.info(f"  - OBJS/: {objs_dir}")
                self.logger.info(f"  - TN/: {tn_dir}")
                self.logger.info(f"  - SMALL/: {small_dir}")
            
            temp_file_paths = []
            temp_file_info = []
            
            for original_path in file_paths:
                try:
                    # Skip empty or None paths
                    if not original_path or not os.path.exists(original_path):
                        self.logger.warning(f"Skipping non-existent file: {original_path}")
                        continue
                    
                    # Get the original filename
                    original_filename = os.path.basename(original_path)
                    
                    # Sanitize the filename (already handles spaces and dashes)
                    sanitized_filename = os.path.basename(self.sanitize_file_path(original_filename))
                    
                    # Create the destination path in OBJS subdirectory
                    temp_file_path = os.path.join(objs_dir, sanitized_filename)
                    
                    # Handle filename collisions
                    counter = 1
                    base_name, ext = os.path.splitext(sanitized_filename)
                    while os.path.exists(temp_file_path):
                        sanitized_filename = f"{base_name}_{counter}{ext}"
                        temp_file_path = os.path.join(objs_dir, sanitized_filename)
                        counter += 1
                    
                    # Create symbolic link instead of copying the file
                    os.symlink(os.path.abspath(original_path), temp_file_path)
                    
                    # Store the paths and info
                    temp_file_paths.append(temp_file_path)
                    temp_file_info.append({
                        'original_path': original_path,
                        'original_filename': original_filename,
                        'temp_path': temp_file_path,
                        'sanitized_filename': sanitized_filename
                    })
                    
                    self.logger.info(f"Created symbolic link '{sanitized_filename}' -> '{original_path}' in OBJS/")
                    
                except Exception as e:
                    self.logger.error(f"Failed to create symbolic link for file {original_path}: {str(e)}")
                    continue
            
            # Store in session
            self.page.session.set("temp_directory", temp_dir)
            self.page.session.set("temp_objs_directory", objs_dir)
            self.page.session.set("temp_tn_directory", tn_dir)
            self.page.session.set("temp_small_directory", small_dir)
            self.page.session.set("temp_files", temp_file_paths)
            self.page.session.set("temp_file_info", temp_file_info)
            
            self.logger.info(f"Successfully created {len(temp_file_paths)} symbolic links in OBJS/ directory")
            return temp_file_paths, temp_file_info, temp_dir
            
        except Exception as e:
            self.logger.error(f"Failed to create temporary directory or symbolic links: {str(e)}")
            return [], [], None
    
    def clear_temp_directory(self):
        """Clear the temporary directory and session data."""
        # Check if temp directory is protected
        import json
        try:
            persistent_file = "storage/data/persistent_session.json"
            if os.path.exists(persistent_file):
                with open(persistent_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    if session_data.get("_temp_protected"):
                        self.logger.info("Temporary directory is protected - skipping deletion")
                        return
        except Exception as e:
            self.logger.warning(f"Could not check temp directory protection: {e}")
        
        temp_dir = self.page.session.get("temp_directory")
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                self.logger.info(f"Cleared temporary directory: {temp_dir}")
            except Exception as e:
                self.logger.error(f"Failed to clear temporary directory: {str(e)}")
        
        # Clear session data
        self.page.session.set("temp_directory", None)
        self.page.session.set("temp_files", [])
        self.page.session.set("temp_file_info", [])
    
    def render(self) -> ft.Column:
        """
        Render the file selector view content.
        This base implementation should be overridden by subclasses.
        
        Returns:
            ft.Column: The file selector page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        return ft.Column([
            ft.Text("File Selector Base View", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("This base view should be overridden by subclasses.", color=colors['secondary_text'])
        ], alignment="start", expand=True)


class FilePickerSelectorView(FileSelectorView):
    """
    File picker implementation of the file selector view.
    Handles local file system file selection.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the file picker selector view."""
        super().__init__(page, "FilePicker")
        self.selected_files = []
        self.selected_files_list = None
    
    def load_last_directory(self):
        """Load the last used directory from persistent storage."""
        try:
            import json
            import os
            persistent_file = os.path.join(os.path.expanduser("~"), ".mdi_persistent.json")
            if os.path.exists(persistent_file):
                with open(persistent_file, 'r') as f:
                    data = json.load(f)
                    return data.get("last_directory")
        except Exception as e:
            self.logger.error(f"Error loading last directory: {str(e)}")
        return None
    
    def save_last_directory(self, directory):
        """Save the last used directory to persistent storage."""
        try:
            import json
            import os
            persistent_file = os.path.join(os.path.expanduser("~"), ".mdi_persistent.json")
            data = {}
            if os.path.exists(persistent_file):
                with open(persistent_file, 'r') as f:
                    data = json.load(f)
            
            data["last_directory"] = directory
            
            with open(persistent_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger.error(f"Error saving last directory: {str(e)}")
    
    def is_image_file(self, file_path):
        """Check if a file is an image based on its extension."""
        try:
            image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.webp'}
            return any(file_path.lower().endswith(ext) for ext in image_extensions)
        except Exception as e:
            self.logger.error(f"Error checking image file: {str(e)}")
            return False
    
    def render(self) -> ft.Column:
        """
        Render the file selector view content.
        This base implementation should be overridden by subclasses.
        
        Returns:
            ft.Column: The file selector page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        return ft.Column([
            ft.Row([
                ft.Text(f"File Selector - {self.selector_type}", size=24, weight=ft.FontWeight.BOLD),
                self.create_log_button("Show Logs", ft.Icons.LIST_ALT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=15),
            ft.Text(f"File selector functionality for {self.selector_type} will be implemented here.",
                   size=16, color=colors['primary_text']),
        ], alignment="center")


class FilePickerSelectorView(FileSelectorView):
    """
    File picker implementation of the file selector view.
    Handles local file system file selection.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the file picker selector view."""
        super().__init__(page, "FilePicker")
        self.selected_files = []
        self.selected_files_list = None
    
    def load_last_directory(self):
        """Load the last used directory from persistent storage."""
        try:
            import json
            import os
            persistent_path = os.path.join("_data", "persistent.json")
            if os.path.exists(persistent_path):
                with open(persistent_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    directory = data.get("last_directory")
                    if directory and os.path.exists(directory):
                        return directory
        except Exception as e:
            self.logger.warning(f"Failed to load last directory: {e}")
        return None
    
    def save_last_directory(self, directory):
        """Save the last used directory to persistent storage."""
        try:
            import json
            import os
            persistent_path = os.path.join("_data", "persistent.json")
            os.makedirs("_data", exist_ok=True)
            
            # Load existing data to preserve other settings
            existing_data = {}
            if os.path.exists(persistent_path):
                try:
                    with open(persistent_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception:
                    self.logger.warning("Failed to read existing persistent data")
            
            # Update only the last_directory field
            existing_data["last_directory"] = directory
            
            # Write back to file
            with open(persistent_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
            
            self.logger.info(f"Saved last directory: {directory}")
        except Exception as e:
            self.logger.error(f"Failed to save last directory: {e}")
    
    def render(self) -> ft.Column:
        """
        Render the file picker selector view content.
        
        Returns:
            ft.Column: The file picker page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Load last directory
        last_dir = self.load_last_directory()
        
        # Handler for file picker result
        def on_file_picker_result(e: ft.FilePickerResultEvent):
            """Handle file picker result and automatically process files."""
            if e.files:
                self.selected_files = []
                file_paths = []
                
                for file in e.files:
                    self.selected_files.append(file)
                    # Store the original file path (don't sanitize here)
                    file_paths.append(file.path)
                
                # Save the directory of the first selected file
                if file_paths:
                    import os
                    directory = os.path.dirname(file_paths[0])
                    self.save_last_directory(directory)
                    
                    # Store selected file paths in page session
                    self.page.session.set("selected_file_paths", file_paths)
                    self.logger.info(f"Selected {len(file_paths)} file(s)")
                
                # Update the UI to show selected files
                self.update_file_list()
                
                # Automatically create links
                self.auto_perform_file_picker_workflow(file_paths)
            else:
                self.logger.info("No files selected")
        
        # Create file picker
        file_picker = ft.FilePicker(
            on_result=on_file_picker_result
        )
        
        # Add file picker to page overlay (required for FilePicker to work)
        self.page.overlay.append(file_picker)
        
        # Handler for open file picker button
        def open_file_picker(e):
            """Open the file picker dialog."""
            # Set initial directory if available
            initial_dir = last_dir if last_dir else None
            
            # Open file picker with multiple selection enabled and file type filters
            file_picker.pick_files(
                dialog_title="Select Image or PDF Files",
                allow_multiple=True,
                allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "pdf"],
                initial_directory=initial_dir
            )
        
        # Create a list view for selected files
        self.selected_files_list = ft.ListView(
            spacing=0,
            padding=2,
            height=300,
            expand=True
        )
        
        # Load previously selected files from session if available
        session_files = self.page.session.get("selected_file_paths")
        if session_files:
            self.logger.info(f"Loaded {len(session_files)} file(s) from session")
            for file_path in session_files:
                import os
                # Sanitize file path for display
                sanitized_path = self.sanitize_file_path(file_path)
                self.selected_files_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DESCRIPTION, size=14),
                        title=ft.Text(os.path.basename(sanitized_path), size=14),
                        subtitle=ft.Text(sanitized_path, size=11, color=colors['secondary_text']),
                        dense=True,
                        content_padding=ft.padding.symmetric(horizontal=5, vertical=0)
                        )
                    )
            self.page.update()
        
        return ft.Column([
            ft.Row([
                ft.Text(f"File Selector - {self.selector_type}", size=24, weight=ft.FontWeight.BOLD),
                self.create_log_button("Show Logs", ft.Icons.LIST_ALT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            # ft.Container(height=8),
            ft.Divider(height=15, color=colors['divider']),
            ft.Text("Select image or PDF files from your local file system.",
                   size=16, color=colors['primary_text']),
            ft.Container(height=5),
            ft.Text(f"Last directory: {last_dir if last_dir else 'None'}", 
                   size=12, color=colors['secondary_text'], italic=True),
            ft.Container(height=8),
            ft.Row([
                ft.ElevatedButton(
                    "Open File Picker",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=open_file_picker
                ),
                ft.ElevatedButton(
                    "Clear Selection",
                    icon=ft.Icons.CLEAR,
                    on_click=lambda e: self.clear_selection()
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Container(height=8),
            ft.Text("A temporary directory of sanitized symbolic links will be populated to reference selected files.", 
                   size=12, color=colors['secondary_text'], italic=True),
            ft.Container(height=8),
            ft.Text("Selected Files:", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=5),
            # Show temporary directory status
            self.create_temp_status_display(colors),
            ft.Container(height=5),
            ft.Container(
                content=self.selected_files_list,
                border=ft.border.all(1, colors['border']),
                border_radius=5,
                padding=2
            )
        ], alignment="start", expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    
    def update_file_list(self):
        """Update the displayed list of selected files."""
        if self.selected_files_list:
            colors = self.get_theme_colors()
            self.selected_files_list.controls.clear()
            
            for file in self.selected_files:
                import os
                # Sanitize the file path for display
                sanitized_path = self.sanitize_file_path(file.path)
                self.selected_files_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DESCRIPTION, size=14),
                        title=ft.Text(os.path.basename(sanitized_path), size=14),
                        subtitle=ft.Text(sanitized_path, size=11, color=colors['secondary_text']),
                        dense=True,
                        content_padding=ft.padding.symmetric(horizontal=5, vertical=0)
                    )
                )
            
            self.page.update()
    
    def clear_selection(self):
        """Clear the selected files."""
        self.selected_files = []
        self.page.session.set("selected_file_paths", [])
        if self.selected_files_list:
            self.selected_files_list.controls.clear()
        self.clear_temp_directory()  # Also clear temp directory
        self.page.update()
        self.logger.info("Cleared file selection")
    
    def create_temp_status_display(self, colors):
        """Create a display showing temporary directory status."""
        temp_dir = self.page.session.get("temp_directory")
        temp_files = self.page.session.get("temp_files") or []
        
        if temp_dir and temp_files:
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"📁 Temporary Directory: {len(temp_files)} files ready", 
                           size=12, color=colors['secondary_text']),
                    ft.Text(f"   {temp_dir}", 
                           size=11, color=colors['secondary_text'], italic=True)
                ], spacing=2),
                padding=ft.padding.all(8),
                border=ft.border.all(1, ft.Colors.GREEN_200),
                border_radius=5,
                bgcolor=ft.Colors.GREEN_50
            )
        else:
            return ft.Container(
                content=ft.Text("📁 No temporary files - select files to automatically create links", 
                               size=12, color=colors['secondary_text']),
                padding=ft.padding.all(8),
                border=ft.border.all(1, ft.Colors.ORANGE_200),
                border_radius=5,
                bgcolor=ft.Colors.ORANGE_50
            )
    
    def on_copy_files_to_temp(self, e):
        """Handle creating symbolic links to files in temporary directory."""
        file_paths = self.page.session.get("selected_file_paths") or []
        if not file_paths:
            self.show_snack("No files selected to link", is_error=True)
            return
        
        self.logger.info(f"Creating symbolic links for {len(file_paths)} files in temporary directory...")
        temp_files, temp_file_info, temp_dir = self.copy_files_to_temp_directory(file_paths)
        
        # Update selected_file_paths to point to temp files so derivatives are created there
        if temp_files:
            self.page.session.set("selected_file_paths", temp_files)
        
        if temp_files:
            self.show_snack(f"Successfully created {len(temp_files)} symbolic links in temporary directory")
            
            # Refresh the view to show updated button states
            self.page.go("/file_selector")
        else:
            self.show_snack("Failed to create symbolic links in temporary directory", is_error=True)


class CSVSelectorView(FileSelectorView):
    """
    CSV implementation of the file selector view.
    Handles file selection from CSV files with a 4-step workflow.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the CSV selector view."""
        super().__init__(page, "CSV")
        self.csv_file_display = None
        self.file_selection_container = None
        self.columns_display_container = None
        self.results_display_container = None
        self.search_container = None
    
    def load_last_directory(self):
        """Load the last used directory from persistent storage."""
        try:
            import json
            import os
            persistent_path = os.path.join("_data", "persistent.json")
            if os.path.exists(persistent_path):
                with open(persistent_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    directory = data.get("last_directory")
                    if directory and os.path.exists(directory):
                        return directory
        except Exception as e:
            self.logger.warning(f"Failed to load last directory: {e}")
        return None
    
    def save_last_directory(self, directory):
        """Save the last used directory to persistent storage."""
        try:
            import json
            import os
            persistent_path = os.path.join("_data", "persistent.json")
            os.makedirs("_data", exist_ok=True)
            
            # Load existing data
            existing_data = {}
            if os.path.exists(persistent_path):
                try:
                    with open(persistent_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception:
                    self.logger.warning("Failed to read existing persistent data")
            
            # Update last_directory
            existing_data["last_directory"] = directory
            
            # Write back
            with open(persistent_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
            
            self.logger.info(f"Saved last directory: {directory}")
        except Exception as e:
            self.logger.error(f"Failed to save last directory: {e}")
    
    def copy_csv_to_temp(self, source_path):
        """
        Copy CSV file to temporary directory with human-readable timestamp.
        
        Args:
            source_path: Path to the source CSV file
            
        Returns:
            str: Path to the copied CSV file, or None if copy failed
        """
        try:
            # Get temp directory from session, or create a new one if it doesn't exist
            temp_dir = self.page.session.get("temp_directory")
            
            if not temp_dir or not os.path.exists(temp_dir):
                # Create a new temp directory structure
                temp_base_dir = os.path.join(os.getcwd(), "storage", "temp")
                os.makedirs(temp_base_dir, exist_ok=True)
                
                # Create a unique subdirectory for this session
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
                temp_dir = os.path.join(temp_base_dir, f"file_selector_{session_id}")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Create subdirectories
                objs_dir = os.path.join(temp_dir, "OBJS")
                tn_dir = os.path.join(temp_dir, "TN")
                small_dir = os.path.join(temp_dir, "SMALL")
                os.makedirs(objs_dir, exist_ok=True)
                os.makedirs(tn_dir, exist_ok=True)
                os.makedirs(small_dir, exist_ok=True)
                
                # Store in session
                self.page.session.set("temp_directory", temp_dir)
                self.page.session.set("temp_objs_directory", objs_dir)
                self.page.session.set("temp_tn_directory", tn_dir)
                self.page.session.set("temp_small_directory", small_dir)
                
                self.logger.info(f"Created temporary directory structure: {temp_dir}")
            
            # Get the base filename and sanitize it
            base_name = os.path.basename(source_path)
            name, ext = os.path.splitext(base_name)
            sanitized_name = utils.sanitize_filename(name)
            
            # Add human-readable timestamp: YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{sanitized_name}_{timestamp}{ext}"
            
            # Create the destination path
            dest_path = os.path.join(temp_dir, new_filename)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied CSV file to: {dest_path}")
            
            return dest_path
            
        except Exception as e:
            self.logger.error(f"Failed to copy CSV file: {e}")
            return None
    
    def read_csv_file(self, file_path):
        """
        Read CSV or Excel file and extract column headers.
        Skips comment rows (rows where first column starts with #).
        
        Returns:
            tuple: (columns: list, error: str)
        """
        try:
            import pandas as pd
            
            # Determine file type and read accordingly
            if file_path.lower().endswith('.csv'):
                # Try multiple encodings for CSV files
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                df = None
                last_error = None
                
                for encoding in encodings:
                    try:
                        # Read all columns as strings to prevent scientific notation and type conversion
                        df = pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False)
                        self.logger.info(f"Successfully read CSV with encoding: {encoding}")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        last_error = f"Failed with encoding {encoding}"
                        continue
                
                if df is None:
                    return None, f"Could not read CSV file with any standard encoding. Last error: {last_error}"
                    
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return None, f"Unsupported file format: {file_path}"
            
            # Filter out comment rows (where first column starts with #)
            original_row_count = len(df)
            if len(df.columns) > 0:
                first_col = df.columns[0]
                comment_mask = df[first_col].astype(str).str.strip().str.startswith('#')
                comment_count = comment_mask.sum()
                
                if comment_count > 0:
                    self.logger.info(f"Skipping {comment_count} comment row(s) starting with '#' in CSV file")
                    df = df[~comment_mask]
            
            # Get column names
            columns = list(df.columns)
            self.logger.info(f"Found {len(columns)} columns in file: {columns}")
            
            return columns, None
            
        except ImportError:
            return None, "pandas library not available. Install with: pip install pandas openpyxl"
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return None, f"Error reading file: {str(e)}"
    
    def extract_column_data(self, file_path, column_name):
        """
        Extract data from a specific column in the CSV file.
        Skips comment rows (rows where first column starts with #).
        
        Returns:
            list: Non-empty values from the column
        """
        try:
            import pandas as pd
            import os
            
            file_ext = os.path.splitext(file_path)[1].lower()
            self.logger.info(f"Reading CSV file to extract column data: {file_path}")
            
            if file_ext == '.csv':
                # Try multiple encodings for CSV files
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                df = None
                
                for encoding in encodings:
                    try:
                        # Read all columns as strings to prevent scientific notation and type conversion
                        df = pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False)
                        self.logger.info(f"Successfully read CSV with encoding: {encoding}")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if df is None:
                    raise ValueError("Could not read CSV file with any standard encoding")
                    
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Filter out comment rows (where first column starts with #)
            if len(df.columns) > 0:
                first_col = df.columns[0]
                comment_mask = df[first_col].astype(str).str.strip().str.startswith('#')
                comment_count = comment_mask.sum()
                
                if comment_count > 0:
                    self.logger.info(f"Skipping {comment_count} comment row(s) starting with '#'")
                    df = df[~comment_mask]
            
            # Extract non-empty values from the selected column
            if column_name in df.columns:
                # Get non-null, non-empty values and convert to strings
                column_values = df[column_name].dropna().astype(str).str.strip()
                # Filter out empty strings after stripping
                non_empty_values = column_values[column_values != ''].tolist()
                
                self.logger.info(f"Extracted {len(non_empty_values)} non-empty values from column '{column_name}'")
                return non_empty_values
            else:
                self.logger.error(f"Column '{column_name}' not found in CSV file")
                return []
                
        except ImportError:
            self.logger.error("Pandas library not available for reading CSV data")
            return []
        except Exception as ex:
            self.logger.error(f"Error extracting data from column '{column_name}': {str(ex)}")
            return []
    
    def extract_display_template_info(self, file_path, filename_column):
        """
        Extract display_template information for each filename from the CSV.
        Skips comment rows (rows where first column starts with #).
        
        Args:
            file_path: Path to the CSV file
            filename_column: Name of the column containing filenames
            
        Returns:
            dict: Mapping of filename to display_template value, e.g. {'file1.jpg': 'image', 'interview.mp3': 'transcript'}
        """
        try:
            import pandas as pd
            import os
            
            file_ext = os.path.splitext(file_path)[1].lower()
            self.logger.info(f"Reading CSV file to extract display_template info: {file_path}")
            
            if file_ext == '.csv':
                # Try multiple encodings for CSV files
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False)
                        self.logger.info(f"Successfully read CSV with encoding: {encoding}")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if df is None:
                    raise ValueError("Could not read CSV file with any standard encoding")
                    
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Filter out comment rows (where first column starts with #)
            if len(df.columns) > 0:
                first_col = df.columns[0]
                comment_mask = df[first_col].astype(str).str.strip().str.startswith('#')
                comment_count = comment_mask.sum()
                
                if comment_count > 0:
                    self.logger.info(f"Skipping {comment_count} comment row(s) starting with '#' when extracting display_template info")
                    df = df[~comment_mask]
            
            # Check if both required columns exist
            if filename_column not in df.columns:
                self.logger.error(f"Filename column '{filename_column}' not found in CSV")
                return {}
            
            if 'display_template' not in df.columns:
                self.logger.info("No 'display_template' column found in CSV - returning empty dict")
                return {}
            
            # Build mapping of filename -> display_template
            transcript_info = {}
            for _, row in df.iterrows():
                filename = str(row[filename_column]).strip()
                display_template = str(row['display_template']).strip()
                
                # Only include non-empty filenames
                if filename:
                    transcript_info[filename] = display_template
            
            # Count how many transcript records we found
            transcript_count = sum(1 for v in transcript_info.values() if v.lower() == 'transcript')
            if transcript_count > 0:
                self.logger.info(f"Found {transcript_count} transcript records in CSV")
            
            return transcript_info
                
        except ImportError:
            self.logger.error("Pandas library not available for reading CSV data")
            return {}
        except Exception as ex:
            self.logger.error(f"Error extracting display_template info: {str(ex)}")
            return {}
    
    def update_csv_display(self):
        """Update the CSV file display with current session data."""
        if not self.csv_file_display:
            return
        
        colors = self.get_theme_colors()
        
        # Get session data
        current_csv_file = self.page.session.get("selected_csv_file")
        current_csv_columns = self.page.session.get("csv_columns")
        current_selected_column = self.page.session.get("selected_csv_column")
        current_csv_error = self.page.session.get("csv_read_error")
        search_directory = self.page.session.get("search_directory")
        search_directories = self.page.session.get("search_directories") or []
        
        # Migrate old single directory to list format if needed
        if search_directory and not search_directories:
            search_directories = [search_directory]
            self.page.session.set("search_directories", search_directories)
        
        csv_validation_passed = self.page.session.get("csv_validation_passed")
        csv_validation_error = self.page.session.get("csv_validation_error")
        csv_unmatched_headings = self.page.session.get("csv_unmatched_headings") or []
        
        # Update container visibility
        self.file_selection_container.visible = True
        self.columns_display_container.visible = bool(current_csv_file and (current_csv_columns or current_csv_error))
        self.results_display_container.visible = bool(current_selected_column)
        self.search_container.visible = bool(current_selected_column)
        
        # Clear current display
        self.csv_file_display.controls.clear()
        
        # === STEP 1: File Selection ===
        # file_selection_content = ft.Column([
        #     ft.ElevatedButton("Select CSV File", icon=ft.Icons.FILE_UPLOAD, on_click=self.open_csv_file_picker),
        # ], spacing=10)
        
        file_selection_content = ft.Row([
            ft.Container(width=10),  # 10 space indentation
            ft.Container(
                content=ft.ElevatedButton("Select CSV File", icon=ft.Icons.FILE_UPLOAD, on_click=self.open_csv_file_picker),
                margin=ft.margin.only(bottom=10)  # Small margin below button
            ),
        ], spacing=0, alignment=ft.MainAxisAlignment.START)

        if current_csv_file:
            import os
            filename = os.path.basename(current_csv_file)
            file_selection_content.controls.extend([
                ft.Container(height=5),
                ft.Text(f"✅ Selected: {filename}", size=14, color=colors['primary_text']),
                ft.Text(f"Path: {current_csv_file}", size=12, color=colors['secondary_text']),
                ft.Row([
                    ft.ElevatedButton("Clear Selection", on_click=self.on_clear_csv_selection, scale=0.8),
                    ft.ElevatedButton("Reload File", on_click=self.reload_csv_file, scale=0.8)
                ], alignment=ft.MainAxisAlignment.START)
            ])
        
        # Build subtitle for Step 1 with validation status
        step1_subtitle = "Choose your CSV/Excel file"
        if current_csv_file:
            filename = os.path.basename(current_csv_file)
            if csv_validation_passed:
                # Validation passed
                current_mode = self.page.session.get("selected_mode")
                if csv_unmatched_headings and current_mode == 'CollectionBuilder':
                    step1_subtitle = f"✅ Selected: {filename} (validated, {len(csv_unmatched_headings)} extra heading(s))"
                else:
                    step1_subtitle = f"✅ Selected: {filename} (validated)"
            elif csv_validation_passed is False:
                # Validation failed
                step1_subtitle = f"❌ Selected: {filename} (validation failed)"
            else:
                # No validation attempted
                step1_subtitle = f"✅ Selected: {filename}"
        
        self.file_selection_container.content = ft.ExpansionTile(
            title=ft.Text("File Selection", weight=ft.FontWeight.BOLD),
            subtitle=ft.Text(step1_subtitle),
            leading=ft.Icon(ft.Icons.FILE_UPLOAD),
            initially_expanded=not bool(current_csv_file),
            controls=[file_selection_content]
        )
        
        # === STEP 2: Column Selection ===
        if current_csv_file:
            columns_content = ft.Column([], spacing=10)
            
            if current_csv_error:
                columns_content.controls.extend([
                    ft.Text("❌ Error reading file:", size=14, weight=ft.FontWeight.BOLD, color=colors['error']),
                    ft.Text(current_csv_error, size=12, color=colors['error'])
                ])
                
                # If validation failed, show unmatched headings
                if csv_validation_passed is False and csv_unmatched_headings:
                    columns_content.controls.extend([
                        ft.Container(height=10),
                        ft.Text("Unmatched headings:", size=13, weight=ft.FontWeight.BOLD, color=colors['error']),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"• {heading}", size=12, color=colors['secondary_text'])
                                for heading in sorted(csv_unmatched_headings)
                            ], spacing=2),
                            padding=10,
                            bgcolor=colors['container_bg'],
                            border_radius=5
                        ),
                        ft.Container(height=5),
                        ft.Text(
                            "💡 Tip: For best results, ensure headings match the CollectionBuilder metadata standard.",
                            size=11,
                            italic=True,
                            color=colors['secondary_text']
                        )
                    ])

            elif current_csv_columns and len(current_csv_columns) > 0:
                # Show column selector for CollectionBuilder
                columns_content.controls.extend([
                        # ft.Container(height=10),
                        ft.Container(
                            content=ft.Row([
                                ft.Container(width=10),  # 10 space indentation
                                ft.Column([
                                    ft.Text("Select column containing filenames:", size=14, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                                    ft.Dropdown(
                                        label="Choose filename column",
                                        value=current_selected_column if current_selected_column else "",
                                        options=[ft.dropdown.Option(col) for col in current_csv_columns],
                                        on_change=self.on_column_selection_change,
                                        width=300
                                    )
                                ], spacing=5, alignment=ft.CrossAxisAlignment.START)
                            ], alignment=ft.MainAxisAlignment.START),
                            margin=ft.margin.only(bottom=10)  # Small margin below control
                        )
                    ])
                
                # Show processing results if a column is selected
                if current_selected_column:
                    selected_files = self.page.session.get("selected_file_paths") or []
                    
                    # Get original count - should be set when column is selected
                    original_count = self.page.session.get("original_filename_count")
                    
                    # Use original count if available, otherwise current count
                    if original_count is not None:
                        extracted_filename_count = original_count
                    else:
                        extracted_filename_count = len(selected_files)
                    
            else:
                columns_content.controls.extend([
                    ft.Text("⚠️ No columns detected in file", size=14, weight=ft.FontWeight.BOLD, color=colors['error']),
                    ft.Text("The file might be empty or in an unsupported format.", size=12, color=colors['secondary_text'])
                ])
            
            # Determine subtitle based on completion status
            if current_selected_column:
                # Get extracted filename count for subtitle
                selected_files = self.page.session.get("selected_file_paths") or []
                original_count = self.page.session.get("original_filename_count")
                
                # Use original count if available, otherwise current count
                if original_count is not None:
                    extracted_count = original_count
                else:
                    extracted_count = len(selected_files)
                
                column_subtitle = f"✅ Selected '{current_selected_column}' - extracted {extracted_count} potential filenames"
            elif current_csv_error:
                column_subtitle = f"❌ Error reading file: {current_csv_error[:50]}..."
            elif current_csv_columns and len(current_csv_columns) > 0:
                column_subtitle = f"Found {len(current_csv_columns)} columns - choose the filename column"
            else:
                column_subtitle = "Choose the column containing filenames"
            
            self.columns_display_container.content = ft.ExpansionTile(
                title=ft.Text("Column Selection", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(column_subtitle),
                leading=ft.Icon(ft.Icons.VIEW_COLUMN),
                initially_expanded=bool(current_csv_columns and not current_selected_column),
                controls=[columns_content]
            )
            
            self.page.update( )
        
        # === STEP 3: Fuzzy Search ===
        if current_selected_column:
            selected_files = self.page.session.get("selected_file_paths") or []
            
            # Get original count and search statistics
            original_count = self.page.session.get("original_filename_count")
            search_completed = self.page.session.get("search_completed")
            if search_completed is None:
                search_completed = False
            
            # Use original count if available, otherwise current count
            if original_count is not None:
                extracted_filename_count = original_count
            else:
                extracted_filename_count = len(selected_files)
            
            # Check if files have been matched (full paths vs just filenames)
            has_full_paths = any(os.path.isabs(f) for f in selected_files if f)
            
            # Debug: Show what types of paths we have
            absolute_paths = [f for f in selected_files if f and os.path.isabs(f)]
            relative_paths = [f for f in selected_files if f and not os.path.isabs(f)]
            print(f"Debug paths - Absolute: {len(absolute_paths)}, Relative: {len(relative_paths)}")
            if len(selected_files) > 0:
                print(f"First 3 files: {selected_files[:3]}")
            
            # Get search statistics
            matched_count = self.page.session.get("matched_file_count")
            
            # For display purposes
            if search_completed and original_count is not None and matched_count is not None:
                display_original_count = original_count
                display_matched_count = matched_count
            else:
                display_original_count = extracted_filename_count
                display_matched_count = len([f for f in selected_files if f and os.path.isabs(f)]) if has_full_paths else 0
            
            # Build directory list display
            directory_controls = []
            if search_directories:
                for idx, dir_path in enumerate(search_directories):
                    directory_controls.append(
                        ft.Row([
                            ft.Icon(ft.Icons.FOLDER, size=16, color=colors['secondary_text']),
                            ft.Text(dir_path, size=11, color=colors['secondary_text'], expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                tooltip="Remove directory",
                                on_click=lambda e, i=idx: self.remove_search_directory(e, i)
                            )
                        ], spacing=5)
                    )
            else:
                directory_controls.append(
                    ft.Text("No directories selected", size=11, color=colors['secondary_text'], italic=True)
                )
            
            search_content_column = ft.Column([
                ft.Text("Search directories:", size=12, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Container(
                    content=ft.Column(directory_controls, spacing=0),
                    padding=5,
                    border=ft.border.all(1, colors['border']),
                    border_radius=5
                ),
                ft.Container(height=5),
                ft.Row([
                    ft.ElevatedButton(
                        "Add Search Directory",
                        icon=ft.Icons.CREATE_NEW_FOLDER,
                        on_click=self.open_search_dir_picker
                    ),
                    ft.ElevatedButton(
                        "Launch Search",
                        icon=ft.Icons.ROCKET_LAUNCH,
                        on_click=self.launch_fuzzy_search,
                        disabled=(len(search_directories) == 0),
                        bgcolor=ft.Colors.BLUE_700 if len(search_directories) > 0 else None,
                        color=ft.Colors.WHITE if len(search_directories) > 0 else None
                    )
                ], spacing=10),
                ft.Container(height=10),
                ft.Text("Add one or more directories, then click 'Launch Search' to find matching files.",
                       size=11, color=colors['secondary_text'], italic=True)
            ], spacing=5, alignment=ft.CrossAxisAlignment.START)
            
            self.page.update( )
            
            # === Show results after fuzzy search completes ===
            if search_completed:
                # Status summary
                unmatched_count = display_original_count - display_matched_count
                status_color = ft.Colors.GREEN_600 if unmatched_count == 0 else ft.Colors.ORANGE_600
                
                search_content_column.controls.append(ft.Container(height=10))
                search_content_column.controls.append(
                    ft.Text(
                        f"✅ Search Complete: {display_matched_count} of {display_original_count} files matched", 
                        size=13, 
                        color=status_color, 
                        weight=ft.FontWeight.BOLD
                    )
                )
                
                # Show matched files
                matched_ratios = self.page.session.get("matched_ratios") or []
                self.logger.info(f"Display: selected_files has {len(selected_files)} items, matched_ratios has {len(matched_ratios)} items")
                
                if selected_files and len(selected_files) > 0:
                    # Create copy to clipboard function for matched files
                    def copy_matched_to_clipboard(e):
                        selected = self.page.session.get("selected_file_paths") or []
                        ratios = self.page.session.get("matched_ratios") or []
                        csv_filenames = self.page.session.get("csv_filenames_for_matched") or []
                        
                        if selected:
                            # Create list with filenames and match percentages
                            clipboard_lines = []
                            for i, filepath in enumerate(selected):
                                if filepath:
                                    target_filename = csv_filenames[i] if i < len(csv_filenames) else os.path.basename(filepath)
                                    ratio = ratios[i] if i < len(ratios) else 100
                                    
                                    if ratio < 100:
                                        # Include matched file path for imperfect matches
                                        clipboard_lines.append(f"{target_filename} ({ratio}%) -> {filepath}")
                                    else:
                                        clipboard_lines.append(f"{target_filename} ({ratio}%)")
                            
                            clipboard_text = "\n".join(clipboard_lines)
                            self.page.set_clipboard(clipboard_text)
                            self.logger.info(f"Copied {len(clipboard_lines)} matched filenames to clipboard")
                            self.show_snack(f"Copied {len(clipboard_lines)} matched filenames to clipboard")
                    
                    search_content_column.controls.append(ft.Container(height=10))
                    search_content_column.controls.append(
                        ft.Row([
                            ft.Text("Matched files:", size=12, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                icon_size=16,
                                tooltip="Copy matched filenames to clipboard",
                                on_click=copy_matched_to_clipboard,
                                icon_color=colors['primary_text']
                            )
                        ], spacing=5, alignment=ft.MainAxisAlignment.START)
                    )
                    
                    matched_items = []
                    # Get the CSV filenames (target names) for matched files
                    csv_filenames = self.page.session.get("csv_filenames_for_matched") or []
                    selected_paths = self.page.session.get("selected_file_paths") or []
                    
                    # Since selected_files only contains matched paths, and matched_ratios align with them
                    for i, filepath in enumerate(selected_files):
                        if filepath:  # Should all be absolute paths
                            ratio = matched_ratios[i] if i < len(matched_ratios) else 100
                            target_filename = csv_filenames[i] if i < len(csv_filenames) else os.path.basename(filepath)
                            
                            # Main display line
                            display_text = f"{target_filename} ({ratio}%)"
                            text_color = colors['secondary_text'] if ratio == 100 else ft.Colors.ORANGE_600
                            main_text = ft.Text(display_text, size=11, color=text_color)
                            matched_items.append(main_text)
                            
                            # If ratio < 100%, show the matched file path
                            if ratio < 100:
                                matched_path = selected_paths[i] if i < len(selected_paths) else filepath
                                matched_file_text = ft.Text(
                                    f"  └─ Matched to: {matched_path}",
                                    size=10,
                                    color=ft.Colors.BLUE_300,
                                    italic=True
                                )
                                matched_items.append(matched_file_text)
                    
                    self.logger.info(f"Display: Created {len(matched_items)} matched items")
                    
                    if matched_items:
                        list_height = min(200, len(matched_items) * 20 + 10)
                        self.logger.info(f"Display: Creating ListView with height={list_height}")
                        
                        matched_list_view = ft.ListView(matched_items, spacing=2, height=list_height)
                        
                        search_content_column.controls.append(
                            ft.Container(
                                content=matched_list_view,
                                border=ft.border.all(1, colors['border']),
                                border_radius=5,
                                padding=10,
                                margin=ft.margin.symmetric(vertical=5)
                            )
                        )
                        self.logger.info(f"Display: Added matched files container to search_content_column")
                    else:
                        search_content_column.controls.append(
                            ft.Text("No matched files to display", size=11, color=colors['secondary_text'], italic=True)
                        )
                
                # Show unmatched files
                unmatched_filenames = self.page.session.get("unmatched_filenames") or []
                self.logger.info(f"Display: unmatched_filenames has {len(unmatched_filenames)} items")
                
                if unmatched_filenames:
                    # Create copy to clipboard function for unmatched files
                    def copy_unmatched_to_clipboard(e):
                        unmatched = self.page.session.get("unmatched_filenames") or []
                        if unmatched:
                            # Handle both old format (strings) and new format (dicts)
                            clipboard_lines = []
                            for item in unmatched:
                                if isinstance(item, dict):
                                    filename = item.get('filename', '')
                                    best_path = item.get('best_path', '')
                                    best_ratio = item.get('best_ratio', 0)
                                    if best_path and best_ratio > 0:
                                        clipboard_lines.append(f"{filename} (best match: {best_path}, {best_ratio}%)")
                                    else:
                                        clipboard_lines.append(filename)
                                else:
                                    # Old format - just a string
                                    clipboard_lines.append(item)
                            
                            clipboard_text = "\n".join(clipboard_lines)
                            self.page.set_clipboard(clipboard_text)
                            self.logger.info(f"Copied {len(unmatched)} unmatched filenames to clipboard")
                            self.show_snack(f"Copied {len(unmatched)} unmatched filenames to clipboard")
                    
                    search_content_column.controls.append(ft.Container(height=10))
                    search_content_column.controls.append(
                        ft.Row([
                            ft.Text(
                                f"⚠️ {len(unmatched_filenames)} unmatched files:", 
                                size=12, 
                                weight=ft.FontWeight.BOLD, 
                                color=ft.Colors.RED_600
                            ),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                icon_size=16,
                                tooltip="Copy unmatched filenames to clipboard",
                                on_click=copy_unmatched_to_clipboard,
                                icon_color=ft.Colors.RED_600
                            )
                        ], spacing=5, alignment=ft.MainAxisAlignment.START)
                    )
                    
                    # Create unmatched items with best match info
                    unmatched_items = []
                    for item in unmatched_filenames[:20]:  # Limit to first 20
                        if isinstance(item, dict):
                            filename = item.get('filename', '')
                            best_path = item.get('best_path', '')
                            best_ratio = item.get('best_ratio', 0)
                            
                            # Create main text with filename
                            main_text = ft.Text(filename, size=11, color=ft.Colors.RED_400)
                            
                            # Add best match info if available (path exists and ratio > 0)
                            if best_path and best_ratio > 0:
                                best_match_text = ft.Text(
                                    f"  └─ Best match ({best_ratio}%): {best_path}",
                                    size=10,
                                    color=ft.Colors.ORANGE_300,
                                    italic=True
                                )
                                unmatched_items.extend([main_text, best_match_text])
                            else:
                                unmatched_items.append(main_text)
                        else:
                            # Old format - just a string
                            unmatched_items.append(ft.Text(item, size=11, color=ft.Colors.RED_400))
                    
                    
                    if len(unmatched_filenames) > 20:
                        unmatched_items.append(
                            ft.Text(f"... and {len(unmatched_filenames) - 20} more", 
                                   size=11, color=ft.Colors.RED_400, italic=True)
                        )
                    
                    unmatched_height = min(150, len(unmatched_items) * 20 + 10)
                    self.logger.info(f"Display: Creating unmatched ListView with {len(unmatched_items)} items, height={unmatched_height}")
                    
                    search_content_column.controls.append(
                        ft.Container(
                            content=ft.ListView(unmatched_items, spacing=2, height=unmatched_height),
                            border=ft.border.all(1, ft.Colors.RED_200),
                            border_radius=5,
                            padding=10,
                            margin=ft.margin.symmetric(vertical=5),
                            bgcolor=ft.Colors.RED_50
                        )
                    )
            else:
                # Before search
                search_content_column.controls.append(ft.Container(height=10))
                search_content_column.controls.append(
                    ft.Text(
                        "⚠️ Select a search directory above to begin fuzzy search", 
                        size=12, 
                        color=ft.Colors.ORANGE_600, 
                        weight=ft.FontWeight.BOLD
                    )
                )

            self.page.update( )

            # Determine subtitle based on search completion status
            search_directories = self.page.session.get("search_directories") or []
            
            if has_full_paths and search_completed:
                # Search completed with matches
                search_subtitle = f"✅ Found {display_matched_count} of {display_original_count} file matches"
                if display_matched_count < display_original_count:
                    unmatched = display_original_count - display_matched_count
                    search_subtitle += f" ({unmatched} unmatched)"
            elif search_completed and not has_full_paths:
                # Search completed but no matches
                search_subtitle = "❌ Search completed but no matches found"
            elif search_directories:
                # Directory(ies) selected but search not yet run
                dir_count = len(search_directories)
                if dir_count == 1:
                    search_subtitle = f"Ready to search in: {os.path.basename(search_directories[0])}"
                else:
                    search_subtitle = f"Ready to search in {dir_count} directories"
            else:
                # Initial state
                search_subtitle = "Match filenames to actual files"

            # Create the ExpansionTile directly with the column (no extra Row wrapper needed)
            self.search_container.content = ft.ExpansionTile(
                title=ft.Text("Fuzzy Search", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(search_subtitle),
                leading=ft.Icon(ft.Icons.SEARCH),
                initially_expanded=True,
                controls=[search_content_column]  # Pass the column directly
            )
        
        # Add all containers to display
        self.csv_file_display.controls.extend([
            self.file_selection_container,
            self.columns_display_container,
            self.search_container
        ])
        
        self.page.update()
    
    def open_csv_file_picker(self, e):
        """Open the CSV file picker."""
        last_directory = self.load_last_directory()
        
        if last_directory and os.path.exists(last_directory):
            self.logger.info(f"Using last directory: {last_directory}")
            self.csv_file_picker.pick_files(
                dialog_title="Select CSV or Excel File",
                allow_multiple=False,
                allowed_extensions=["csv", "xlsx", "xls"],
                initial_directory=last_directory
            )
        else:
            self.csv_file_picker.pick_files(
                dialog_title="Select CSV or Excel File",
                allow_multiple=False,
                allowed_extensions=["csv", "xlsx", "xls"]
            )
    
    def on_csv_file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle CSV file selection."""
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            self.page.session.set("selected_csv_file", file_path)
            self.logger.info(f"Selected CSV file: {file_path}")
            
            # Store directory
            import os
            directory = os.path.dirname(file_path)
            self.save_last_directory(directory)
            
            # Validate CSV headings against verified headings for the current mode
            current_mode = self.page.session.get("selected_mode")
            csv_validation_passed = False
            csv_validation_error = None
            csv_unmatched_headings = []
            
            if current_mode:
                is_valid, unmatched_headings, error = utils.validate_csv_headings(file_path, current_mode)
                
                if error:
                    # Validation error (file not found, encoding issue, etc.)
                    csv_validation_error = error
                    self.logger.error(f"CSV validation error: {error}")
                    self.page.session.set("csv_validation_passed", False)
                    self.page.session.set("csv_validation_error", error)
                    self.page.session.set("csv_unmatched_headings", [])
                elif not is_valid:
                    # Validation failed - unmatched headings found
                    csv_validation_error = f"CSV contains {len(unmatched_headings)} unverified heading(s) for {current_mode} mode"
                    csv_unmatched_headings = unmatched_headings
                    self.logger.error(f"CSV validation failed: {csv_validation_error}")
                    self.logger.error(f"Unmatched headings: {', '.join(unmatched_headings)}")
                    self.page.session.set("csv_validation_passed", False)
                    self.page.session.set("csv_validation_error", csv_validation_error)
                    self.page.session.set("csv_unmatched_headings", unmatched_headings)
                else:
                    # Validation passed
                    csv_validation_passed = True
                    self.logger.info(f"✓ CSV validation passed for {current_mode} mode")
                    if unmatched_headings:
                        # CollectionBuilder mode - report extra headings but allow
                        self.logger.warning(f"Note: CSV contains {len(unmatched_headings)} extra heading(s) not in verified list: {', '.join(unmatched_headings)}")
                    self.page.session.set("csv_validation_passed", True)
                    self.page.session.set("csv_validation_error", None)
                    self.page.session.set("csv_unmatched_headings", unmatched_headings)
            else:
                # No mode selected - skip validation but allow processing
                self.logger.warning("No mode selected - skipping CSV validation")
                csv_validation_passed = True
                self.page.session.set("csv_validation_passed", True)
                self.page.session.set("csv_validation_error", "No mode selected")
                self.page.session.set("csv_unmatched_headings", [])
            
            # If validation failed, stop processing and update display
            if not csv_validation_passed:
                # Still save the file path so user can see what failed
                self.page.session.set("csv_columns", None)
                self.page.session.set("csv_read_error", csv_validation_error)
                self.page.session.set("temp_csv_file", None)
                self.page.session.set("temp_csv_filename", None)
                self.update_csv_display()
                return
            
            # Create a working copy of the CSV file in temp directory
            temp_csv_path = self.copy_csv_to_temp(file_path)
            if temp_csv_path:
                self.page.session.set("temp_csv_file", temp_csv_path)
                # Store just the basename for easy access
                temp_csv_basename = os.path.basename(temp_csv_path)
                self.page.session.set("temp_csv_filename", temp_csv_basename)
                self.logger.info(f"Created working copy at: {temp_csv_path}")
            else:
                self.page.session.set("temp_csv_file", None)
                self.page.session.set("temp_csv_filename", None)
                self.logger.warning("No working copy created - temp directory not available")
            
            # Read columns
            columns, error = self.read_csv_file(file_path)
            
            if columns:
                self.page.session.set("csv_columns", columns)
                self.page.session.set("csv_read_error", None)
                self.logger.info(f"Successfully read {len(columns)} columns")
                
                # Clear previous selection (CollectionBuilder mode)
                self.page.session.set("selected_csv_column", None)
            else:
                self.page.session.set("csv_columns", None)
                self.page.session.set("csv_read_error", error)
                self.logger.error(f"Failed to read CSV: {error}")
                
                # Clear previous selections
                self.page.session.set("selected_csv_column", None)
            
            # Clear search statistics
            self.page.session.set("selected_file_paths", [])
            self.page.session.set("original_filename_count", None)
            self.page.session.set("matched_file_count", None)
            self.page.session.set("matched_ratios", None)
            self.page.session.set("unmatched_filenames", None)
            self.page.session.set("search_completed", False)
            
            self.update_csv_display()
        else:
            self.logger.info("No CSV file selected")
    
    def on_clear_csv_selection(self, e):
        """Clear CSV selection."""
        self.page.session.set("selected_csv_file", None)
        self.page.session.set("temp_csv_file", None)
        self.page.session.set("temp_csv_filename", None)
        self.page.session.set("csv_columns", None)
        self.page.session.set("selected_csv_column", None)
        self.page.session.set("csv_read_error", None)
        self.page.session.set("csv_validation_passed", None)
        self.page.session.set("csv_validation_error", None)
        self.page.session.set("csv_unmatched_headings", None)
        self.page.session.set("selected_file_paths", [])
        self.page.session.set("search_directory", None)
        self.page.session.set("search_directories", [])
        self.page.session.set("original_filename_count", None)
        self.page.session.set("matched_file_count", None)
        self.page.session.set("matched_ratios", None)
        self.page.session.set("unmatched_filenames", None)
        self.page.session.set("search_completed", False)
        self.clear_temp_directory()  # Also clear temp directory
        self.logger.info("Cleared CSV selection")
        self.update_csv_display()
    
    def reload_csv_file(self, e):
        """Reload the current CSV file."""
        current_csv_file = self.page.session.get("selected_csv_file")
        if current_csv_file:
            self.logger.info(f"Reloading CSV file: {current_csv_file}")
            columns, error = self.read_csv_file(current_csv_file)
            
            if columns:
                self.page.session.set("csv_columns", columns)
                self.page.session.set("csv_read_error", None)
            else:
                self.page.session.set("csv_columns", None)
                self.page.session.set("csv_read_error", error)
            
            self.update_csv_display()
    
    def on_column_selection_change(self, e):
        """Handle column selection."""
        selected_col = e.control.value
        self.page.session.set("selected_csv_column", selected_col)
        self.logger.info(f"Selected column: {selected_col}")
        
        # Clear search statistics when changing columns
        self.page.session.set("original_filename_count", None)
        self.page.session.set("matched_file_count", None)
        self.page.session.set("matched_ratios", None)
        self.page.session.set("unmatched_filenames", None)
        self.page.session.set("search_completed", False)
        self.page.session.set("transcript_info", None)  # Clear transcript info
        
        if selected_col:
            current_csv_file = self.page.session.get("selected_csv_file")
            if current_csv_file:
                # Extract data from column
                column_data = self.extract_column_data(current_csv_file, selected_col)
                self.page.session.set("selected_file_paths", column_data)
                # Set the original count when we first extract the filenames
                original_count = len(column_data)
                self.page.session.set("original_filename_count", original_count)
                self.logger.info(f"Extracted {len(column_data)} potential filenames")
                
                # Also extract display_template information for transcript handling
                transcript_info = self.extract_display_template_info(current_csv_file, selected_col)
                self.page.session.set("transcript_info", transcript_info)
                if transcript_info:
                    transcript_count = sum(1 for v in transcript_info.values() if v.lower() == 'transcript')
                    if transcript_count > 0:
                        self.logger.info(f"Stored display_template info for {len(transcript_info)} records ({transcript_count} transcripts)")
        else:
            self.page.session.set("selected_file_paths", [])
        
        self.update_csv_display()
    
    def open_search_dir_picker(self, e):
        """Open directory picker for fuzzy search, starting from last selected location."""
        # Get the last selected directory to use as initial directory
        search_directories = self.page.session.get("search_directories") or []
        initial_directory = search_directories[-1] if search_directories else None
        
        if initial_directory:
            self.search_dir_picker.get_directory_path(
                dialog_title="Select Directory for Fuzzy Search (can add multiple)",
                initial_directory=initial_directory
            )
        else:
            self.search_dir_picker.get_directory_path(
                dialog_title="Select Directory for Fuzzy Search (can add multiple)"
            )
    
    def remove_search_directory(self, e, index):
        """Remove a directory from the search directories list."""
        search_directories = self.page.session.get("search_directories") or []
        if 0 <= index < len(search_directories):
            removed_dir = search_directories.pop(index)
            self.page.session.set("search_directories", search_directories)
            
            # If this was the last directory, also clear the old single directory field
            if not search_directories:
                self.page.session.set("search_directory", None)
                # Clear search results when removing all directories
                self.page.session.set("search_completed", False)
                self.page.session.set("matched_file_count", None)
                self.page.session.set("original_filename_count", None)
            
            self.logger.info(f"Removed search directory: {removed_dir}")
            self.update_csv_display()
    
    def on_search_dir_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle search directory selection and add to list."""
        if e.path:
            search_directories = self.page.session.get("search_directories") or []
            
            # Check if directory already exists in list
            if e.path not in search_directories:
                search_directories.append(e.path)
                self.page.session.set("search_directories", search_directories)
                self.page.session.set("search_directory", e.path)  # Keep for backward compatibility
                self.logger.info(f"Added search directory: {e.path}")
                self.update_csv_display()
            else:
                self.logger.info(f"Directory already in list: {e.path}")
                self.update_csv_display()
    
    def launch_fuzzy_search(self, e):
        """Launch the fuzzy search across all selected directories."""
        search_directories = self.page.session.get("search_directories") or []
        
        if not search_directories:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Please add at least one search directory first"),
                bgcolor=ft.Colors.ORANGE_700
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        self.logger.info(f"Launching fuzzy search across {len(search_directories)} directories")
        self.auto_perform_workflow()
    
    def auto_perform_workflow(self):
        """Automatically perform fuzzy search and link creation across all search directories."""
        selected_files = self.page.session.get("selected_file_paths") or []
        search_directories = self.page.session.get("search_directories") or []
        
        if not selected_files:
            self.logger.warning("No files available for automatic workflow")
            return
        
        if not search_directories:
            self.logger.warning("No files available for automatic workflow")
            return
        
        # Show progress dialog for the entire workflow
        progress_dialog = ft.AlertDialog(
            title=ft.Text("Processing Files"),
            content=ft.Column([
                ft.Text("Performing fuzzy search and creating links..."),
                ft.ProgressRing()
            ], tight=True, height=100),
            modal=True
        )
        
        self.page.overlay.append(progress_dialog)
        progress_dialog.open = True
        self.page.update()
        
        try:
            # Step 1: Perform fuzzy search across all directories
            self.logger.info(f"Auto-workflow: Starting fuzzy search for {len(selected_files)} files across {len(search_directories)} directories")
            
            # Call the fuzzy search logic (extracted from do_fuzzy_search)
            results = self.perform_fuzzy_search_workflow(search_directories, selected_files)
            
            if results is None:  # Search was cancelled or failed
                progress_dialog.open = False
                self.page.update()
                return
            
            # Create symbolic links for matched files
            matched_files = self.page.session.get("selected_file_paths") or []
            full_path_files = [f for f in matched_files if f and os.path.isabs(f) and os.path.exists(f)]
            
            # Also get transcript CSV files if any
            transcript_csv_files = self.page.session.get("transcript_csv_files") or []
            
            if full_path_files:
                self.logger.info(f"Auto-workflow: Creating symbolic links for {len(full_path_files)} matched files")
                temp_files, temp_file_info, temp_dir = self.copy_files_to_temp_directory(full_path_files)
                
                # Create links for transcript CSV files in separate TRANSCRIPTS directory
                if transcript_csv_files:
                    self.logger.info(f"Auto-workflow: Creating symbolic links for {len(transcript_csv_files)} transcript CSV files")
                    transcript_temp_files = self.copy_transcript_files_to_temp_directory(transcript_csv_files, temp_dir)
                    self.logger.info(f"Created links for {len(transcript_temp_files)} transcript CSV files in {temp_dir}/TRANSCRIPTS")
                
                # Update selected_file_paths to point to temp files so derivatives are created there
                self.page.session.set("selected_file_paths", temp_files)
                
                # Close progress dialog
                progress_dialog.open = False
                self.page.update()
                
                # Show result with transcript info
                result_message = f"Found {len(full_path_files)} matches and created links successfully."
                if transcript_csv_files:
                    result_message += f" Also created links for {len(transcript_csv_files)} transcript CSV files."
                result_message += " Use the Derivatives menu to generate thumbnails and other derivatives."
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(result_message),
                    bgcolor=ft.Colors.GREEN_400
                )
            else:
                # Close progress dialog
                progress_dialog.open = False
                self.page.update()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Search completed but no file matches were found"),
                    bgcolor=ft.Colors.ORANGE_400
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
            # Refresh the display
            self.update_csv_display()
            
        except Exception as ex:
            # Close progress dialog on error
            progress_dialog.open = False
            self.page.update()
            
            self.logger.error(f"Error during automatic workflow: {str(ex)}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error during automatic workflow: {str(ex)}"),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def perform_fuzzy_search_workflow(self, search_dirs, selected_files):
        """Perform the fuzzy search workflow across multiple directories and return results."""
        try:
            # Get transcript info from session
            transcript_info = self.page.session.get("transcript_info") or {}
            
            # Define progress callback (simplified for auto mode)
            def update_progress(progress):
                # Could add more detailed progress tracking here if needed
                pass
            
            # Define cancel check
            def check_cancel():
                return False  # No cancellation in auto mode
            
            # Combine results from all directories
            combined_results = {}
            transcript_csv_files = []  # Track transcript CSV files found
            
            # Search each directory and keep best matches
            for search_dir in search_dirs:
                self.logger.info(f"Searching in directory: {search_dir}")
                
                # Perform the fuzzy search in this directory (with transcript support)
                results = utils.perform_fuzzy_search_batch(
                    search_dir, 
                    selected_files,
                    threshold=90,
                    progress_callback=update_progress,
                    cancel_check=check_cancel,
                    transcript_info=transcript_info  # Pass transcript info
                )
                
                if results is None:
                    continue
                
                # Merge results, keeping best matches
                for filename, result_tuple in results.items():
                    # Check if this is a transcript result (3-tuple) or normal result (2-tuple)
                    if len(result_tuple) == 3:
                        # Transcript result: (media_path, ratio, transcript_csv_path)
                        match_path, ratio, transcript_csv = result_tuple
                        
                        # Store transcript CSV if found
                        if transcript_csv:
                            transcript_csv_files.append(transcript_csv)
                            self.logger.info(f"Found transcript CSV: {transcript_csv}")
                        
                        # Update combined results with media file
                        if filename not in combined_results or ratio > combined_results[filename][1]:
                            combined_results[filename] = (match_path, ratio)
                    else:
                        # Normal result: (match_path, ratio)
                        match_path, ratio = result_tuple
                        if filename not in combined_results or ratio > combined_results[filename][1]:
                            combined_results[filename] = (match_path, ratio)
            
            # Store transcript CSV files in session for later use
            if transcript_csv_files:
                self.page.session.set("transcript_csv_files", transcript_csv_files)
                self.logger.info(f"Stored {len(transcript_csv_files)} transcript CSV files for later processing")
            
            if not combined_results:
                return None
            
            # Process results (same logic as in do_fuzzy_search)
            matched_paths = []
            matched_ratios = []
            unmatched_filenames = []
            csv_filenames_for_matched = []  # Track CSV filenames for successfully matched files
            matches_found = 0
            original_count = len(selected_files)
            
            for filename in selected_files:
                match_path, ratio = combined_results.get(filename, (None, 0))
                if match_path and ratio >= 90:
                    matched_paths.append(match_path)
                    matched_ratios.append(ratio)
                    csv_filenames_for_matched.append(filename)  # Store original CSV filename
                    matches_found += 1
                    self.logger.info(f"Auto-workflow: Found match for '{filename}': {match_path} ({ratio}% match)")
                else:
                    matched_paths.append(None)
                    # Store unmatched filename with best match info (filename, best_path, best_ratio)
                    unmatched_filenames.append({
                        'filename': filename,
                        'best_path': match_path,
                        'best_ratio': ratio
                    })
                    # Log unmatched files with severity based on fuzzy score
                    if ratio == 0:
                        self.logger.error(f"Auto-workflow: No match found for '{filename}' (0% match)")
                    elif ratio < 50:
                        self.logger.error(f"Auto-workflow: No match found for '{filename}' ({ratio}% match - very low)")
                    elif ratio < 90:
                        self.logger.warning(f"Auto-workflow: No match found for '{filename}' ({ratio}% match - below 90% threshold)")
                    else:
                        self.logger.info(f"Auto-workflow: No match found for '{filename}' meeting 90% threshold)")
            
            # Store search statistics
            self.page.session.set("original_filename_count", original_count)
            self.page.session.set("matched_file_count", matches_found)
            self.page.session.set("matched_ratios", matched_ratios)
            self.page.session.set("unmatched_filenames", unmatched_filenames)
            self.page.session.set("search_completed", True)
            
            # Update session with matched paths and CSV filenames
            self.page.session.set("selected_file_paths", [p for p in matched_paths if p is not None])
            self.page.session.set("csv_filenames_for_matched", csv_filenames_for_matched)
            
            self.logger.info(f"Auto-workflow: Fuzzy search completed across {len(search_dirs)} directories. Found {matches_found} matches out of {len(selected_files)} files")
            return combined_results
            
        except Exception as e:
            self.logger.error(f"Error during automatic fuzzy search: {str(e)}")
            return None
    
    def auto_perform_file_picker_workflow(self, file_paths):
        """Automatically create links for directly selected files."""
        if not file_paths:
            return
        
        # Show progress dialog
        progress_dialog = ft.AlertDialog(
            title=ft.Text("Processing Files"),
            content=ft.Column([
                ft.Text("Creating links..."),
                ft.ProgressRing()
            ], tight=True, height=100),
            modal=True
        )
        
        self.page.overlay.append(progress_dialog)
        progress_dialog.open = True
        self.page.update()
        
        try:
            # Create symbolic links
            self.logger.info(f"Auto-workflow: Creating symbolic links for {len(file_paths)} files")
            temp_files, temp_file_info, temp_dir = self.copy_files_to_temp_directory(file_paths)
            
            # Update selected_file_paths to point to temp files so derivatives are created there
            if temp_files:
                self.page.session.set("selected_file_paths", temp_files)
            
            if temp_files:
                # Close progress dialog
                progress_dialog.open = False
                self.page.update()
                
                # Show result
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Successfully created links for {len(file_paths)} files. Use the Derivatives menu to generate thumbnails and derivatives."),
                    bgcolor=ft.Colors.GREEN_400
                )
            else:
                # Close progress dialog
                progress_dialog.open = False
                self.page.update()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Failed to create symbolic links for selected files"),
                    bgcolor=ft.Colors.RED_400
                )
            
            self.page.snack_bar.open = True
            self.page.update()
            
            # Refresh to show updated status
            self.page.go("/file_selector")
            
        except Exception as ex:
            # Close progress dialog on error
            progress_dialog.open = False
            self.page.update()
            
            self.logger.error(f"Error during file picker automatic workflow: {str(ex)}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error during automatic processing: {str(ex)}"),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def do_fuzzy_search(self, e):
        """Perform fuzzy search using utils.perform_fuzzy_search_batch."""
        search_dir = self.page.session.get("search_directory")
        selected_files = self.page.session.get("selected_file_paths") or []
        
        if not search_dir or not selected_files:
            self.logger.error("Search directory or files not available")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Please select both a search directory and ensure files are extracted from CSV"),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        self.logger.info(f"Starting fuzzy search in {search_dir} for {len(selected_files)} files")
        
        # Get theme colors
        colors = self.get_theme_colors()
        
        # Create progress display
        progress_text = ft.Text("Initializing search...", size=14, color=colors['primary_text'])
        progress_bar = ft.ProgressBar(width=400, value=0)
        cancel_button = ft.ElevatedButton(
            "Cancel Search",
            icon=ft.Icons.CANCEL,
            on_click=lambda _: self.page.session.set("cancel_search", True),
            bgcolor=ft.Colors.RED_400
        )
        
        # Create progress dialog
        progress_dialog = ft.AlertDialog(
            title=ft.Text("Fuzzy Search in Progress"),
            content=ft.Column([
                progress_text,
                progress_bar,
                ft.Container(height=10),
                cancel_button
            ], tight=True, height=150),
            modal=True
        )
        
        # Show dialog
        self.page.overlay.append(progress_dialog)
        progress_dialog.open = True
        self.page.update()
        
        # Reset cancel flag
        self.page.session.set("cancel_search", False)
        
        # Define progress callback
        def update_progress(progress):
            """Update progress bar and text"""
            try:
                files_done = int(progress * len(selected_files))
                progress_text.value = f"Search Progress: {files_done}/{len(selected_files)} files processed ({progress:.0%})"
                progress_bar.value = progress
                self.logger.info(f"Progress update: {files_done}/{len(selected_files)} files ({progress:.0%})")
                self.page.update()
            except Exception as e:
                self.logger.error(f"Error updating progress: {str(e)}")
        
        # Define cancel check
        def check_cancel():
            """Check if search should be cancelled"""
            cancel = self.page.session.get("cancel_search")
            return cancel if cancel is not None else False
        
        try:
            # Get transcript info from session
            transcript_info = self.page.session.get("transcript_info") or {}
            
            # Perform the fuzzy search with progress tracking and cancellation support
            results = utils.perform_fuzzy_search_batch(
                search_dir, 
                selected_files,
                threshold=90,
                progress_callback=update_progress,
                cancel_check=check_cancel,
                transcript_info=transcript_info  # Pass transcript info
            )
            
            # Close progress dialog
            progress_dialog.open = False
            self.page.update()
            
            # If search was cancelled
            if results is None:
                self.logger.info("Fuzzy search was cancelled by user")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Search cancelled by user"),
                    bgcolor=ft.Colors.ORANGE_400
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Process results and update session with matched paths
            matched_paths = []
            matched_ratios = []
            unmatched_filenames = []
            transcript_csv_files = []  # Track transcript CSV files
            matches_found = 0
            original_count = len(selected_files)
            
            for filename in selected_files:
                result_tuple = results.get(filename, (None, 0))
                
                # Check if this is a transcript result (3-tuple) or normal result (2-tuple)
                if len(result_tuple) == 3:
                    # Transcript result: (media_path, ratio, transcript_csv_path)
                    match_path, ratio, transcript_csv = result_tuple
                    
                    # Store transcript CSV if found
                    if transcript_csv:
                        transcript_csv_files.append(transcript_csv)
                        self.logger.info(f"Found transcript CSV: {transcript_csv}")
                else:
                    # Normal result: (match_path, ratio)
                    match_path, ratio = result_tuple
                
                if match_path and ratio >= 90:
                    # Store the original matched path (don't sanitize here)
                    matched_paths.append(match_path)
                    matched_ratios.append(ratio)
                    matches_found += 1
                    self.logger.info(f"Found match for '{filename}': {match_path} ({ratio}% match)")
                else:
                    matched_paths.append(None)
                    # Store unmatched filename with best match info (filename, best_path, best_ratio)
                    unmatched_filenames.append({
                        'filename': filename,
                        'best_path': match_path,
                        'best_ratio': ratio
                    })
                    # Log unmatched files with severity based on fuzzy score
                    if ratio == 0:
                        self.logger.error(f"No match found for '{filename}' (0% match)")
                    elif ratio < 50:
                        self.logger.error(f"No match found for '{filename}' ({ratio}% match - very low)")
                    elif ratio < 90:
                        self.logger.warning(f"No match found for '{filename}' ({ratio}% match - below 90% threshold)")
                    else:
                        self.logger.info(f"No match found for '{filename}' meeting 90% threshold")
            
            # Store transcript CSV files in session for later use
            if transcript_csv_files:
                self.page.session.set("transcript_csv_files", transcript_csv_files)
                self.logger.info(f"Stored {len(transcript_csv_files)} transcript CSV files for later processing")
            
            # Store search statistics for UI display
            self.page.session.set("original_filename_count", original_count)
            self.page.session.set("matched_file_count", matches_found)
            self.page.session.set("matched_ratios", matched_ratios)
            self.page.session.set("unmatched_filenames", unmatched_filenames)
            self.page.session.set("search_completed", True)
            
            # Update session with matched paths (replaces the original filenames)
            self.page.session.set("selected_file_paths", [p for p in matched_paths if p is not None])
            
            # Log completion
            completion_msg = f"Fuzzy search completed. Found {matches_found} matches out of {len(selected_files)} files"
            if transcript_csv_files:
                completion_msg += f" (including {len(transcript_csv_files)} transcript CSV files)"
            self.logger.info(completion_msg)
            
            # Show success message
            success_msg = f"Search Complete: Found {matches_found} matches out of {len(selected_files)} files"
            if transcript_csv_files:
                success_msg += f" (+ {len(transcript_csv_files)} transcript CSVs)"
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(success_msg),
                bgcolor=ft.Colors.GREEN_400
            )
            self.page.snack_bar.open = True
            
            # Refresh the display to show updated results
            self.update_csv_display()
            
        except Exception as e:
            # Close progress dialog on error
            progress_dialog.open = False
            self.page.update()
            
            error_msg = f"Error during search: {str(e)}"
            self.logger.error(f"Error during fuzzy search: {str(e)}")
            
            # Show error in snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(error_msg),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def on_copy_csv_matches_to_temp(self, e):
        """Handle creating symbolic links for CSV matched files in temporary directory."""
        matched_files = self.page.session.get("selected_file_paths") or []
        transcript_csv_files = self.page.session.get("transcript_csv_files") or []
        
        # Filter to only include matched files (absolute paths)
        full_path_files = [f for f in matched_files if f and os.path.isabs(f) and os.path.exists(f)]
        
        if not full_path_files and not transcript_csv_files:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("No matched files found to link"),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        self.logger.info(f"Creating symbolic links for {len(full_path_files)} matched files in temporary directory...")
        temp_files, temp_file_info, temp_dir = self.copy_files_to_temp_directory(full_path_files)
        
        # Create links for transcript CSV files in separate TRANSCRIPTS directory
        if transcript_csv_files:
            self.logger.info(f"Creating symbolic links for {len(transcript_csv_files)} transcript CSV files...")
            transcript_temp_files = self.copy_transcript_files_to_temp_directory(transcript_csv_files, temp_dir)
            self.logger.info(f"Created links for {len(transcript_temp_files)} transcript CSV files in {temp_dir}/TRANSCRIPTS")
        
        # Update selected_file_paths to point to temp files so derivatives are created there
        if temp_files:
            self.page.session.set("selected_file_paths", temp_files)
        
        if temp_files or transcript_csv_files:
            success_msg = f"Successfully created {len(temp_files)} symbolic links for matched files"
            if transcript_csv_files:
                success_msg += f" and {len(transcript_csv_files)} transcript CSV files"
            success_msg += " in temporary directory"
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(success_msg),
                bgcolor=ft.Colors.GREEN_400
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            # Refresh the view to show updated button states
            self.update_csv_display()
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Failed to create symbolic links for matched files in temporary directory"),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def render(self) -> ft.Column:
        """
        Render the CSV selector view with 4-step workflow.
        
        Returns:
            ft.Column: The CSV page layout
        """
        self.on_view_enter()
        
        # Get theme colors
        colors = self.get_theme_colors()
        
        # Create file pickers
        self.csv_file_picker = ft.FilePicker(on_result=self.on_csv_file_picker_result)
        self.search_dir_picker = ft.FilePicker(on_result=self.on_search_dir_picker_result)
        self.page.overlay.append(self.csv_file_picker)
        self.page.overlay.append(self.search_dir_picker)
        
        # Initialize containers
        self.file_selection_container = ft.Container(visible=False)
        self.columns_display_container = ft.Container(visible=False)
        self.results_display_container = ft.Container(visible=False)
        self.search_container = ft.Container(visible=False)
        
        # Create main display
        self.csv_file_display = ft.Column([], spacing=10)
        
        # Initial update
        self.update_csv_display()
        
        return ft.Column([
            ft.Row([
                ft.Text(f"File Selector - {self.selector_type}", size=24, weight=ft.FontWeight.BOLD),
                self.create_log_button("Show Logs", ft.Icons.LIST_ALT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=15, color=colors['divider']),
            ft.Text("Process CSV or Excel files step by step", 
                   size=16, color=colors['primary_text']),
            ft.Text("Follow the collapsible sections below to complete your file selection", 
                   size=14, color=colors['secondary_text']),
            ft.Container(height=10),
            self.csv_file_display,
        ], alignment="start", expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
