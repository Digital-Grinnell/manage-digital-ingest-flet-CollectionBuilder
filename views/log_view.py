"""
Log View for Manage Digital Ingest Application

This module contains the LogView class for displaying logs.
"""

import flet as ft
from views.base_view import BaseView
from views.log_overlay import LogOverlay


class LogView(BaseView):
    """
    Log view class for displaying application logs.
    """
    
    def render(self) -> ft.Column:
        """
        Render the log view content.
        
        Returns:
            ft.Column: The log page layout
        """
        self.on_view_enter()
        
        # Show the overlay instead of a full page
        log_overlay = LogOverlay(self.page)
        log_overlay.show()
        
        # Return a simple page that explains the overlay
        colors = self.get_theme_colors()
        return ft.Column([
            ft.Text("Process Log & Progress", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=15),
            ft.Text("The log viewer is now displayed as an overlay.", 
                   size=16, color=colors['primary_text']),
            ft.Text("You can view logs while continuing to work on other pages.", 
                   size=14, color=colors['secondary_text']),
            ft.Container(height=15),
            ft.ElevatedButton(
                text="Show Log Overlay",
                icon=ft.Icons.VISIBILITY,
                on_click=lambda e: log_overlay.show()
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)