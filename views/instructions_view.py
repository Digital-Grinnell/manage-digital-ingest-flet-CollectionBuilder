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
    
    def generate_cb_deployment_script(self, e):
        """Generate CollectionBuilder deployment script to copy CSV and update _config.yml."""
        try:
            self.logger.info("Generate deployment script button clicked")
            
            # Get session data
            temp_csv_path = self.page.session.get("temp_csv_file") or ""
            temp_csv_filename = self.page.session.get("temp_csv_filename") or ""
            temp_dir = self.page.session.get("temp_directory") or ""
            
            self.logger.info(f"Session data - temp_csv_path: {temp_csv_path}, temp_csv_filename: {temp_csv_filename}")
            
            if not temp_csv_path or not temp_csv_filename:
                self.logger.warning("Missing CSV file information in session")
                self.show_snack("No CSV file found. Please complete the Update CSV step first.", is_error=True)
                return
            
            if not temp_dir:
                self.logger.warning("No temp directory found in session")
                self.show_snack("No temp directory found. Please complete the workflow first.", is_error=True)
                return
            
            # Remove .csv extension for metadata key
            metadata_name = temp_csv_filename.replace(".csv", "")
            
            # Generate the bash script
            script_content = f"""#!/bin/bash
# CollectionBuilder Deployment Script
# Generated by Manage Digital Ingest
#
# IMPORTANT: Run this script FROM your CollectionBuilder project directory!
# cd to your project before running this script!
#
# This script copies the updated CSV file and updates _config.yml

set -e  # Exit on error

echo "=========================================="
echo "CollectionBuilder Deployment Script"
echo "=========================================="
echo ""

# Check if we're in a CollectionBuilder project directory
if [ ! -f "_config.yml" ]; then
    echo "ERROR: _config.yml not found in current directory"
    echo "Please run this script from your CollectionBuilder project root directory"
    exit 1
fi

# Check if _data directory exists
if [ ! -d "_data" ]; then
    echo "Creating _data directory..."
    mkdir -p _data
fi

# Copy the updated CSV file
echo "Copying CSV file to _data directory..."
cp "{temp_csv_path}" "_data/{temp_csv_filename}"

if [ $? -eq 0 ]; then
    echo "✓ CSV file copied successfully: _data/{temp_csv_filename}"
else
    echo "✗ Failed to copy CSV file"
    exit 1
fi

# Update _config.yml
echo ""
echo "Updating _config.yml metadata reference..."

# Check if metadata key exists in _config.yml
if grep -q "^metadata:" "_config.yml"; then
    # Backup _config.yml
    cp _config.yml _config.yml.backup
    echo "  (Backup created: _config.yml.backup)"
    
    # Update the metadata line
    sed -i.tmp 's/^metadata:.*/metadata: {metadata_name}/' _config.yml
    rm -f _config.yml.tmp
    
    echo "✓ Updated metadata key in _config.yml"
    echo "  New value: metadata: {metadata_name}"
else
    echo "⚠ Warning: 'metadata:' key not found in _config.yml"
    echo "  Please manually add the following line to _config.yml:"
    echo "  metadata: {metadata_name}"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the changes: git diff _config.yml"
echo "2. Test locally: bundle exec jekyll s"
echo "3. Commit and push when ready"
echo ""
"""

            # Write script to temp directory
            script_filename = "deploy_to_collectionbuilder.sh"
            script_path = os.path.join(temp_dir, script_filename)
            
            try:
                with open(script_path, "w") as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)  # Make executable
                self.logger.info(f"Generated deployment script: {script_path}")
            except Exception as ex:
                self.logger.error(f"Failed to save script: {ex}")
                self.show_snack(f"Failed to save script: {ex}", is_error=True)
                return
            
            # Create commands for user to copy
            copy_command = f'cp "{script_path}" .'
            run_command = f'./{script_filename}'
            
            # Create dialog to show the script
            colors = self.get_theme_colors()
            
            dialog = ft.AlertDialog(
                title=ft.Text("CollectionBuilder Deployment Script Generated", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.ORANGE_700, size=20),
                                ft.Text(
                                    "Run these commands FROM your CollectionBuilder project directory!",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ORANGE_900,
                                ),
                            ], spacing=8),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=10,
                            border_radius=4,
                            border=ft.border.all(1, ft.Colors.ORANGE_700),
                        ),
                        ft.Container(height=15),
                        
                        ft.Text(
                            "Script saved to:",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Container(
                            content=ft.Text(
                                script_path,
                                size=11,
                                font_family="Courier New",
                                color=colors['secondary_text'],
                                selectable=True
                            ),
                            bgcolor=ft.Colors.GREY_200,
                            padding=8,
                            border_radius=4,
                        ),
                        ft.Container(height=15),
                        
                        ft.Text(
                            "Step 1: Copy script to your project directory",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    copy_command,
                                    size=12,
                                    font_family="Courier New",
                                    color=ft.Colors.WHITE,
                                    selectable=True
                                ),
                                expand=True,
                                bgcolor=ft.Colors.GREY_900,
                                padding=10,
                                border_radius=4,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                tooltip="Copy command",
                                on_click=lambda e: self.copy_to_clipboard(e, copy_command)
                            )
                        ], spacing=5),
                        
                        ft.Container(height=10),
                        
                        ft.Text(
                            "Step 2: Run the script",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    run_command,
                                    size=12,
                                    font_family="Courier New",
                                    color=ft.Colors.WHITE,
                                    selectable=True
                                ),
                                expand=True,
                                bgcolor=ft.Colors.GREY_900,
                                padding=10,
                                border_radius=4,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                tooltip="Copy command",
                                on_click=lambda e: self.copy_to_clipboard(e, run_command)
                            )
                        ], spacing=5),
                        
                        ft.Container(height=15),
                        ft.Divider(),
                        
                        ft.Text(
                            "What the script does:",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Text(
                            f"• Copies {temp_csv_filename} to _data/ directory",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Text(
                            f"• Updates _config.yml: metadata: {metadata_name}",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Text(
                            "• Creates backup of _config.yml before modifying",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        
                        ft.Container(height=10),
                        
                        ft.Text(
                            "Script contents (for reference):",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=colors['secondary_text']
                        ),
                        ft.Container(
                            content=ft.Text(
                                script_content,
                                size=10,
                                font_family="Courier New",
                                color=ft.Colors.GREEN_300,
                                selectable=True
                            ),
                            bgcolor=ft.Colors.GREY_900,
                            padding=10,
                            border_radius=4,
                            height=250
                        ),
                    ], spacing=5, scroll=ft.ScrollMode.AUTO),
                    width=700,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.logger.info("Opening deployment script dialog")
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            self.logger.info("Dialog should now be visible")
            
        except Exception as ex:
            self.logger.error(f"Error generating deployment script: {ex}", exc_info=True)
            self.show_snack(f"Error: {ex}", is_error=True)
            
            # Generate the bash script
            script_content = f"""#!/bin/bash
# CollectionBuilder Deployment Script
# Generated by Manage Digital Ingest
#
# IMPORTANT: Run this script FROM your CollectionBuilder project directory!
# cd to your project before running this script!
#
# This script copies the updated CSV file and updates _config.yml

set -e  # Exit on error

echo "=========================================="
echo "CollectionBuilder Deployment Script"
echo "=========================================="
echo ""

# Check if we're in a CollectionBuilder project directory
if [ ! -f "_config.yml" ]; then
    echo "ERROR: _config.yml not found in current directory"
    echo "Please run this script from your CollectionBuilder project root directory"
    exit 1
fi

# Check if _data directory exists
if [ ! -d "_data" ]; then
    echo "Creating _data directory..."
    mkdir -p _data
fi

# Copy the updated CSV file
echo "Copying CSV file to _data directory..."
cp "{temp_csv_path}" "_data/{temp_csv_filename}"

if [ $? -eq 0 ]; then
    echo "✓ CSV file copied successfully: _data/{temp_csv_filename}"
else
    echo "✗ Failed to copy CSV file"
    exit 1
fi

# Update _config.yml
echo ""
echo "Updating _config.yml metadata reference..."

# Check if metadata key exists in _config.yml
if grep -q "^metadata:" "_config.yml"; then
    # Backup _config.yml
    cp _config.yml _config.yml.backup
    echo "  (Backup created: _config.yml.backup)"
    
    # Update the metadata line
    sed -i.tmp 's/^metadata:.*/metadata: {metadata_name}/' _config.yml
    rm -f _config.yml.tmp
    
    echo "✓ Updated metadata key in _config.yml"
    echo "  New value: metadata: {metadata_name}"
else
    echo "⚠ Warning: 'metadata:' key not found in _config.yml"
    echo "  Please manually add the following line to _config.yml:"
    echo "  metadata: {metadata_name}"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the changes: git diff _config.yml"
echo "2. Test locally: bundle exec jekyll s"
echo "3. Commit and push when ready"
echo ""
"""

            # Create dialog to show the script
            colors = self.get_theme_colors()
            
            dialog = ft.AlertDialog(
                title=ft.Text("CollectionBuilder Deployment Script", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.ORANGE_700, size=20),
                                ft.Text(
                                    "Run this script FROM your CollectionBuilder project directory!",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ORANGE_900,
                                ),
                            ], spacing=8),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=10,
                            border_radius=4,
                            border=ft.border.all(1, ft.Colors.ORANGE_700),
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            "This script will:",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Text(
                            f"1. Copy {temp_csv_filename} to _data/ directory",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Text(
                            f"2. Update _config.yml: metadata: {metadata_name}",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            "Usage:",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Text(
                            "1. Click 'Copy Script' button below",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Text(
                            "2. Save it as 'deploy_csv.sh' in your CollectionBuilder project root",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Text(
                            "3. Make it executable: chmod +x deploy_csv.sh",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Text(
                            "4. Run it: ./deploy_csv.sh",
                            size=12,
                            color=colors['secondary_text']
                        ),
                        ft.Container(height=10),
                        ft.Text("Script:", size=13, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(
                                script_content,
                                size=11,
                                font_family="Courier New",
                                color=ft.Colors.GREEN_300,
                                selectable=True
                            ),
                            bgcolor=ft.Colors.GREY_900,
                            padding=10,
                            border_radius=4,
                            height=400
                        ),
                    ], spacing=5, scroll=ft.ScrollMode.AUTO),
                    width=700,
                ),
                actions=[
                    ft.ElevatedButton(
                        text="Copy Script",
                        icon=ft.Icons.COPY_ALL,
                        on_click=lambda e: self.copy_to_clipboard(e, script_content),
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.GREEN_700
                        )
                    ),
                    ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            
            self.logger.info("Opening deployment script dialog")
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            self.logger.info("Dialog should now be visible")
            
        except Exception as ex:
            self.logger.error(f"Error generating deployment script: {ex}", exc_info=True)
            self.show_snack(f"Error: {ex}", is_error=True)
    
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
        
        # Get temp CSV info from session
        temp_csv_path = self.page.session.get("temp_csv_file") or ""
        temp_csv_filename = self.page.session.get("temp_csv_filename") or ""
        
        instructions = [
            ft.Text("CollectionBuilder Workflow - Next Steps", 
                   size=20, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=15),
            
            # Highlighted important information box
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.BLUE_700, size=24),
                        ft.Text("Updated CSV File", 
                               size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ], spacing=10),
                    ft.Divider(height=1, color=ft.Colors.BLUE_300),
                    ft.Text(
                        "To adopt the changes made by MDI:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=colors['primary_text']
                    ),
                    ft.Container(height=5),
                    ft.Text(
                        "1. Save the updated CSV file to your CollectionBuilder project",
                        size=14,
                        color=colors['primary_text']
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"   • Updated CSV: {temp_csv_filename or 'N/A'}",
                                size=13,
                                color=colors['secondary_text'],
                                font_family="Courier New"
                            ),
                            ft.Text(
                                f"   • Full path: {temp_csv_path}",
                                size=12,
                                color=colors['secondary_text'],
                                italic=True,
                                selectable=True
                            ),
                            ft.Text(
                                "   • Destination: <your-project>/_data/",
                                size=13,
                                color=ft.Colors.GREEN_700,
                                weight=ft.FontWeight.BOLD
                            ),
                        ], spacing=3),
                        margin=ft.margin.only(left=20, top=5)
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "2. Update your _config.yml file",
                        size=14,
                        color=colors['primary_text']
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                '   • Update the "metadata:" key to reference your new CSV file',
                                size=13,
                                color=colors['secondary_text']
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f'   metadata: {temp_csv_filename.replace(".csv", "") if temp_csv_filename else "your-metadata"}',
                                    size=12,
                                    color=ft.Colors.WHITE,
                                    font_family="Courier New",
                                    selectable=True
                                ),
                                bgcolor=ft.Colors.GREY_900,
                                padding=8,
                                border_radius=4,
                                margin=ft.margin.only(top=5)
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700, size=16),
                                    ft.Text(
                                        'IMPORTANT: The metadata key value should NEVER include the .csv extension',
                                        size=12,
                                        color=ft.Colors.ORANGE_900,
                                        weight=ft.FontWeight.BOLD,
                                        italic=True
                                    ),
                                ], spacing=5),
                                bgcolor=ft.Colors.ORANGE_50,
                                padding=8,
                                border_radius=4,
                                border=ft.border.all(1, ft.Colors.ORANGE_700),
                                margin=ft.margin.only(top=8)
                            ),
                        ], spacing=3),
                        margin=ft.margin.only(left=20, top=5)
                    ),
                ], spacing=5),
                padding=ft.padding.all(15),
                border=ft.border.all(2, ft.Colors.BLUE_700),
                border_radius=8,
                bgcolor=ft.Colors.BLUE_50,
                margin=ft.margin.only(bottom=20)
            ),
            
            # Deployment script generator button
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Automated Deployment Script",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=colors['primary_text']
                    ),
                    ft.Text(
                        "Generate a bash script to automatically copy the CSV and update _config.yml",
                        size=13,
                        color=colors['secondary_text']
                    ),
                    ft.Container(
                        content=ft.ElevatedButton(
                            text="Generate Deployment Script",
                            icon=ft.Icons.TERMINAL,
                            on_click=self.generate_cb_deployment_script,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.GREEN_700
                            )
                        ),
                        margin=ft.margin.only(top=10)
                    ),
                ], spacing=5),
                padding=ft.padding.all(15),
                border=ft.border.all(2, ft.Colors.GREEN_700),
                border_radius=8,
                bgcolor=colors['markdown_bg'],
                margin=ft.margin.only(bottom=15)
            ),
        ]
        
        return instructions
    
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
