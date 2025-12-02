"""
Integration tests for worker configuration with @worker_task decorator
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import Mock, patch

# Prevent actual task handler initialization
sys.modules['conductor.client.automator.task_handler'] = Mock()

from conductor.client.worker.worker_task import worker_task
from conductor.client.worker.worker_config import resolve_worker_config


class TestWorkerConfigWithDecorator(unittest.TestCase):
    """Test worker configuration resolution with @worker_task decorator"""

    def setUp(self):
        """Save original environment before each test"""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment after each test"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_decorator_values_used_without_env_overrides(self):
        """Test decorator values are used when no environment overrides"""
        config = resolve_worker_config(
            worker_name='process_order',
            poll_interval=2000,
            domain='orders',
            worker_id='order-worker-1',
            thread_count=3,
            register_task_def=True,
            poll_timeout=250,
            lease_extend_enabled=False
        )

        self.assertEqual(config['poll_interval'], 2000)
        self.assertEqual(config['domain'], 'orders')
        self.assertEqual(config['worker_id'], 'order-worker-1')
        self.assertEqual(config['thread_count'], 3)
        self.assertTrue(config['register_task_def'])
        self.assertEqual(config['poll_timeout'], 250)
        self.assertFalse(config['lease_extend_enabled'])

    def test_global_env_overrides_decorator_values(self):
        """Test global environment variables override decorator values"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.all.thread_count'] = '10'

        config = resolve_worker_config(
            worker_name='process_order',
            poll_interval=2000,
            domain='orders',
            thread_count=3
        )

        self.assertEqual(config['poll_interval'], 500.0)
        self.assertEqual(config['domain'], 'orders')  # Not overridden
        self.assertEqual(config['thread_count'], 10)

    def test_worker_specific_env_overrides_all(self):
        """Test worker-specific env vars override both decorator and global"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.all.domain'] = 'staging'
        os.environ['conductor.worker.process_order.poll_interval'] = '100'
        os.environ['conductor.worker.process_order.domain'] = 'production'

        config = resolve_worker_config(
            worker_name='process_order',
            poll_interval=2000,
            domain='dev'
        )

        # Worker-specific wins
        self.assertEqual(config['poll_interval'], 100.0)
        self.assertEqual(config['domain'], 'production')

    def test_multiple_workers_independent_configs(self):
        """Test multiple workers can have independent configurations"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.high_priority.thread_count'] = '20'
        os.environ['conductor.worker.low_priority.thread_count'] = '1'

        high_priority_config = resolve_worker_config(
            worker_name='high_priority',
            poll_interval=1000,
            thread_count=5
        )

        low_priority_config = resolve_worker_config(
            worker_name='low_priority',
            poll_interval=1000,
            thread_count=5
        )

        normal_config = resolve_worker_config(
            worker_name='normal',
            poll_interval=1000,
            thread_count=5
        )

        # All get global poll_interval
        self.assertEqual(high_priority_config['poll_interval'], 500.0)
        self.assertEqual(low_priority_config['poll_interval'], 500.0)
        self.assertEqual(normal_config['poll_interval'], 500.0)

        # But different thread counts
        self.assertEqual(high_priority_config['thread_count'], 20)
        self.assertEqual(low_priority_config['thread_count'], 1)
        self.assertEqual(normal_config['thread_count'], 5)

    def test_production_like_scenario(self):
        """Test production-like configuration scenario"""
        # Global production settings
        os.environ['conductor.worker.all.domain'] = 'production'
        os.environ['conductor.worker.all.poll_interval'] = '250'
        os.environ['conductor.worker.all.lease_extend_enabled'] = 'true'

        # Critical worker needs more resources
        os.environ['conductor.worker.process_payment.thread_count'] = '50'
        os.environ['conductor.worker.process_payment.poll_interval'] = '50'

        # Regular worker
        order_config = resolve_worker_config(
            worker_name='process_order',
            poll_interval=1000,
            domain='dev',
            thread_count=5,
            lease_extend_enabled=False
        )

        # Critical worker
        payment_config = resolve_worker_config(
            worker_name='process_payment',
            poll_interval=1000,
            domain='dev',
            thread_count=5,
            lease_extend_enabled=False
        )

        # Regular worker - uses global overrides
        self.assertEqual(order_config['domain'], 'production')
        self.assertEqual(order_config['poll_interval'], 250.0)
        self.assertEqual(order_config['thread_count'], 5)  # No override
        self.assertTrue(order_config['lease_extend_enabled'])

        # Critical worker - uses worker-specific where available
        self.assertEqual(payment_config['domain'], 'production')  # Global
        self.assertEqual(payment_config['poll_interval'], 50.0)   # Worker-specific
        self.assertEqual(payment_config['thread_count'], 50)      # Worker-specific
        self.assertTrue(payment_config['lease_extend_enabled'])   # Global

    def test_development_debug_scenario(self):
        """Test development environment with debug settings"""
        os.environ['conductor.worker.all.poll_interval'] = '10000'  # Very slow
        os.environ['conductor.worker.all.thread_count'] = '1'       # Single-threaded
        os.environ['conductor.worker.all.poll_timeout'] = '5000'    # Long timeout

        config = resolve_worker_config(
            worker_name='debug_worker',
            poll_interval=100,
            thread_count=10,
            poll_timeout=100
        )

        self.assertEqual(config['poll_interval'], 10000.0)
        self.assertEqual(config['thread_count'], 1)
        self.assertEqual(config['poll_timeout'], 5000)

    def test_partial_override_scenario(self):
        """Test scenario where only some properties are overridden"""
        # Only override domain, leave rest as code defaults
        os.environ['conductor.worker.all.domain'] = 'staging'

        config = resolve_worker_config(
            worker_name='test_worker',
            poll_interval=750,
            domain='dev',
            thread_count=8,
            poll_timeout=150,
            lease_extend_enabled=True
        )

        # Only domain changes
        self.assertEqual(config['domain'], 'staging')

        # Everything else from code
        self.assertEqual(config['poll_interval'], 750)
        self.assertEqual(config['thread_count'], 8)
        self.assertEqual(config['poll_timeout'], 150)
        self.assertTrue(config['lease_extend_enabled'])

    def test_canary_deployment_scenario(self):
        """Test canary deployment where one worker uses different config"""
        # Most workers use production config
        os.environ['conductor.worker.all.domain'] = 'production'
        os.environ['conductor.worker.all.poll_interval'] = '200'

        # Canary worker uses staging
        os.environ['conductor.worker.canary_worker.domain'] = 'staging'

        prod_config = resolve_worker_config(
            worker_name='prod_worker',
            poll_interval=1000,
            domain='dev'
        )

        canary_config = resolve_worker_config(
            worker_name='canary_worker',
            poll_interval=1000,
            domain='dev'
        )

        # Production worker
        self.assertEqual(prod_config['domain'], 'production')
        self.assertEqual(prod_config['poll_interval'], 200.0)

        # Canary worker - different domain, same poll_interval
        self.assertEqual(canary_config['domain'], 'staging')
        self.assertEqual(canary_config['poll_interval'], 200.0)


if __name__ == '__main__':
    unittest.main()
