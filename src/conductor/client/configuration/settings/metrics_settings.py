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
            clean_directory: bool = False,
            clean_dead_pids: bool = False):
        """
        Configure metrics collection settings.

        Args:
            directory: Base directory for storing multiprocess metrics .db files.
                      The factory (``create_metrics_collector``) appends a
                      collector-type subdirectory (``legacy/`` or ``canonical/``)
                      so that switching implementations never produces stale
                      metric names.
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
            clean_directory: If True, remove all prometheus_client .db files from
                      the metrics directory when the collector is created.  Only
                      safe when no other live process shares the same directory.
                      Defaults to False.
            clean_dead_pids: If True, remove .db files whose owning PID no
                      longer exists.  Safer than ``clean_directory`` in shared
                      environments.  Defaults to False.
        """
        if directory is None:
            directory = get_default_temporary_folder()
        self.__set_dir(directory)
        self.file_name = file_name
        self.update_interval = update_interval
        self.http_port = http_port
        self.clean_directory = clean_directory
        self.clean_dead_pids = clean_dead_pids

    def __set_dir(self, dir: str) -> None:
        if not os.path.isdir(dir):
            try:
                os.mkdir(dir)
            except Exception as e:
                logger.warning(
                    "Failed to create metrics temporary folder, reason: %s", e)

        self.directory = dir

    def _clean_stale_db_files(self) -> None:
        """Remove all prometheus_client multiprocess .db files."""
        import glob
        pattern = os.path.join(self.directory, "*.db")
        for path in glob.glob(pattern):
            try:
                os.remove(path)
            except Exception as e:
                logger.debug("Could not remove stale metrics db file %s: %s", path, e)

    def _clean_dead_pid_files(self) -> None:
        """Remove .db files whose owning PID no longer exists."""
        import glob
        import re
        pattern = os.path.join(self.directory, "*.db")
        for path in glob.glob(pattern):
            match = re.search(r'_(\d+)\.db$', os.path.basename(path))
            if not match:
                continue
            pid = int(match.group(1))
            try:
                os.kill(pid, 0) # Check if the process is still running (0 = simple probe, doesn't send a signal), if it isn't we'll get a ProcessLookupError which is an OSError
            except OSError:
                try:
                    os.remove(path)
                    logger.debug("Removed dead-pid metrics file %s (pid %d)", path, pid)
                except Exception as e:
                    logger.debug("Could not remove dead-pid metrics db file %s: %s", path, e)
