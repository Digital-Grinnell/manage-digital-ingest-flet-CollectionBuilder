"""
Exit View for Manage Digital Ingest Application

This module contains the ExitView class for handling application termination.
"""

import flet as ft
import sys
from views.base_view import BaseView


class ExitView(BaseView):
    """
    Exit view class for application termination.
    Provides a confirmation dialog with Confirm/Cancel options.
    """
    
    def render(self) -> ft.Column:
        """
        Render the exit view content.
        
        Returns:
            ft.Column: The exit page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        def on_cancel_exit(e):
            """Handle cancellation of exit action."""
            self.logger.info("User cancelled application exit")
            # Navigate back to home page
            self.page.go("/")
        
        return ft.Column([
            ft.Container(height=50),
            ft.Icon(
                ft.Icons.EXIT_TO_APP,
                size=64,
                color=colors['primary_text']
            ),
            ft.Container(height=20),
            ft.Text(
                "Exit Application",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=colors['primary_text']
            ),
            ft.Container(height=15),
            ft.Text("There's no good way to gracefully shutdown this Flet window.", size=16, color=colors['secondary_text']),
            ft.Row([
                ft.Text("Please click ", size=16, color=colors['secondary_text']),
                ft.Icon(ft.Icons.CIRCLE, size=16, color=ft.Colors.RED),
                ft.Text(" in the upper-left corner of the window to terminate this app.", size=16, color=colors['secondary_text'])
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton(
                    "Cancel",
                    icon=ft.Icons.CANCEL,
                    on_click=on_cancel_exit,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREY_400,
                        color=ft.Colors.WHITE
                    ),
                    width=120,
                    height=40
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20)
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True)