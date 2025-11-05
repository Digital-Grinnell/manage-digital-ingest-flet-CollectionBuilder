"""
Home View for Manage Digital Ingest Application

This module contains the HomeView class for displaying the main home page.
"""

import flet as ft
from views.base_view import BaseView
import utils


class HomeView(BaseView):
    """
    Home view class for displaying the main application page with branding and info.
    """
    
    def render(self) -> ft.Column:
        """
        Render the home view content.
        
        Returns:
            ft.Column: The home page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()

        # Read markdown content from a file
        markdown_text = utils.read_markdown("_data/home.md")
        
        # Create a Markdown widget with the content
        md_widget = ft.Markdown(
            markdown_text, 
            md_style_sheet=self.get_markdown_style()
        )  

        # Read config from _data/config.json
        config = utils.read_config()

        return ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    height=8,
                ),
                ft.Image(
                    src='Primary_Libraries.png',  # Updated to Grinnell College Libraries logo
                    fit=ft.ImageFit.CONTAIN,
                    width=400,
                ),
                ft.Text(f"🚀 powered by Flet {config['flet_version']} and Python version {config['python_version']} 🐍", color=colors['secondary_text']),
                ft.Text("Manage Digital Ingest: CollectionBuilder Edition", size=35),
                ft.Markdown("A Flet Python app for managing Grinnell College ingest of digital objects to CollectionBuilder"),
                ft.Divider(height=15, color=colors['divider']),
                md_widget,
                ft.Divider(height=15, color=colors['divider']),
                ft.Container(
                    height=60,
                    content=ft.Markdown("**Thanks for choosing Flet!**"),
                ),
            ],
        )