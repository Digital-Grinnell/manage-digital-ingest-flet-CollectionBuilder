"""
About View for Manage Digital Ingest Application

This module contains the AboutView class for displaying application information
and session data.
"""

import flet as ft
from views.base_view import BaseView
import utils
import logging
import json
import os


class AboutView(BaseView):
    """
    About view class for displaying application information and demo logging.
    """
    
    PERSISTENT_SESSION_FILE = "storage/data/persistent_session.json"
    
    def preserve_session(self, e):
        """
        Save all session data to a persistent JSON file and protect temp directory.
        """
        try:
            # Ensure storage/data directory exists
            os.makedirs(os.path.dirname(self.PERSISTENT_SESSION_FILE), exist_ok=True)
            
            # Collect all session data
            session_data = {}
            for key in self.page.session.get_keys():
                value = self.page.session.get(key)
                # Convert to JSON-serializable format
                if isinstance(value, (str, int, float, bool, type(None))):
                    session_data[key] = value
                elif isinstance(value, (list, dict)):
                    session_data[key] = value
                else:
                    # For other types, convert to string representation
                    session_data[key] = str(value)
            
            # Add a flag to mark temp directory as protected
            temp_directory = self.page.session.get("temp_directory")
            if temp_directory:
                session_data["_temp_protected"] = True
            
            # Save to JSON file
            with open(self.PERSISTENT_SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.info(f"Preserved {len(session_data)} session keys to {self.PERSISTENT_SESSION_FILE}")
            if temp_directory:
                self.logger.info(f"Protected temporary directory: {temp_directory}")
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Session preserved! {len(session_data)} keys saved."),
                bgcolor=ft.Colors.GREEN_600
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.logger.error(f"Error preserving session: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def clear_session(self, e):
        """
        Clear all session data and delete the persistent session file.
        Resets the application to pristine initial state.
        """
        try:
            # Get all session keys before clearing
            session_keys = list(self.page.session.get_keys())
            key_count = len(session_keys)
            
            # Clear all session variables
            for key in session_keys:
                self.page.session.remove(key)
            
            # Delete the persistent session file if it exists
            if os.path.exists(self.PERSISTENT_SESSION_FILE):
                os.remove(self.PERSISTENT_SESSION_FILE)
                self.logger.info(f"Deleted persistent session file: {self.PERSISTENT_SESSION_FILE}")
            
            self.logger.info(f"Cleared {key_count} session keys - session reset to pristine state")
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Session cleared! {key_count} keys removed. Application reset to initial state."),
                bgcolor=ft.Colors.ORANGE_700
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    @staticmethod
    def restore_session(page):
        """
        Restore session data from persistent JSON file if it exists.
        Should be called during app initialization.
        
        Args:
            page: The Flet page object
        """
        try:
            persistent_file = "storage/data/persistent_session.json"
            if os.path.exists(persistent_file):
                with open(persistent_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Restore all session keys
                for key, value in session_data.items():
                    if key != "_temp_protected":  # Don't restore the protection flag itself
                        page.session.set(key, value)
                
                # Log restoration
                logger = logging.getLogger(__name__)
                logger.info(f"Restored {len(session_data)} session keys from {persistent_file}")
                
                temp_dir = session_data.get("temp_directory")
                if temp_dir and session_data.get("_temp_protected"):
                    logger.info(f"Restored protected temporary directory: {temp_dir}")
                
                return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error restoring session: {e}")
        
        return False
    
    def render(self) -> ft.Column:
        """
        Render the about view content.
        
        Returns:
            ft.Column: The about page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Demo buttons to exercise the SnackBar logger at different levels
        def _log_info(e):
            self.logger.info("Demo INFO from About page")

        def _log_warn(e):
            self.logger.warning("Demo WARNING from About page")

        def _log_error(e):
            self.logger.error("Demo ERROR from About page")

        # Generate session report as plain text (markdown breaks with complex data)
        session_data_found = False
        session_lines = []
        session_lines.append(ft.Text("Current Session Data:", size=18, weight=ft.FontWeight.BOLD, color=colors['primary_text']))
        session_lines.append(ft.Container(height=10))

        # Get all session keys and values
        for key in self.page.session.get_keys():
            value = self.page.session.get(key)
            # Don't truncate - show full values
            value_str = str(value)
            session_lines.append(
                ft.Column([
                    ft.Text(f"{key}:", size=14, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                    ft.Text(value_str, size=12, color=colors['code_text'], selectable=True),
                    ft.Container(height=5),
                ], spacing=2)
            )
            session_data_found = True
        
        if not session_data_found:
            session_lines.append(ft.Text("No session data found!", italic=True, color=colors['secondary_text']))
        
        session_lines.append(ft.Container(height=10))
        session_lines.append(ft.Divider(color=colors['divider']))
        session_lines.append(ft.Text("This report shows all key-value pairs stored in page.session.", 
                                     size=11, italic=True, color=colors['secondary_text']))

        # Create a column with all session data
        session_widget = ft.Column(session_lines, spacing=0, scroll=ft.ScrollMode.AUTO)  

        # Read config from _data/config.json
        config = utils.read_config()

        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=8),
                ft.Image(
                    src='assets/Primary_Libraries.png',  # Grinnell College Libraries logo
                    fit=ft.ImageFit.CONTAIN,
                    width=400,
                ),
                ft.Text(f"🚀 powered by Flet {config['flet_version']} and Python version {config['python_version']} 🐍", 
                       color=colors['secondary_text']),
                ft.Text("Manage Digital Ingest: CollectionBuilder Edition", 
                       size=24, weight=ft.FontWeight.BOLD),
                ft.Text("A Flet Python app for managing Grinnell College ingest of digital objects to CollectionBuilder",
                       size=14, color=colors['secondary_text']),
                ft.Divider(height=15, color=colors['divider']),
                ft.Container(
                    content=session_widget,
                    padding=10,
                    width=800,
                    height=400,  # Set explicit height for scrolling
                    bgcolor=colors['container_bg'],
                    border=ft.border.all(1, colors['border']),
                    border_radius=8,
                ),
                ft.Divider(height=15, color=colors['divider']),
                ft.Row([
                    ft.ElevatedButton("Log INFO", on_click=_log_info),
                    ft.ElevatedButton("Log WARNING", on_click=_log_warn),
                    ft.ElevatedButton("Log ERROR", on_click=_log_error),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Divider(height=15, color=colors['divider']),
                ft.Text("Session Management", size=18, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Text(
                    "Save current session state and protect temporary directory, or reset to pristine settings",
                    size=12, italic=True, color=colors['secondary_text'], text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=5),
                ft.Row([
                    ft.ElevatedButton(
                        "Preserve Session & Protect Temp",
                        icon=ft.Icons.SAVE_OUTLINED,
                        on_click=self.preserve_session,
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Clear Session & Reset",
                        icon=ft.Icons.RESTART_ALT,
                        on_click=self.clear_session,
                        bgcolor=ft.Colors.ORANGE_700,
                        color=ft.Colors.WHITE
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(height=20),
            ],
        )