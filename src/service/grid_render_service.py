import logging
import os
import traceback
from pathlib import Path
from typing import List

from src.service.html_service import HtmlService
from src.service.table_renderer_service import TableRendererService

logger = logging.getLogger(__name__)


class GridRenderService:
    def __init__(self, html_service: HtmlService,
                 playwright_service: TableRendererService):
        self.html_service = html_service
        self.playwright_service = playwright_service
        self.input_dir: Path = "html"
        self.output_dir: Path = "html"
        self.file_ext: str = "html"

    def convert(self) -> None:
        # TODO: Add logic for deflating files is upload is compressed file
        input_files = self._list_input_files(Path(self.input_dir), self.file_ext)

        for file_path in input_files:
            try:
                # Parse html as element tree
                tree = self.html_service.parse(file_path)
                tables = tree.xpath("//table")

                for idx, table in enumerate(tables):
                    # Generate unique image name
                    image_name = f"{file_path.stem}_table_{idx}.png"
                    image_path = Path(f"{self.output_dir}/{image_name}")

                    # Render table to screenshot
                    self.playwright_service.render_table(str(table), image_path)

                    # Replace table with new image tag
                    parent = table.getparent()
                    img = tree.Element("img", src=image_path)
                    parent.replace(table, img)

                    # Write updated tree in output file
                    self.html_service.save_html(parent, file_path)  # TODO: Add output file name logic

            except Exception as e:
                logger.info(f"{self.__class__.__name__} Failed to parse file {file_path} with error: {e}")
                logger.info(f"{self.__class__.__name__} Traceback: {traceback.format_exc()}")

    def _list_input_files(self, input_dir: Path, file_ext: str) -> List[Path]:
        """
            Provides the list of input files to be processed filtering files
            matching the extension in config

            Args:
                input_dir: Directory containing the input files.
                file_ext: File extension to filter files with.

            Returns:
                List of input files to be processed.
        """
        return [
            Path(os.path.join(input_dir, f))
            for f in os.listdir(input_dir)
            if f.endswith(file_ext)
        ]
