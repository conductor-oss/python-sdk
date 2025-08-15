from __future__ import annotations

from abc import ABC, abstractmethod


class IntegrationConfig(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        pass
