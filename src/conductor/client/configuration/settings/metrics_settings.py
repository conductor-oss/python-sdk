from __future__ import annotations
import logging
import os
from pathlib import Path

from typing import Optional

from conductor.client.configuration.configuration import Configuration

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(
        __name__
    )
)


def get_default_temporary_folder() -> str:
    return f"{Path.home()!s}/tmp/"


class MetricsSettings:
    def __init__(
            self,
            directory: Optional[str] = None,
            file_name: str = "metrics.log",
            update_interval: float = 0.1,
            http_port: Optional[int] = None,
            clean_directory: bool = True):
        """
        Configure metrics collection settings.

        Args:
            directory: Directory for storing multiprocess metrics .db files
            file_name: Name of the metrics output file (only used when http_port is None)
            update_interval: How often to update metrics (in seconds)
            http_port: Optional HTTP port to expose metrics endpoint for Prometheus scraping.
                      If specified:
                      - An HTTP server will be started on this port
                      - Metrics served from memory at http://localhost:{port}/metrics
                      - No file will be written (metrics kept in memory only)
                      If None:
                      - Metrics will be written to file at {directory}/{file_name}
                      - No HTTP server will be started
            clean_directory: If True (default), remove stale prometheus_client
                      .db files from the directory on init.  Without this,
                      metric names from previous configurations persist in the
                      multiprocess directory and appear in /metrics output.
        """
        if directory is None:
            directory = get_default_temporary_folder()
        self.__set_dir(directory)
        self.file_name = file_name
        self.update_interval = update_interval
        self.http_port = http_port
        if clean_directory:
            self._clean_stale_db_files()

    def __set_dir(self, dir: str) -> None:
        if not os.path.isdir(dir):
            try:
                os.mkdir(dir)
            except Exception as e:
                logger.warning(
                    "Failed to create metrics temporary folder, reason: %s", e)

        self.directory = dir

    def _clean_stale_db_files(self) -> None:
        """Remove leftover prometheus_client multiprocess .db files."""
        import glob
        pattern = os.path.join(self.directory, "*.db")
        for path in glob.glob(pattern):
            try:
                os.remove(path)
            except Exception as e:
                logger.debug("Could not remove stale metrics db file %s: %s", path, e)
