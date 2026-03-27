import logging
import os
import traceback
from pathlib import Path

from lxml import html, etree

logger = logging.getLogger(__name__)


class HtmlService:

    def parse(self, filename: Path):
        """
            Parses HTML from either a local file path

            Args:
                filename (Path): Path to the file to parse
        """
        logger.info(f"{self.__class__.__name__} Started parsing {filename} as element tree")
        try:
            if os.path.exists(filename) and os.path.isfile(filename):
                return html.parse(filename)
        except Exception as e:
            logger.info(f"{self.__class__.__name__} Failed to parse file {filename} with error: {e}")
            logger.info(f"{self.__class__.__name__} Traceback: {traceback.format_exc()}")

    def save_html(self, root_element: etree.Element, filename: Path) -> None:
        """
            Saves html element tree to file

            Args:
                root_element (etree.Element): Root element of the html element
                filename (Path): Path to the file to save
        """
        logger.info(f"{self.__class__.__name__} Saving xml data to {filename}")
        # Wrap the root element in an ElementTree object
        tree = etree.ElementTree(root_element)

        # Write directly to the file path
        tree.write(
            str(filename),
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )
        logger.info(f"{self.__class__.__name__} Finished saving html data to {filename}")
