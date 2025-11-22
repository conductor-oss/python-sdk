"""
Event dispatcher for publishing and routing events to listeners.

This module provides the core event routing infrastructure, matching the
Java SDK's EventDispatcher implementation with both sync and async support.
"""

import asyncio
import inspect
import logging
import threading
from collections import defaultdict
from copy import copy
from typing import Callable, Dict, Generic, List, Type, TypeVar

from conductor.client.configuration.configuration import Configuration
from conductor.client.event.conductor_event import ConductorEvent

logger = logging.getLogger(
    Configuration.get_logging_formatted_name(__name__)
)

T = TypeVar('T', bound=ConductorEvent)


class EventDispatcher(Generic[T]):
    """
    Generic event dispatcher that manages listener registration and event publishing.

    This class provides thread-safe event routing with asynchronous event publishing
    to ensure non-blocking behavior. It matches the Java SDK's EventDispatcher design.

    Type Parameters:
        T: The base event type this dispatcher handles (must extend ConductorEvent)

    Example:
        >>> from conductor.client.event import TaskRunnerEvent, PollStarted
        >>> dispatcher = EventDispatcher[TaskRunnerEvent]()
        >>>
        >>> def on_poll_started(event: PollStarted):
        ...     print(f"Poll started for {event.task_type}")
        >>>
        >>> dispatcher.register(PollStarted, on_poll_started)
        >>> dispatcher.publish(PollStarted(task_type="my_task", worker_id="worker1", poll_count=1))
    """

    def __init__(self):
        """Initialize the event dispatcher with empty listener registry."""
        self._listeners: Dict[Type[T], List[Callable[[T], None]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def register(self, event_type: Type[T], listener: Callable[[T], None]) -> None:
        """
        Register a listener for a specific event type.

        The listener will be called asynchronously whenever an event of the specified
        type is published. Multiple listeners can be registered for the same event type.

        Args:
            event_type: The class of events to listen for
            listener: Callback function that accepts the event as parameter

        Example:
            >>> async def setup_listener():
            ...     await dispatcher.register(PollStarted, handle_poll_started)
        """
        async with self._lock:
            if listener not in self._listeners[event_type]:
                self._listeners[event_type].append(listener)
                logger.debug(
                    f"Registered listener for event type: {event_type.__name__}"
                )

    async def unregister(self, event_type: Type[T], listener: Callable[[T], None]) -> None:
        """
        Unregister a listener for a specific event type.

        Args:
            event_type: The class of events to stop listening for
            listener: The callback function to remove

        Example:
            >>> async def cleanup_listener():
            ...     await dispatcher.unregister(PollStarted, handle_poll_started)
        """
        async with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(listener)
                    logger.debug(
                        f"Unregistered listener for event type: {event_type.__name__}"
                    )
                    if not self._listeners[event_type]:
                        del self._listeners[event_type]
                except ValueError:
                    logger.warning(
                        f"Attempted to unregister non-existent listener for {event_type.__name__}"
                    )

    def publish(self, event: T) -> None:
        """
        Publish an event to all registered listeners asynchronously.

        This method is non-blocking - it schedules the event delivery to listeners
        without waiting for them to complete. This ensures that event publishing
        does not impact the performance of the calling code.

        If a listener raises an exception, it is logged but does not affect other listeners.

        Args:
            event: The event instance to publish

        Example:
            >>> dispatcher.publish(PollStarted(
            ...     task_type="my_task",
            ...     worker_id="worker1",
            ...     poll_count=1
            ... ))
        """
        # Get listeners without lock for minimal blocking
        listeners = copy(self._listeners.get(type(event), []))

        if not listeners:
            return

        # Dispatch asynchronously to avoid blocking the caller
        asyncio.create_task(self._dispatch_to_listeners(event, listeners))

    async def _dispatch_to_listeners(self, event: T, listeners: List[Callable[[T], None]]) -> None:
        """
        Internal method to dispatch an event to all listeners.

        Each listener is called in sequence. If a listener raises an exception,
        it is logged and execution continues with the next listener.

        Args:
            event: The event to dispatch
            listeners: List of listener callbacks to invoke
        """
        for listener in listeners:
            try:
                # Call listener - if it's a coroutine, await it
                result = listener(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    f"Error in event listener for {type(event).__name__}: {e}",
                    exc_info=True
                )

    def has_listeners(self, event_type: Type[T]) -> bool:
        """
        Check if there are any listeners registered for an event type.

        Args:
            event_type: The event type to check

        Returns:
            True if at least one listener is registered, False otherwise

        Example:
            >>> if dispatcher.has_listeners(PollStarted):
            ...     dispatcher.publish(event)
        """
        return event_type in self._listeners and len(self._listeners[event_type]) > 0

    def listener_count(self, event_type: Type[T]) -> int:
        """
        Get the number of listeners registered for an event type.

        Args:
            event_type: The event type to check

        Returns:
            Number of registered listeners

        Example:
            >>> count = dispatcher.listener_count(PollStarted)
            >>> print(f"There are {count} listeners for PollStarted")
        """
        return len(self._listeners.get(event_type, []))
