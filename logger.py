import logging
import flet as ft


class SnackBarHandler(logging.Handler):
    """A logging.Handler that posts log messages to a Flet SnackBar.

    It expects the LogRecord to have an attribute `page` (or that the
    application sets a page in the handler via handler.set_page(page)).
    To keep usage simple, the handler will also look for `record.page` and
    fall back to a stored page reference.
    """

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self._page = None

    @property
    def page(self):
        """Get the page reference."""
        return self._page
    
    @page.setter
    def page(self, value):
        """Set the page reference."""
        self._page = value

    def set_page(self, page: ft.Page):
        """Give the handler a reference to the Flet page so it can show SnackBars."""
        self._page = page

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            page = getattr(record, 'page', None) or self._page
            
            if page is None:
                # No page available; nothing we can do
                return

            # Ensure a snack_bar exists on the page
            if not hasattr(page, 'snack_bar') or page.snack_bar is None:
                page.snack_bar = ft.SnackBar(content=ft.Text(msg))

            # Only show warnings and errors in snackbar
            if record.levelno >= logging.WARNING:
                # Color by level
                if record.levelno >= logging.ERROR:
                    bgcolor = ft.Colors.RED_600
                else:
                    bgcolor = ft.Colors.ORANGE_400
                
                page.snack_bar.content.value = msg
                page.snack_bar.bgcolor = bgcolor
                page.open(page.snack_bar)
                page.update()
        except Exception:
            self.handleError(record)
