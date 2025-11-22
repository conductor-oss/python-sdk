"""
Unit tests for EventDispatcher
"""

import asyncio
import unittest
from conductor.client.event.event_dispatcher import EventDispatcher
from conductor.client.event.task_runner_events import (
    TaskRunnerEvent,
    PollStarted,
    PollCompleted,
    TaskExecutionCompleted
)


class TestEventDispatcher(unittest.IsolatedAsyncioTestCase):
    """Test EventDispatcher functionality"""

    def setUp(self):
        """Create a fresh event dispatcher for each test"""
        self.dispatcher = EventDispatcher[TaskRunnerEvent]()
        self.events_received = []

    async def test_register_and_publish_event(self):
        """Test basic event registration and publishing"""
        # Register listener
        def on_poll_started(event: PollStarted):
            self.events_received.append(event)

        await self.dispatcher.register(PollStarted, on_poll_started)

        # Publish event
        event = PollStarted(
            task_type="test_task",
            worker_id="worker_1",
            poll_count=5
        )
        self.dispatcher.publish(event)

        # Give event loop time to process
        await asyncio.sleep(0.01)

        # Verify event was received
        self.assertEqual(len(self.events_received), 1)
        self.assertEqual(self.events_received[0].task_type, "test_task")
        self.assertEqual(self.events_received[0].worker_id, "worker_1")
        self.assertEqual(self.events_received[0].poll_count, 5)

    async def test_multiple_listeners_same_event(self):
        """Test multiple listeners can receive the same event"""
        received_1 = []
        received_2 = []

        def listener_1(event: PollStarted):
            received_1.append(event)

        def listener_2(event: PollStarted):
            received_2.append(event)

        await self.dispatcher.register(PollStarted, listener_1)
        await self.dispatcher.register(PollStarted, listener_2)

        event = PollStarted(task_type="test", worker_id="w1", poll_count=1)
        self.dispatcher.publish(event)

        await asyncio.sleep(0.01)

        self.assertEqual(len(received_1), 1)
        self.assertEqual(len(received_2), 1)
        self.assertEqual(received_1[0].task_type, "test")
        self.assertEqual(received_2[0].task_type, "test")

    async def test_different_event_types(self):
        """Test dispatcher routes different event types correctly"""
        poll_events = []
        exec_events = []

        def on_poll(event: PollStarted):
            poll_events.append(event)

        def on_exec(event: TaskExecutionCompleted):
            exec_events.append(event)

        await self.dispatcher.register(PollStarted, on_poll)
        await self.dispatcher.register(TaskExecutionCompleted, on_exec)

        # Publish different event types
        self.dispatcher.publish(PollStarted(task_type="t1", worker_id="w1", poll_count=1))
        self.dispatcher.publish(TaskExecutionCompleted(
            task_type="t1",
            task_id="task123",
            worker_id="w1",
            workflow_instance_id="wf123",
            duration_ms=100.0
        ))

        await asyncio.sleep(0.01)

        # Verify each listener only received its event type
        self.assertEqual(len(poll_events), 1)
        self.assertEqual(len(exec_events), 1)
        self.assertIsInstance(poll_events[0], PollStarted)
        self.assertIsInstance(exec_events[0], TaskExecutionCompleted)

    async def test_unregister_listener(self):
        """Test listener unregistration"""
        events = []

        def listener(event: PollStarted):
            events.append(event)

        await self.dispatcher.register(PollStarted, listener)

        # Publish first event
        self.dispatcher.publish(PollStarted(task_type="t1", worker_id="w1", poll_count=1))
        await asyncio.sleep(0.01)
        self.assertEqual(len(events), 1)

        # Unregister and publish second event
        await self.dispatcher.unregister(PollStarted, listener)
        self.dispatcher.publish(PollStarted(task_type="t2", worker_id="w2", poll_count=2))
        await asyncio.sleep(0.01)

        # Should still only have one event
        self.assertEqual(len(events), 1)

    async def test_has_listeners(self):
        """Test has_listeners check"""
        self.assertFalse(self.dispatcher.has_listeners(PollStarted))

        def listener(event: PollStarted):
            pass

        await self.dispatcher.register(PollStarted, listener)
        self.assertTrue(self.dispatcher.has_listeners(PollStarted))

        await self.dispatcher.unregister(PollStarted, listener)
        self.assertFalse(self.dispatcher.has_listeners(PollStarted))

    async def test_listener_count(self):
        """Test listener_count method"""
        self.assertEqual(self.dispatcher.listener_count(PollStarted), 0)

        def listener1(event: PollStarted):
            pass

        def listener2(event: PollStarted):
            pass

        await self.dispatcher.register(PollStarted, listener1)
        self.assertEqual(self.dispatcher.listener_count(PollStarted), 1)

        await self.dispatcher.register(PollStarted, listener2)
        self.assertEqual(self.dispatcher.listener_count(PollStarted), 2)

        await self.dispatcher.unregister(PollStarted, listener1)
        self.assertEqual(self.dispatcher.listener_count(PollStarted), 1)

    async def test_async_listener(self):
        """Test async listener functions"""
        events = []

        async def async_listener(event: PollCompleted):
            await asyncio.sleep(0.001)  # Simulate async work
            events.append(event)

        await self.dispatcher.register(PollCompleted, async_listener)

        event = PollCompleted(task_type="test", duration_ms=100.0, tasks_received=1)
        self.dispatcher.publish(event)

        # Give more time for async listener
        await asyncio.sleep(0.02)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].task_type, "test")

    async def test_listener_exception_isolation(self):
        """Test that exception in one listener doesn't affect others"""
        good_events = []

        def bad_listener(event: PollStarted):
            raise Exception("Intentional error")

        def good_listener(event: PollStarted):
            good_events.append(event)

        await self.dispatcher.register(PollStarted, bad_listener)
        await self.dispatcher.register(PollStarted, good_listener)

        event = PollStarted(task_type="test", worker_id="w1", poll_count=1)
        self.dispatcher.publish(event)

        await asyncio.sleep(0.01)

        # Good listener should still receive the event
        self.assertEqual(len(good_events), 1)


if __name__ == '__main__':
    unittest.main()
