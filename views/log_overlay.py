"""
Log Overlay Module for Manage Digital Ingest Application

This module contains the LogOverlay class for displaying logs and progress
in an overlay dialog.
"""

import flet as ft
import logging
import os


class LogOverlay:
    """
    Handles the creation and management of the log overlay dialog.
    """
    
    def __init__(self, page: ft.Page):
        """
        Initialize the log overlay.
        
        Args:
            page (ft.Page): The Flet page object
        """
        self.page = page
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_theme_colors(self):
        """Get theme-appropriate colors based on current theme mode"""
        # Detect if we're in dark mode
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        if is_dark:
            return {
                'primary_text': ft.Colors.WHITE,
                'secondary_text': ft.Colors.GREY_300,
                'border': ft.Colors.GREY_600,
                'markdown_bg': ft.Colors.PURPLE_900,
                'container_bg': ft.Colors.GREY_900,
                'container_text': ft.Colors.WHITE,
            }
        else:
            return {
                'primary_text': ft.Colors.BLACK,
                'secondary_text': ft.Colors.GREY_600,
                'border': ft.Colors.GREY_400,
                'markdown_bg': ft.Colors.PURPLE_50,
                'container_bg': ft.Colors.GREY_100,
                'container_text': ft.Colors.BLACK,
            }
    
    def read_recent_logs(self, max_lines=100):
        """Read the most recent log entries from mdi.log"""
        try:
            with open("mdi.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Return the last max_lines entries
                return lines[-max_lines:] if len(lines) > max_lines else lines
        except Exception as e:
            return [f"Error reading log file: {str(e)}\\n"]
    
    def create_overlay(self):
        """Create the log viewer as an overlay dialog"""
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Get current search state information
        selected_files = self.page.session.get("selected_files") or []
        search_directory = self.page.session.get("search_directory")
        search_in_progress = self.page.session.get("search_in_progress") or False
        current_progress = self.page.session.get("search_progress") or 0.0
        
        # Read recent log entries
        log_entries = self.read_recent_logs(100)  # Get last 100 log entries
        
        # Create log display controls
        log_controls = []
        for entry in log_entries:
            entry = entry.strip()
            if entry:
                log_controls.append(ft.Text(entry, size=11, color=colors['primary_text']))
        
        # Create status information
        status_info = []
        
        # Add current status information
        if selected_files:
            status_info.append(
                ft.Text(f"📁 Files to process: {len(selected_files)}", 
                       size=14, color=colors['primary_text'])
            )
        
        if search_directory:
            status_info.append(
                ft.Text(f"🔍 Search directory: {search_directory}", 
                       size=12, color=colors['secondary_text'])
            )
        
        if search_in_progress:
            status_info.append(
                ft.Text("⏳ Process in progress...", 
                       size=12, color=colors['primary_text'], weight=ft.FontWeight.BOLD)
            )
        
        # Create progress bar
        progress_bar = ft.ProgressBar(
            value=current_progress,
            width=350,
            color=ft.Colors.BLUE,
            bgcolor=colors['container_bg']
        )
        
        # Create cancel button
        def on_cancel_click(e):
            self.cancel_process()
            # Refresh the overlay content
            self.show()
        
        cancel_button = ft.ElevatedButton(
            text="Cancel Process",
            icon=ft.Icons.CANCEL,
            bgcolor=ft.Colors.RED_600,
            color="white",
            visible=search_in_progress,
            on_click=on_cancel_click
        )
        
        # Create refresh button
        def on_refresh_click(e):
            # Close current overlay and open a new one with fresh data
            self.close()
            self.show()
        
        refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh logs",
            on_click=on_refresh_click
        )
        
        # Create the overlay dialog
        log_overlay = ft.AlertDialog(
            modal=False,  # Allow interaction with background
            title=ft.Row([
                ft.Text("Process Log & Progress", size=18, weight=ft.FontWeight.BOLD),
                refresh_button
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    # Status information
                    ft.Column(status_info, spacing=4) if status_info else ft.Container(),
                    
                    # Progress section
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Process Progress", 
                                   size=16, weight=ft.FontWeight.BOLD, color=colors['container_text']),
                            progress_bar,
                            ft.Text(f"Progress: {current_progress:.0%}" if current_progress > 0 else "Ready to start...", 
                                   size=12, color=colors['container_text']),
                            cancel_button,
                        ], spacing=6),
                        padding=ft.padding.all(8),
                        border=ft.border.all(1, colors['border']),
                        border_radius=8,
                        bgcolor=colors['container_bg'],
                        margin=ft.margin.symmetric(vertical=4)
                    ),
                    
                    # Log display section
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Application Logs", 
                                   size=16, weight=ft.FontWeight.BOLD, color=colors['container_text']),
                            ft.Container(
                                content=ft.Column(
                                    controls=log_controls,
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=1
                                ) if log_controls else ft.Text("No log entries found", 
                                                              size=12, color=colors['secondary_text']),
                                height=188,
                                border=ft.border.all(1, colors['border']),
                                border_radius=5,
                                padding=6,
                                bgcolor=colors['markdown_bg']
                            )
                        ], spacing=6),
                        padding=ft.padding.all(8),
                        border=ft.border.all(1, colors['border']),
                        border_radius=8,
                        bgcolor=colors['container_bg'],
                        margin=ft.margin.symmetric(vertical=4)
                    ),
                    
                ], spacing=8),
                width=500,
                height=400
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        return log_overlay
    
    def show(self):
        """Show the log overlay dialog"""
        # Close existing overlay if any
        self.close()
        
        # Create and show new overlay
        log_overlay = self.create_overlay()
        self.page.session.set("_log_overlay", log_overlay)
        self.page.overlay.append(log_overlay)
        log_overlay.open = True
        self.page.update()
        self.logger.info("Opened log overlay")
    
    def close(self):
        """Close the log overlay dialog"""
        log_overlay = self.page.session.get("_log_overlay")
        if log_overlay:
            log_overlay.open = False
            # Remove from overlay list to clean up
            if log_overlay in self.page.overlay:
                self.page.overlay.remove(log_overlay)
            self.page.session.set("_log_overlay", None)
            self.page.update()
            self.logger.info("Closed log overlay")
    
    def cancel_process(self):
        """Cancel the current process"""
        self.page.session.set("cancel_search", True)
        self.page.session.set("search_in_progress", False)
        self.logger.warning("Process cancelled by user")
        
        # Refresh the overlay if it's open, otherwise do nothing
        if self.page.session.get("_log_overlay") and self.page.session.get("_log_overlay").open:
            self.show()