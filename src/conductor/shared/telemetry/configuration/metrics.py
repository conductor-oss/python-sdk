from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_default_temporary_folder() -> str:
    return f"{Path.home()!s}/tmp/"


class MetricsSettings:
    """
    Async metrics settings adapter for Orkes Conductor Asyncio Client.
    
    This adapter provides configuration for metrics collection in async environments,
    following the same pattern as other async adapters in the asyncio client.
    """
    
    def __init__(
            self,
            directory: Optional[str] = None,
            file_name: str = "metrics.log",
            update_interval: float = 0.1):
        """
        Initialize metrics settings.
        
        Parameters:
        -----------
        directory : str, optional
            Directory for storing metrics files. If None, uses default temp folder.
        file_name : str
            Name of the metrics file. Default is "metrics.log".
        update_interval : float
            Interval in seconds for updating metrics. Default is 0.1 seconds.
        """
        if directory is None:
            directory = get_default_temporary_folder()
        self.__set_dir(directory)
        self.file_name = file_name
        self.update_interval = update_interval

    def __set_dir(self, dir: str) -> None:
        """Set and create the metrics directory if it doesn't exist."""
        if not os.path.isdir(dir):
            try:
                os.makedirs(dir, exist_ok=True)
            except Exception as e:
                logger.warning(
                    "Failed to create metrics temporary folder, reason: %s", e)

        self.directory = dir 
