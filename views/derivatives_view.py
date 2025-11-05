"""
Derivatives View for Manage Digital Ingest Application

This module contains the DerivativesView class for creating file derivatives.
"""

import flet as ft
from views.base_view import BaseView
import os
from subprocess import call
from thumbnail import generate_thumbnail, generate_pdf_thumbnail


class DerivativesView(BaseView):
    """
    Derivatives view class for derivative creation operations.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the derivatives view."""
        super().__init__(page)
        self.log_view = None
        self.processing = False
        self.cancel_processing = False
    
    def create_single_derivative(self, file_path, mode, derivative_type='thumbnail'):
        """
        Create a single derivative for a file based on mode and type.
        
        Args:
            file_path: Path to the source file
            mode: Mode to use ('Alma' or 'CollectionBuilder')
            derivative_type: Type of derivative ('thumbnail' or 'small')
            
        Returns:
            tuple: (success: bool, result: str)
        """
        try:
            # Check for spaces in the file path
            if any(char.isspace() for char in file_path):
                error_msg = f"File path '{file_path}' contains spaces! This should not happen with temp files."
                self.logger.error(error_msg)
                return False, error_msg
            
            # Parse file path components
            dirname, basename = os.path.split(file_path)
            root, ext = os.path.splitext(basename)
            
            # Determine the base temp directory (go up one level from OBJS)
            if dirname.endswith('OBJS'):
                temp_base_dir = os.path.dirname(dirname)
            else:
                temp_base_dir = dirname
            
            self.logger.info(f"Processing file: {file_path}")
            self.logger.info(f"Directory: {dirname}, Basename: {basename}, Root: {root}, Extension: {ext}")
            self.logger.info(f"Temp base directory: {temp_base_dir}")
            
            if mode == 'Alma':
                # Alma mode - create thumbnail with .jpg.clientThumb extension in TN/ directory
                tn_dir = os.path.join(temp_base_dir, 'TN')
                os.makedirs(tn_dir, exist_ok=True)
                derivative_filename = f"{root}.jpg.clientThumb"
                derivative_path = os.path.join(tn_dir, derivative_filename)
                self.logger.info(f"Alma derivative path: {derivative_path}")
                
                # Define options for Alma thumbnails
                options = {
                    'trim': False,
                    'height': 200,
                    'width': 200,
                    'quality': 85,
                    'type': 'thumbnail'
                }
                
                # Process based on file type
                if ext.lower() in ['.tiff', '.tif', '.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    success = generate_thumbnail(file_path, derivative_path, options)
                    if success:
                        self.logger.info(f"Created Alma thumbnail: {derivative_path}")
                        return True, derivative_path
                    else:
                        error_msg = f"Failed to create Alma thumbnail: {derivative_path}"
                        self.logger.error(error_msg)
                        return False, error_msg
                elif ext.lower() == '.pdf':
                    success = generate_pdf_thumbnail(file_path, derivative_path, options)
                    if success:
                        self.logger.info(f"Created Alma PDF thumbnail: {derivative_path}")
                        return True, derivative_path
                    else:
                        error_msg = f"Failed to create PDF thumbnail: {derivative_path}"
                        self.logger.error(error_msg)
                        return False, error_msg
                else:
                    error_msg = f"Unsupported file type for Alma: {ext}"
                    self.logger.error(error_msg)
                    return False, error_msg
            
            elif mode == 'CollectionBuilder':
                # CollectionBuilder mode - create thumbnail or small in respective directories
                if derivative_type == 'thumbnail':
                    tn_dir = os.path.join(temp_base_dir, 'TN')
                    os.makedirs(tn_dir, exist_ok=True)
                    derivative_path = os.path.join(tn_dir, f"{root}_TN.jpg")
                    self.logger.info(f"CollectionBuilder thumbnail path: {derivative_path}")
                    options = {
                        'trim': False,
                        'height': 400,
                        'width': 400,
                        'quality': 85,
                        'type': 'thumbnail'
                    }
                elif derivative_type == 'small':
                    small_dir = os.path.join(temp_base_dir, 'SMALL')
                    os.makedirs(small_dir, exist_ok=True)
                    derivative_path = os.path.join(small_dir, f"{root}_SMALL.jpg")
                    self.logger.info(f"CollectionBuilder small path: {derivative_path}")
                    options = {
                        'trim': False,
                        'height': 800,
                        'width': 800,
                        'quality': 85,
                        'type': 'thumbnail'
                    }
                else:
                    error_msg = f"Unknown derivative type for CollectionBuilder: {derivative_type}"
                    self.logger.error(error_msg)
                    return False, error_msg
                
                # Process based on file type
                if ext.lower() in ['.tiff', '.tif', '.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    success = generate_thumbnail(file_path, derivative_path, options)
                    if success:
                        self.logger.info(f"Created CollectionBuilder {derivative_type}: {derivative_path}")
                        return True, derivative_path
                    else:
                        error_msg = f"Failed to create CollectionBuilder {derivative_type}: {derivative_path}"
                        self.logger.error(error_msg)
                        return False, error_msg
                elif ext.lower() == '.pdf':
                    success = generate_pdf_thumbnail(file_path, derivative_path, options)
                    if success:
                        self.logger.info(f"Created CollectionBuilder {derivative_type} from PDF: {derivative_path}")
                        return True, derivative_path
                    else:
                        error_msg = f"Failed to create PDF {derivative_type}: {derivative_path}"
                        self.logger.error(error_msg)
                        return False, error_msg
                else:
                    error_msg = f"Unsupported file type for CollectionBuilder: {ext}"
                    self.logger.error(error_msg)
                    return False, error_msg
            else:
                error_msg = f"Unsupported mode: {mode}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Exception in create_single_derivative: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def create_derivatives_for_files(self):
        """Process all selected files and create derivatives."""
        colors = self.get_theme_colors()
        
        # Get current settings
        current_mode = self.page.session.get("selected_mode")
        selected_files = self.page.session.get("selected_file_paths") or []
        total_files = len(selected_files)
        
        if not current_mode:
            self.log_view.controls.clear()
            self.log_view.controls.append(ft.Text(
                "❌ No mode selected. Please go to Settings first.",
                size=12,
                color=colors['error']
            ))
            self.page.update()
            return
        
        if not selected_files:
            self.log_view.controls.clear()
            self.log_view.controls.append(ft.Text(
                "❌ No files selected. Please go to File Selector first.",
                size=12,
                color=colors['error']
            ))
            self.page.update()
            return
        
        # Update UI to show processing state
        self.processing = True
        self.cancel_processing = False
        
        # Update button states
        if hasattr(self, 'create_button'):
            self.create_button.disabled = True
        if hasattr(self, 'clear_button'):
            self.clear_button.disabled = True
        if hasattr(self, 'cancel_button'):
            self.cancel_button.visible = True
        
        self.page.update()
        
        # Start processing
        msg = f"Starting derivative creation for {total_files} files in {current_mode} mode"
        self.logger.info(msg)
        self.log_view.controls.clear()
        self.log_view.controls.append(ft.Text(msg, size=12, color=colors['primary_text']))
        
        self.log_view.controls.append(ft.Text(
            f"🔄 Processing {total_files} files in {current_mode} mode...",
            size=12,
            color=colors['primary_text']
        ))
        self.page.update()
        
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for index, file_path in enumerate(selected_files):
            # Check for cancellation
            if self.cancel_processing:
                self.log_view.controls.append(ft.Text(
                    f"⚠️ Processing cancelled by user. Processed {processed_count}/{total_files} files.",
                    size=12,
                    color=colors['error']
                ))
                self.page.update()
                self.logger.info(f"Processing cancelled by user at file {index + 1}/{total_files}")
                break
                
            try:
                display_name = os.path.basename(file_path)
                self.logger.info(f"Processing file {index + 1}/{total_files}: {file_path}")
                
                # Update log
                self.log_view.controls.append(ft.Text(
                    f"🔄 Processing file {index + 1}/{total_files}: {display_name}",
                    size=12,
                    color=colors['primary_text']
                ))
                self.page.update()
                
                # Create derivatives based on mode
                if current_mode == "CollectionBuilder":
                    # Create thumbnail
                    thumbnail_success, thumbnail_result = self.create_single_derivative(
                        file_path, current_mode, 'thumbnail'
                    )
                    
                    # Create small derivative
                    small_success, small_result = self.create_single_derivative(
                        file_path, current_mode, 'small'
                    )
                    
                    # Log results
                    if thumbnail_success and small_success:
                        result_text = f"✅ {display_name} - Created thumbnail and small derivatives"
                        success_count += 1
                        self.logger.info(f"Successfully created derivatives for {file_path}")
                    else:
                        result_text = f"❌ {display_name} - Failed to create derivatives"
                        if not thumbnail_success:
                            self.logger.error(f"Thumbnail failed: {thumbnail_result}")
                        if not small_success:
                            self.logger.error(f"Small derivative failed: {small_result}")
                        error_count += 1
                        
                elif current_mode == "Alma":
                    # Create thumbnail only for Alma
                    thumbnail_success, thumbnail_result = self.create_single_derivative(
                        file_path, current_mode, 'thumbnail'
                    )
                    
                    if thumbnail_success:
                        result_text = f"✅ {display_name} - Created thumbnail derivative"
                        success_count += 1
                        self.logger.info(f"Successfully created thumbnail for {file_path}")
                    else:
                        result_text = f"❌ {display_name} - Failed to create thumbnail"
                        self.logger.error(f"Thumbnail failed: {thumbnail_result}")
                        error_count += 1
                else:
                    result_text = f"❌ {display_name} - Unsupported mode: {current_mode}"
                    error_count += 1
                    self.logger.error(f"Unsupported mode {current_mode} for file {file_path}")
                
                # Add result to UI
                self.log_view.controls.append(
                    ft.Text(result_text, size=12, color=colors['primary_text'])
                )
                self.page.update()
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                error_text = f"❌ {display_name} - Error: {str(e)}"
                self.log_view.controls.append(
                    ft.Text(error_text, size=12, color=colors['error'])
                )
                self.logger.error(f"Exception processing {file_path}: {str(e)}")
                self.page.update()
            
            # Update progress
            self.log_view.controls.append(
                ft.Text(
                    f"Progress: {index + 1}/{total_files} files ({(index + 1)/total_files:.0%})",
                    size=12,
                    color=colors['primary_text']
                )
            )
            self.page.update()
        
        # Final summary
        if not self.cancel_processing:
            summary_text = f"\n✅ Processing complete!\nTotal: {total_files} | Success: {success_count} | Errors: {error_count}"
        else:
            summary_text = f"\n⚠️ Processing cancelled!\nProcessed: {processed_count}/{total_files} | Success: {success_count} | Errors: {error_count}"
        
        self.log_view.controls.append(
            ft.Text(summary_text, size=14, weight=ft.FontWeight.BOLD, color=colors['primary_text'])
        )
        self.page.update()
        self.logger.info(summary_text)
        
        # Reset processing state
        self.processing = False
        self.cancel_processing = False
        
        # Update button states back to normal
        if hasattr(self, 'create_button'):
            self.create_button.disabled = False
        if hasattr(self, 'clear_button'):
            self.clear_button.disabled = False
        if hasattr(self, 'cancel_button'):
            self.cancel_button.visible = False
        
        self.page.update()
        
        self.logger.info("Processing completed, buttons reset")
    
    def interrupt_processing(self, e):
        """Interrupt the current processing operation."""
        if self.processing:
            self.cancel_processing = True
            self.logger.info("Processing interruption requested by user")
            
            # Update UI to show cancellation in progress
            colors = self.get_theme_colors()
            self.log_view.controls.append(ft.Text(
                "🛑 Cancellation requested... stopping after current file.",
                size=12,
                color=colors['error']
            ))
            self.page.update()
    
    def render(self) -> ft.Column:
        """
        Render the derivatives view content.
        
        Returns:
            ft.Column: The derivatives page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Get current mode and files from session
        current_mode = self.page.session.get("selected_mode")
        selected_files = self.page.session.get("selected_file_paths") or []
        total_files = len(selected_files)
        
        # Prepare status information controls
        status_info_controls = [
            ft.Text(f"Current Mode: {current_mode or 'None selected'}", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['container_text']),
            ft.Text(f"Selected Files: {total_files}", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['container_text'])
        ]
        
        status_info_controls.extend([
            ft.Container(height=5),
            ft.Text("Derivative Types:", size=14, weight=ft.FontWeight.BOLD, color=colors['container_text']),
            ft.Text("• CollectionBuilder: _TN.jpg (400x400) + _SMALL.jpg (800x800)", 
                   size=12, color=colors['container_text']),
            ft.Text("• Alma: _TN.jpg (200x200) thumbnail", 
                   size=12, color=colors['container_text'])
        ])
        
        # Create log view
        self.log_view = ft.ListView(
            spacing=2,
            padding=5,
            height=300,
            expand=True,
            auto_scroll=True
        )
        
        # Add initial message
        if not current_mode:
            self.log_view.controls.append(
                ft.Text("⚠️ Please select a mode in Settings before creating derivatives.",
                       size=12, color=colors['secondary_text'])
            )
        elif total_files == 0:
            self.log_view.controls.append(
                ft.Text("⚠️ Please select files in File Selector before creating derivatives.",
                       size=12, color=colors['secondary_text'])
            )
        else:
            self.log_view.controls.append(
                ft.Text(f"Ready to create derivatives for {total_files} files in {current_mode} mode.",
                       size=12, color=colors['primary_text'])
            )
        
        def on_create_derivatives_click(e):
            """Handle the create derivatives button click."""
            self.create_derivatives_for_files()
        
        def on_interrupt_click(e):
            """Handle the interrupt/cancel button click."""
            self.interrupt_processing(e)
        
        def on_clear_results_click(e):
            """Clear the results log."""
            self.log_view.controls.clear()
            self.log_view.controls.append(
                ft.Text("Log cleared. Ready to process files.",
                       size=12, color=colors['secondary_text'])
            )
            self.page.update()
            self.logger.info("Cleared derivatives log")
        
        # Create buttons with references that can be updated
        create_button = ft.ElevatedButton(
            "Create Derivatives",
            icon=ft.Icons.AUTO_FIX_HIGH,
            on_click=on_create_derivatives_click,
            disabled=(not current_mode or total_files == 0)
        )
        
        clear_button = ft.ElevatedButton(
            "Clear Results",
            icon=ft.Icons.CLEAR,
            on_click=on_clear_results_click
        )
        
        # Store button references for dynamic updates
        self.create_button = create_button
        self.clear_button = clear_button
        
        start_button = ft.Row([
            create_button,
            clear_button
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
        # Create cancel button (always present, visibility controlled dynamically)
        self.cancel_button = ft.Container(
            content=ft.Column([
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "🛑 Cancel Processing",
                        icon=ft.Icons.CANCEL,
                        on_click=on_interrupt_click,
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=0),
            visible=self.processing  # Initially hidden unless already processing
        )
        
        # Build the layout controls list
        layout_controls = [
            *self.create_page_header("Derivatives Creation"),
            
            # Status information
            ft.Container(
                content=ft.Column(status_info_controls, spacing=2),
                padding=ft.padding.all(10),
                border=ft.border.all(1, colors['border']),
                border_radius=10,
                bgcolor=colors['container_bg'],
                margin=ft.margin.symmetric(vertical=5)
            ),
            
            # Start button at top
            start_button,
            
            ft.Container(height=5),
            
            # Log view
            ft.Text("Processing Log:", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=5),
            ft.Container(
                content=self.log_view,
                border=ft.border.all(1, colors['border']),
                border_radius=5,
                padding=2,
                expand=True
            ),
            
            # Cancel button below log (only visible during processing)
            self.cancel_button
        ]
        
        # Create the UI layout
        return ft.Column(layout_controls, alignment="start", expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)
