import logging
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class TableRendererService:
    def __init__(self):
        pass

    def render_table(self, table_html: str, output_path: Path) -> None:
        full_html = f"""
        <html>
        <head>
            <style>
                body {{ margin: 0; padding: 10px; }}
                table {{ border-collapse: collapse; }}
                td, th {{ border: 1px solid #000; padding: 6px; }}
            </style>
        </head>
        <body>
            {table_html}
        </body>
        </html>
        """

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()

                page = browser.new_page()
                page.set_content(full_html)
                page.screenshot(path=str(output_path), full_page=True, type="png")
        except Exception as e:
            logger.info(f"{self.__class__.__name__} An error occurred while rendering table with playwright: {e}")
            logger.info(f"{self.__class__.__name__} Traceback: {traceback.format_exc()}")
        finally:
            browser.close()
