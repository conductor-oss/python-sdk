"""
Base event class for all Conductor events.

This module provides the foundation for the event-driven observability system,
matching the architecture of the Java SDK's event system.
"""

from datetime import datetime


class ConductorEvent:
    """
    Base class for all Conductor events.

    All events are immutable (frozen=True) to ensure thread-safety and
    prevent accidental modification after creation.

    Note: This is not a dataclass itself to avoid inheritance issues with
    default arguments. All child classes should be dataclasses and include
    a timestamp field with default_factory.

    Attributes:
        timestamp: UTC timestamp when the event was created
    """
    pass
