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


CANONICAL_SUBDIR = "canonical"


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name, "")
    if not value:
        return default
    return value.strip().lower() in ("true", "1", "yes")


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

        The ``WORKER_CANONICAL_METRICS`` env var is read at construction time
        to decide whether ``.db`` files go in *directory* (legacy) or in a
        ``canonical/`` subdirectory (canonical mode).  Set the env var before
        creating this object.

        Args:
            directory: Base directory for storing multiprocess metrics .db files.
                      Legacy metrics use this directory directly (unchanged from
                      prior releases).  Canonical metrics use a ``canonical/``
                      subdirectory so that switching implementations never
                      produces stale metric names.
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
        self._subdir: str = (
            CANONICAL_SUBDIR
            if _env_bool("WORKER_CANONICAL_METRICS", False)
            else ""
        )

    @property
    def is_canonical(self) -> bool:
        return self._subdir == CANONICAL_SUBDIR

    @property
    def metrics_directory(self) -> str:
        """Full path where .db files live (base directory + optional subdir).

        Legacy leaves the subdirectory empty (base directory unchanged from
        prior releases); canonical sets it to ``"canonical"`` to avoid stale
        metric-name collisions.  Resolved eagerly at construction time from
        the ``WORKER_CANONICAL_METRICS`` env var.
        """
        if self._subdir:
            return os.path.join(self.directory, self._subdir)
        return self.directory

    def clean_metrics_directory(self) -> None:
        """Prepare the shared metrics directory exactly once, before any worker
        writes to it.

        This is the destructive counterpart to metrics collection and must be
        invoked only by the process that owns the worker lifecycle (i.e. the
        parent that spawns workers, via ``TaskHandler``), never by a spawned
        worker.  A worker cannot know whether sibling processes are already
        live and sharing this directory, so it must never wipe ``.db`` files.

        Ensures the directory exists, then applies the configured cleanup:
          - ``clean_directory``: remove all prometheus_client ``.db`` files.
          - ``clean_dead_pids``: remove only ``.db`` files whose owning PID no
            longer exists.
        Both are no-ops when their respective flag is ``False``.
        """
        os.makedirs(self.metrics_directory, exist_ok=True)
        if self.clean_directory:
            self._clean_stale_db_files()
        if self.clean_dead_pids:
            self._clean_dead_pid_files()

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
        pattern = os.path.join(self.metrics_directory, "*.db")
        for path in glob.glob(pattern):
            try:
                os.remove(path)
            except Exception as e:
                logger.debug("Could not remove stale metrics db file %s: %s", path, e)

    def _clean_dead_pid_files(self) -> None:
        """Remove .db files whose owning PID no longer exists."""
        import glob
        import re
        pattern = os.path.join(self.metrics_directory, "*.db")
        for path in glob.glob(pattern):
            match = re.search(r'_(\d+)\.db$', os.path.basename(path))
            if not match:
                continue
            pid = int(match.group(1))
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                # ESRCH: no process owns this PID -> safe to remove its db file.
                try:
                    os.remove(path)
                    logger.debug("Removed dead-pid metrics file %s (pid %d)", path, pid)
                except OSError as e:
                    logger.debug("Could not remove dead-pid metrics db file %s: %s", path, e)
            except OSError as e:
                # Any non-ESRCH probe failure (commonly EPERM: the process is
                # alive but owned by another user) -> keep the file; deleting it
                # could corrupt a live worker's metrics in a shared directory.
                logger.debug(
                    "Keeping metrics db file %s; pid %d probe returned a "
                    "non-ProcessLookupError OSError (process likely alive): %s",
                    path, pid, e,
                )
                continue
