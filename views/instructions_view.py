"""
Instructions View for Manage Digital Ingest Application

This module contains the InstructionsView class for displaying follow-up instructions
and scripts based on the current mode.
"""

import flet as ft
from views.base_view import BaseView
import os
import utils


class InstructionsView(BaseView):
    """
    Instructions view class for displaying mode-specific instructions and scripts.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the instructions view."""
        super().__init__(page)
        self.profile_id_input = None
        self.import_id_input = None
    
    def generate_upload_script(self, e):
        """Generate Alma S3 upload script and display it with copy buttons."""
        try:
            # Get the temp directory from session
            temp_dir = self.page.session.get("temp_directory")
            if not temp_dir:
                self.show_snack("No temporary directory found. Please select files first.", is_error=True)
                return
            
            # Get the temp CSV filename from session
            temp_csv_filename = self.page.session.get("temp_csv_filename")
            
            # Get profile-id and import-id from input fields
            profile_id = self.profile_id_input.value.strip() if self.profile_id_input and self.profile_id_input.value else ""
            import_id = self.import_id_input.value.strip() if self.import_id_input and self.import_id_input.value else ""
            
            # Generate the script
            script_content = utils.generate_alma_s3_script(temp_dir, temp_csv_filename)
            
            # Replace placeholders with actual values if provided
            if profile_id and import_id:
                script_content = script_content.replace("<profile-id>", profile_id)
                script_content = script_content.replace("<import-id>", import_id)
                self.logger.info(f"Replaced placeholders with profile-id: {profile_id}, import-id: {import_id}")
            
            # Save script to temp directory
            script_path = os.path.join(temp_dir, "upload_to_alma.sh")
            try:
                with open(script_path, "w") as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)  # Make executable
                self.logger.info(f"Generated upload script: {script_path}")
            except Exception as ex:
                self.logger.error(f"Failed to save script: {ex}")
                self.show_snack(f"Failed to save script: {ex}", is_error=True)
                return
            
            # Parse script into commands (lines starting with 'aws') and their preceding comments
            lines = script_content.split('\n')
            commands = []
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('aws '):
                    # Look for the preceding comment line (starts with #)
                    comment = ""
                    if i > 0:
                        prev_line = lines[i - 1].strip()
                        if prev_line.startswith('#') and not prev_line.startswith('#!/'):
                            # Remove the leading # and whitespace
                            comment = prev_line.lstrip('#').strip()
                    commands.append((comment, stripped))
            
            # Create display with copy buttons
            colors = self.get_theme_colors()
            
            command_controls = []
            for idx, (comment, cmd) in enumerate(commands, 1):
                # Add comment text if available
                controls_list = []
                if comment:
                    # Determine comment color: red for last command (optional cleanup), green for others
                    comment_color = ft.Colors.RED_300 if idx == len(commands) else ft.Colors.GREEN_300
                    
                    controls_list.append(
                        ft.Text(
                            comment,
                            size=12,
                            color=comment_color,
                            weight=ft.FontWeight.W_500,
                            italic=True
                        )
                    )
                
                # Add the command with copy button
                controls_list.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                cmd,
                                size=11,
                                font_family="Courier New",
                                color=ft.Colors.GREEN_300,  # Lighter text for better contrast
                                selectable=True
                            ),
                            expand=True,
                            padding=10,
                            bgcolor=ft.Colors.GREY_900,  # Darker background for better contrast
                            border_radius=4,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            tooltip=f"Copy command {idx}",
                            on_click=lambda e, command=cmd: self.copy_to_clipboard(e, command)
                        )
                    ], spacing=5)
                )
                
                command_controls.append(
                    ft.Container(
                        content=ft.Column(controls_list, spacing=5),
                        margin=ft.margin.only(bottom=15)
                    )
                )
            
            # Create dialog to show the script
            dialog = ft.AlertDialog(
                title=ft.Text("Alma S3 Upload Script Generated", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"Script saved to: {script_path}",
                            size=12,
                            color=ft.Colors.GREEN_700,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Text(
                            "AWS Commands:",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Text(
                            "Click the copy button to copy each command to clipboard",
                            size=11,
                            italic=True,
                            color=colors['secondary_text']
                        ),
                        ft.Container(height=10),
                        ft.Column(
                            command_controls,
                            scroll=ft.ScrollMode.ALWAYS,
                            height=450
                        ),
                    ], spacing=5),
                    width=700,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            
        except Exception as ex:
            self.logger.error(f"Error generating upload script: {ex}")
            self.show_snack(f"Error: {ex}", is_error=True)
    
    def copy_to_clipboard(self, e, text):
        """Copy text to clipboard."""
        self.page.set_clipboard(text)
        self.show_snack("✓ Copied to clipboard", is_error=False)
    
    def close_dialog(self, dialog):
        """Close the dialog."""
        dialog.open = False
        self.page.update()
    
    def get_alma_instructions(self) -> list:
        """
        Get instructions for Alma mode.
        
        Returns:
            list: List of instruction controls
        """
        colors = self.get_theme_colors()
        
        # Create input fields for profile-id and import-id
        self.profile_id_input = ft.TextField(
            value="6496776180004641",
            hint_text="e.g., 12345",
            width=200,
            dense=True,
            border_color=ft.Colors.GREEN_700,
        )
        
        self.import_id_input = ft.TextField(
            hint_text="e.g., 67890",
            width=200,
            dense=True,
            border_color=ft.Colors.GREEN_700,
        )
        
        instructions = [
            ft.Text("Alma Workflow Instructions", 
                   size=20, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=10),
            
            # Add button for generating upload script with input fields
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Alma AWS S3 Upload",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=colors['primary_text']
                    ),
                    ft.Text(
                        "Generate a bash script to upload files to Alma's AWS S3 storage",
                        size=13,
                        color=colors['secondary_text']
                    ),
                    ft.Container(height=10),
                    # Input fields for profile-id and import-id
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Profile ID:", size=12, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                                self.profile_id_input,
                            ], spacing=3),
                            expand=1,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Import ID:", size=12, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                                self.import_id_input,
                            ], spacing=3),
                            expand=1,
                        ),
                    ], spacing=10),
                    ft.Text(
                        "💡 Leave blank to use placeholders in the script",
                        size=11,
                        italic=True,
                        color=colors['secondary_text']
                    ),
                    ft.Container(
                        content=ft.ElevatedButton(
                            text="Generate Upload Script",
                            icon=ft.Icons.TERMINAL,
                            on_click=self.generate_upload_script,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.GREEN_700
                            )
                        ),
                        margin=ft.margin.only(top=10, bottom=5)
                    ),
                ], spacing=5),
                padding=ft.padding.all(15),
                border=ft.border.all(2, ft.Colors.GREEN_700),
                border_radius=8,
                bgcolor=colors['markdown_bg'],
                margin=ft.margin.only(bottom=15)
            ),
        ]
        
        # Read and display the alma_aws_s3.md file
        alma_md_path = os.path.join("_data", "alma_aws_s3.md")
        if os.path.exists(alma_md_path):
            try:
                md_content = utils.read_markdown(alma_md_path)
                
                # Add a Markdown control to display the file content
                instructions.append(
                    ft.Markdown(
                        md_content,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        on_tap_link=lambda e: self.page.launch_url(e.data),
                        md_style_sheet=self.get_markdown_style()
                    )
                )
            except Exception as e:
                self.logger.error(f"Failed to read alma_aws_s3.md: {e}")
                instructions.append(
                    ft.Text(f"Error loading AWS S3 instructions: {e}", 
                           size=12, color=ft.Colors.RED_600)
                )
        else:
            instructions.append(
                ft.Text("AWS S3 instructions file not found.", 
                       size=12, color=ft.Colors.ORANGE_600)
            )
        
        return instructions
    
    def get_collectionbuilder_instructions(self) -> list:
        """
        Get instructions for CollectionBuilder mode.
        
        Returns:
            list: List of instruction controls
        """
        colors = self.get_theme_colors()
        
        return [
            ft.Text("CollectionBuilder Workflow Instructions", 
                   size=20, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=10),
            
            ft.Text("1. Organize Derivative Files", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Text("• TN/ directory contains thumbnails (400x400 pixels)", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• SMALL/ directory contains small images (800x800 pixels)", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Both use _TN.jpg and _SMALL.jpg suffixes respectively", 
                   size=14, color=colors['secondary_text']),
            ft.Container(height=10),
            
            ft.Text("2. Upload to Repository", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Text("• Upload TN/ directory to /objects/thumbnails/", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Upload SMALL/ directory to /objects/small/", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Original files go to /objects/ directory", 
                   size=14, color=colors['secondary_text']),
            ft.Container(height=10),
            
            ft.Text("3. Update Metadata CSV", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Text("• Add filenames to the 'filename' column", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Ensure objectid values match your filenames", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Add format, title, and other required metadata", 
                   size=14, color=colors['secondary_text']),
            ft.Container(height=10),
            
            ft.Text("4. Build and Deploy", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Text("• Run 'rake generate_derivatives' if needed", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Run 'rake deploy' to build and publish", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• Verify site displays correctly", 
                   size=14, color=colors['secondary_text']),
        ]
    
    def get_no_mode_instructions(self) -> list:
        """
        Get instructions when no mode is selected.
        
        Returns:
            list: List of instruction controls
        """
        colors = self.get_theme_colors()
        
        return [
            ft.Text("No Mode Selected", 
                   size=20, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=10),
            ft.Text("Please select a mode in the Settings page to view mode-specific instructions.", 
                   size=14, color=colors['secondary_text']),
            ft.Container(height=10),
            ft.Text("Available Modes:", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Text("• Alma - For Alma Digital Repository workflows", 
                   size=14, color=colors['secondary_text']),
            ft.Text("• CollectionBuilder - For CollectionBuilder static site workflows", 
                   size=14, color=colors['secondary_text']),
        ]
    
    def render(self) -> ft.Column:
        """
        Render the instructions view content.
        
        Returns:
            ft.Column: The instructions page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Get current mode from session
        current_mode = self.page.session.get("selected_mode")
        
        # Get temp directory info
        temp_dir = self.page.session.get("temp_directory")
        temp_objs_dir = self.page.session.get("temp_objs_directory")
        temp_tn_dir = self.page.session.get("temp_tn_directory")
        temp_small_dir = self.page.session.get("temp_small_directory")
        
        # Build file paths section
        file_paths_controls = []
        if temp_dir:
            file_paths_controls.extend([
                ft.Text("Current Session Directories:", 
                       size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Container(height=5),
                ft.Text(f"Base: {temp_dir}", 
                       size=12, color=colors['secondary_text'], selectable=True),
                ft.Text(f"OBJS/: {temp_objs_dir}", 
                       size=12, color=colors['secondary_text'], selectable=True),
                ft.Text(f"TN/: {temp_tn_dir}", 
                       size=12, color=colors['secondary_text'], selectable=True),
                ft.Text(f"SMALL/: {temp_small_dir}", 
                       size=12, color=colors['secondary_text'], selectable=True),
                ft.Container(height=15),
            ])
        
        # Get mode-specific instructions
        if current_mode == "Alma":
            instruction_controls = self.get_alma_instructions()
        elif current_mode == "CollectionBuilder":
            instruction_controls = self.get_collectionbuilder_instructions()
        else:
            instruction_controls = self.get_no_mode_instructions()
        
        # Build the layout
        return ft.Column([
            ft.Row([
                ft.Text("Follow-Up Instructions", size=24, weight=ft.FontWeight.BOLD),
                self.create_log_button("Show Logs", ft.Icons.LIST_ALT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=15, color=colors['divider']),
            
            # Current mode indicator
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Current Mode: {current_mode or 'None'}", 
                           size=16, weight=ft.FontWeight.BOLD, color=colors['container_text']),
                ], spacing=5),
                padding=ft.padding.all(10),
                border=ft.border.all(1, colors['border']),
                border_radius=10,
                bgcolor=colors['container_bg'],
                margin=ft.margin.symmetric(vertical=5)
            ),
            
            ft.Container(height=10),
            
            # File paths section (if available)
            *file_paths_controls,
            
            # Instructions container
            ft.Container(
                content=ft.Column(
                    instruction_controls,
                    spacing=5,
                    scroll=ft.ScrollMode.AUTO
                ),
                padding=ft.padding.all(15),
                border=ft.border.all(1, colors['border']),
                border_radius=10,
                bgcolor=colors['container_bg'],
                expand=True
            ),
            
        ], alignment="start", expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)
