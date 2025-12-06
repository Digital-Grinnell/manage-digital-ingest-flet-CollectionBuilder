"""
Storage view for Azure storage operations.
"""
import os
import json
import flet as ft
from azure.storage.blob import BlobServiceClient

import utils
from .base_view import BaseView


class StorageView(BaseView):
    
    def __init__(self, page: ft.Page):
        """Initialize the storage view."""
        super().__init__(page)
        self.upload_progress = ft.ProgressBar(width=400, visible=False)
        self.upload_status = ft.Text("", visible=False)
    
    def get_azure_base_url(self):
        """Get the Azure base URL from persistent settings or use mode-specific default."""
        try:
            # Check the current mode
            current_mode = self.page.session.get("selected_mode")
            
            # If in CollectionBuilder mode, use the CollectionBuilder Azure URL
            if current_mode == "CollectionBuilder":
                return "https://collectionbuilder.blob.core.windows.net"
            
            # Otherwise, get from persistent settings
            with open("_data/persistent.json", "r", encoding="utf-8") as f:
                persistent_data = json.load(f)
            return persistent_data.get("azure_base_url", "")
        except Exception as e:
            self.logger.error(f"Failed to read Azure base URL: {e}")
            return ""
    
    def copy_to_clipboard(self, e, text):
        """Copy text to clipboard."""
        self.page.set_clipboard(text)
        self.show_snack("✓ Copied to clipboard", is_error=False)
    
    def close_dialog(self, dialog):
        """Close the dialog."""
        dialog.open = False
        self.page.update()
    
    def upload_files_to_azure(self, e):
        """Upload files from temporary /OBJS directory to Azure Blob storage."""
        try:
            # Get the Azure base URL
            azure_base_url = self.get_azure_base_url()
            if not azure_base_url:
                self.upload_status.value = "❌ Azure base URL not configured"
                self.upload_status.color = ft.Colors.RED
                self.upload_status.visible = True
                self.page.update()
                return
            
            # Get the temp directory from session
            temp_dir = self.page.session.get("temp_directory")
            if not temp_dir:
                self.upload_status.value = "❌ No temporary directory found. Please select files first."
                self.upload_status.color = ft.Colors.RED
                self.upload_status.visible = True
                self.page.update()
                return
            
            # Check for OBJS directory
            objs_dir = os.path.join(temp_dir, "OBJS")
            if not os.path.exists(objs_dir):
                self.upload_status.value = f"❌ No OBJS directory found in {temp_dir}"
                self.upload_status.color = ft.Colors.RED
                self.upload_status.visible = True
                self.page.update()
                return
            
            # Check for SMALL and TN directories (optional)
            small_dir = os.path.join(temp_dir, "SMALL")
            tn_dir = os.path.join(temp_dir, "TN")
            
            # Show progress bar
            self.upload_progress.visible = True
            self.upload_status.value = "🔄 Initializing Azure connection..."
            self.upload_status.color = ft.Colors.BLUE
            self.upload_status.visible = True
            self.page.update()
            
            # Initialize Azure Blob Service Client using connection string
            try:
                # Get the selected storage from session
                selected_storage = self.page.session.get("selected_storage")
                
                # Determine which connection string to use based on selected storage
                if selected_storage == "collectionbuilder":
                    connection_string = os.getenv("AZURE_CB_STORAGE_CONNECTION_STRING")
                    storage_name = "CollectionBuilder"
                else:  # dgobjects or other
                    connection_string = os.getenv("AZURE_DG_STORAGE_CONNECTION_STRING")
                    storage_name = "DG Objects"
                
                if not connection_string:
                    env_var_name = "AZURE_CB_STORAGE_CONNECTION_STRING" if selected_storage == "collectionbuilder" else "AZURE_DG_STORAGE_CONNECTION_STRING"
                    self.upload_status.value = f"❌ Azure Storage connection string not configured for {storage_name}"
                    self.upload_status.value += f"\n\n💡 Please set {env_var_name} in .env file"
                    self.upload_status.color = ft.Colors.RED
                    self.upload_progress.visible = False
                    self.logger.error(f"{env_var_name} environment variable not set")
                    self.page.update()
                    return
                
                # Create BlobServiceClient from connection string
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                
            except Exception as e:
                error_msg = str(e)
                self.upload_status.value = f"❌ Failed to connect to Azure Storage"
                self.upload_status.value += f"\n\nError: {error_msg}"
                env_var_name = "AZURE_CB_STORAGE_CONNECTION_STRING" if selected_storage == "collectionbuilder" else "AZURE_DG_STORAGE_CONNECTION_STRING"
                self.upload_status.value += f"\n\n💡 Please check your {env_var_name} in .env file"
                self.upload_status.color = ft.Colors.RED
                self.upload_progress.visible = False
                self.logger.error(f"Azure Storage connection failed: {error_msg}")
                self.page.update()
                return
            
            # Get transcript CSV files from session to exclude from upload
            transcript_csv_files = self.page.session.get("transcript_csv_files") or []
            transcript_csv_basenames = {os.path.basename(f) for f in transcript_csv_files}
            
            # Get list of files to upload from OBJS, SMALL, and TN directories
            files_to_upload = []
            skipped_transcripts = []
            
            # Add files from OBJS directory (excluding transcript CSVs)
            for root, dirs, files in os.walk(objs_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip transcript CSV files - they'll be handled by deployment script
                    if file in transcript_csv_basenames:
                        skipped_transcripts.append(file_path)
                        self.logger.info(f"Skipping transcript CSV from upload: {file}")
                        continue
                    
                    # Create relative path for blob name
                    relative_path = os.path.relpath(file_path, objs_dir)
                    files_to_upload.append((file_path, relative_path))
            
            # Add files from SMALL directory if it exists
            if os.path.exists(small_dir):
                for root, dirs, files in os.walk(small_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Create relative path for blob name, marking as from SMALL
                        relative_path = os.path.relpath(file_path, small_dir)
                        files_to_upload.append((file_path, relative_path))
            
            # Add files from TN directory if it exists
            if os.path.exists(tn_dir):
                for root, dirs, files in os.walk(tn_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Create relative path for blob name, marking as from TN
                        relative_path = os.path.relpath(file_path, tn_dir)
                        files_to_upload.append((file_path, relative_path))
            
            if not files_to_upload:
                self.upload_status.value = "⚠️ No files found in OBJS directory"
                self.upload_status.color = ft.Colors.ORANGE
                self.upload_progress.visible = False
                self.page.update()
                return
            
            # Upload files
            uploaded_count = 0
            skipped_count = 0
            failed_count = 0
            total_files = len(files_to_upload)
            
            # Get selected mode and collection for CollectionBuilder path construction
            selected_mode = self.page.session.get("selected_mode")
            selected_collection = self.page.session.get("selected_collection")
            
            for i, (local_path, blob_name) in enumerate(files_to_upload):
                try:
                    self.upload_status.value = f"🔄 Uploading {blob_name} ({i+1}/{total_files})"
                    self.upload_progress.value = i / total_files
                    self.page.update()
                    
                    # Determine container based on file path
                    if "thumbs/" in blob_name or "/TN/" in local_path:
                        container_name = "thumbs"
                        # Remove 'thumbs/' prefix if present
                        blob_path = blob_name.replace("thumbs/", "")
                    elif "smalls/" in blob_name or "/SMALL/" in local_path:
                        container_name = "smalls"
                        # Remove 'smalls/' prefix if present
                        blob_path = blob_name.replace("smalls/", "")
                    else:
                        container_name = "objs"
                        # Remove 'objs/' prefix if present
                        blob_path = blob_name.replace("objs/", "")
                    
                    # For CollectionBuilder mode with collectionbuilder storage, prepend collection name to path
                    if selected_mode == "CollectionBuilder" and selected_storage == "collectionbuilder" and selected_collection:
                        blob_path = f"{selected_collection}/{blob_path}"
                    
                    # Create blob client
                    blob_client = blob_service_client.get_blob_client(
                        container=container_name, 
                        blob=blob_path
                    )
                    
                    # Check if blob already exists
                    if blob_client.exists():
                        self.logger.info(f"Blob '{blob_path}' already exists in container '{container_name}'. Skipping.")
                        skipped_count += 1
                    else:
                        # Upload the file
                        with open(local_path, "rb") as data:
                            blob_client.upload_blob(data)
                        self.logger.info(f"Successfully uploaded '{blob_path}' to container '{container_name}'")
                        uploaded_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to upload {blob_name}: {e}")
                    failed_count += 1
                    continue
            
            # Update final status
            self.upload_progress.value = 1.0
            
            # Build detailed status message
            status_parts = []
            if uploaded_count > 0:
                status_parts.append(f"✅ Uploaded: {uploaded_count}")
            if skipped_count > 0:
                status_parts.append(f"⏭️ Skipped: {skipped_count}")
            if failed_count > 0:
                status_parts.append(f"❌ Failed: {failed_count}")
            if len(skipped_transcripts) > 0:
                status_parts.append(f"📝 Transcripts excluded: {len(skipped_transcripts)}")
            
            total_processed = uploaded_count + skipped_count + failed_count
            self.upload_status.value = f"{' | '.join(status_parts)} (Total: {total_processed}/{total_files})"
            
            if len(skipped_transcripts) > 0:
                self.upload_status.value += f"\n💡 Transcript CSVs will be copied by deployment script to _data/transcripts/"
            
            # Set color based on results
            if failed_count > 0:
                self.upload_status.color = ft.Colors.RED
            elif uploaded_count == total_files:
                self.upload_status.color = ft.Colors.GREEN
            elif skipped_count > 0 and failed_count == 0:
                self.upload_status.color = ft.Colors.BLUE
            else:
                self.upload_status.color = ft.Colors.ORANGE
            
            self.page.update()
            
        except Exception as e:
            self.logger.error(f"Upload process failed: {e}")
            self.upload_status.value = f"❌ Upload failed: {str(e)}"
            self.upload_status.color = ft.Colors.RED
            self.upload_progress.visible = False
            self.page.update()
    
    def render(self) -> ft.Column:
        """
        Render the storage page content based on selected mode.
        
        Returns:
            ft.Column: The storage page content
        """
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # CollectionBuilder mode - show Azure upload controls
        azure_url = self.get_azure_base_url()
        
        upload_button = ft.ElevatedButton(
            text="Upload Files to Azure",
            icon=ft.Icons.CLOUD_UPLOAD,
            on_click=self.upload_files_to_azure,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600
            )
        )
        
        upload_controls = ft.Column(
            controls=[
                ft.Text(
                    "Azure Storage Upload",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=colors['primary_text']
                    ),
                    ft.Divider(height=1, color=colors['divider']),
                    ft.Text(
                        f"Azure Base URL: {azure_url or 'Not configured'}",
                        size=14,
                        color=colors['secondary_text']
                    ),
                    ft.Text(
                        "This will upload files from the temporary /OBJS directory to Azure Blob storage.",
                        size=14,
                        color=colors['secondary_text']
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "📋 Prerequisites:",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=colors['primary_text']
                            ),
                            ft.Text(
                                "• Files must be selected first (via File Selector page)",
                                size=12,
                                color=colors['secondary_text']
                            ),
                            ft.Text(
                                "• Azure Storage connection string must be configured in .env file",
                                size=12,
                                color=colors['secondary_text']
                            ),
                            ft.Text(
                                "  AZURE_STORAGE_CONNECTION_STRING=\"...\"",
                                size=11,
                                color=colors['code_text'],
                                font_family="monospace"
                            ),
                        ], spacing=4),
                        bgcolor=colors['markdown_bg'],
                        border=ft.border.all(1, colors['border']),
                        border_radius=4,
                        padding=10,
                        margin=ft.margin.only(top=10, bottom=10)
                    ),
                    ft.Container(
                        content=upload_button,
                        margin=ft.margin.only(top=20, bottom=10)
                    ),
                    self.upload_progress,
                    self.upload_status
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START
            )
        
        return ft.Column(
            controls=[
                *self.create_page_header("Storage", include_log_button=True),
                ft.Container(
                        content=upload_controls,
                        bgcolor=colors['container_bg'],
                        border=ft.border.all(1, colors['border']),
                        border_radius=8,
                        padding=20,
                        margin=ft.margin.only(top=10)
                    )
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            )