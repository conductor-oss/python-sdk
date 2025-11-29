"""
Tests for worker configuration hierarchical resolution
"""

import os
import unittest
from unittest.mock import patch

from conductor.client.worker.worker_config import (
    resolve_worker_config,
    get_worker_config_summary,
    _get_env_value,
    _parse_env_value
)


class TestWorkerConfig(unittest.TestCase):
    """Test hierarchical worker configuration resolution"""

    def setUp(self):
        """Save original environment before each test"""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment after each test"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_parse_env_value_boolean_true(self):
        """Test parsing boolean true values"""
        self.assertTrue(_parse_env_value('true', bool))
        self.assertTrue(_parse_env_value('True', bool))
        self.assertTrue(_parse_env_value('TRUE', bool))
        self.assertTrue(_parse_env_value('1', bool))
        self.assertTrue(_parse_env_value('yes', bool))
        self.assertTrue(_parse_env_value('YES', bool))
        self.assertTrue(_parse_env_value('on', bool))

    def test_parse_env_value_boolean_false(self):
        """Test parsing boolean false values"""
        self.assertFalse(_parse_env_value('false', bool))
        self.assertFalse(_parse_env_value('False', bool))
        self.assertFalse(_parse_env_value('FALSE', bool))
        self.assertFalse(_parse_env_value('0', bool))
        self.assertFalse(_parse_env_value('no', bool))

    def test_parse_env_value_integer(self):
        """Test parsing integer values"""
        self.assertEqual(_parse_env_value('42', int), 42)
        self.assertEqual(_parse_env_value('0', int), 0)
        self.assertEqual(_parse_env_value('-10', int), -10)

    def test_parse_env_value_float(self):
        """Test parsing float values"""
        self.assertEqual(_parse_env_value('3.14', float), 3.14)
        self.assertEqual(_parse_env_value('1000.5', float), 1000.5)

    def test_parse_env_value_string(self):
        """Test parsing string values"""
        self.assertEqual(_parse_env_value('hello', str), 'hello')
        self.assertEqual(_parse_env_value('production', str), 'production')

    def test_code_level_defaults_only(self):
        """Test configuration uses code-level defaults when no env vars set"""
        config = resolve_worker_config(
            worker_name='test_worker',
            poll_interval=1000,
            domain='dev',
            worker_id='worker-1',
            thread_count=5,
            register_task_def=True,
            poll_timeout=200,
            lease_extend_enabled=False
        )

        self.assertEqual(config['poll_interval'], 1000)
        self.assertEqual(config['domain'], 'dev')
        self.assertEqual(config['worker_id'], 'worker-1')
        self.assertEqual(config['thread_count'], 5)
        self.assertEqual(config['register_task_def'], True)
        self.assertEqual(config['poll_timeout'], 200)
        self.assertEqual(config['lease_extend_enabled'], False)

    def test_global_worker_override(self):
        """Test global worker config overrides code-level defaults"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.all.domain'] = 'staging'
        os.environ['conductor.worker.all.thread_count'] = '10'

        config = resolve_worker_config(
            worker_name='test_worker',
            poll_interval=1000,
            domain='dev',
            thread_count=5
        )

        self.assertEqual(config['poll_interval'], 500.0)
        self.assertEqual(config['domain'], 'staging')
        self.assertEqual(config['thread_count'], 10)

    def test_worker_specific_override(self):
        """Test worker-specific config overrides global config"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.all.domain'] = 'staging'
        os.environ['conductor.worker.process_order.poll_interval'] = '250'
        os.environ['conductor.worker.process_order.domain'] = 'production'

        config = resolve_worker_config(
            worker_name='process_order',
            poll_interval=1000,
            domain='dev'
        )

        # Worker-specific overrides should win
        self.assertEqual(config['poll_interval'], 250.0)
        self.assertEqual(config['domain'], 'production')

    def test_hierarchy_all_three_levels(self):
        """Test complete hierarchy: code -> global -> worker-specific"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.all.thread_count'] = '10'
        os.environ['conductor.worker.my_task.domain'] = 'production'

        config = resolve_worker_config(
            worker_name='my_task',
            poll_interval=1000,  # Overridden by global
            domain='dev',        # Overridden by worker-specific
            thread_count=5,      # Overridden by global
            worker_id='w1'       # No override, uses code value
        )

        self.assertEqual(config['poll_interval'], 500.0)  # From global
        self.assertEqual(config['domain'], 'production')  # From worker-specific
        self.assertEqual(config['thread_count'], 10)      # From global
        self.assertEqual(config['worker_id'], 'w1')       # From code

    def test_boolean_properties_from_env(self):
        """Test boolean properties can be overridden via env vars"""
        os.environ['conductor.worker.all.register_task_def'] = 'true'
        os.environ['conductor.worker.test_worker.lease_extend_enabled'] = 'false'

        config = resolve_worker_config(
            worker_name='test_worker',
            register_task_def=False,
            lease_extend_enabled=True
        )

        self.assertTrue(config['register_task_def'])
        self.assertFalse(config['lease_extend_enabled'])

    def test_integer_properties_from_env(self):
        """Test integer properties can be overridden via env vars"""
        os.environ['conductor.worker.all.thread_count'] = '20'
        os.environ['conductor.worker.test_worker.poll_timeout'] = '300'

        config = resolve_worker_config(
            worker_name='test_worker',
            thread_count=5,
            poll_timeout=100
        )

        self.assertEqual(config['thread_count'], 20)
        self.assertEqual(config['poll_timeout'], 300)

    def test_none_values_preserved(self):
        """Test None values are preserved when no overrides exist"""
        config = resolve_worker_config(
            worker_name='test_worker',
            poll_interval=None,
            domain=None,
            worker_id=None
        )

        self.assertIsNone(config['poll_interval'])
        self.assertIsNone(config['domain'])
        self.assertIsNone(config['worker_id'])

    def test_partial_override_preserves_others(self):
        """Test that only overridden properties change, others remain unchanged"""
        os.environ['conductor.worker.test_worker.domain'] = 'production'

        config = resolve_worker_config(
            worker_name='test_worker',
            poll_interval=1000,
            domain='dev',
            thread_count=5
        )

        self.assertEqual(config['poll_interval'], 1000)  # Unchanged
        self.assertEqual(config['domain'], 'production')  # Changed
        self.assertEqual(config['thread_count'], 5)       # Unchanged

    def test_multiple_workers_different_configs(self):
        """Test different workers can have different overrides"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.worker_a.domain'] = 'prod-a'
        os.environ['conductor.worker.worker_b.domain'] = 'prod-b'

        config_a = resolve_worker_config(
            worker_name='worker_a',
            poll_interval=1000,
            domain='dev'
        )

        config_b = resolve_worker_config(
            worker_name='worker_b',
            poll_interval=1000,
            domain='dev'
        )

        # Both get global poll_interval
        self.assertEqual(config_a['poll_interval'], 500.0)
        self.assertEqual(config_b['poll_interval'], 500.0)

        # But different domains
        self.assertEqual(config_a['domain'], 'prod-a')
        self.assertEqual(config_b['domain'], 'prod-b')

    def test_get_env_value_worker_specific_priority(self):
        """Test _get_env_value prioritizes worker-specific over global"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.my_task.poll_interval'] = '250'

        value = _get_env_value('my_task', 'poll_interval', float)
        self.assertEqual(value, 250.0)

    def test_get_env_value_returns_none_when_not_found(self):
        """Test _get_env_value returns None when property not in env"""
        value = _get_env_value('my_task', 'nonexistent_property', str)
        self.assertIsNone(value)

    def test_config_summary_generation(self):
        """Test configuration summary generation"""
        os.environ['conductor.worker.all.poll_interval'] = '500'
        os.environ['conductor.worker.my_task.domain'] = 'production'

        config = resolve_worker_config(
            worker_name='my_task',
            poll_interval=1000,
            domain='dev',
            thread_count=5
        )

        summary = get_worker_config_summary('my_task', config)

        self.assertIn("Worker 'my_task' configuration:", summary)
        self.assertIn('poll_interval', summary)
        self.assertIn('conductor.worker.all.poll_interval', summary)
        self.assertIn('domain', summary)
        self.assertIn('conductor.worker.my_task.domain', summary)
        self.assertIn('thread_count', summary)
        self.assertIn('from code', summary)

    def test_empty_string_env_value_treated_as_set(self):
        """Test empty string env values are treated as set (not None)"""
        os.environ['conductor.worker.test_worker.domain'] = ''

        config = resolve_worker_config(
            worker_name='test_worker',
            domain='dev'
        )

        # Empty string should override 'dev'
        self.assertEqual(config['domain'], '')

    def test_all_properties_resolvable(self):
        """Test all worker properties can be resolved via hierarchy"""
        os.environ['conductor.worker.all.poll_interval'] = '100'
        os.environ['conductor.worker.all.domain'] = 'global-domain'
        os.environ['conductor.worker.all.worker_id'] = 'global-worker'
        os.environ['conductor.worker.all.thread_count'] = '15'
        os.environ['conductor.worker.all.register_task_def'] = 'true'
        os.environ['conductor.worker.all.poll_timeout'] = '500'
        os.environ['conductor.worker.all.lease_extend_enabled'] = 'false'

        config = resolve_worker_config(
            worker_name='test_worker',
            poll_interval=1000,
            domain='dev',
            worker_id='w1',
            thread_count=1,
            register_task_def=False,
            poll_timeout=100,
            lease_extend_enabled=True
        )

        # All should be overridden by global config
        self.assertEqual(config['poll_interval'], 100.0)
        self.assertEqual(config['domain'], 'global-domain')
        self.assertEqual(config['worker_id'], 'global-worker')
        self.assertEqual(config['thread_count'], 15)
        self.assertTrue(config['register_task_def'])
        self.assertEqual(config['poll_timeout'], 500)
        self.assertFalse(config['lease_extend_enabled'])


class TestWorkerConfigIntegration(unittest.TestCase):
    """Integration tests for worker configuration in realistic scenarios"""

    def setUp(self):
        """Save original environment before each test"""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment after each test"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_production_deployment_scenario(self):
        """Test realistic production deployment with env-based configuration"""
        # Simulate production environment variables
        os.environ['conductor.worker.all.domain'] = 'production'
        os.environ['conductor.worker.all.poll_interval'] = '250'
        os.environ['conductor.worker.all.lease_extend_enabled'] = 'true'

        # High-priority worker gets special treatment
        os.environ['conductor.worker.critical_task.thread_count'] = '20'
        os.environ['conductor.worker.critical_task.poll_interval'] = '100'

        # Regular worker
        regular_config = resolve_worker_config(
            worker_name='regular_task',
            poll_interval=1000,
            domain='dev',
            thread_count=5,
            lease_extend_enabled=False
        )

        # Critical worker
        critical_config = resolve_worker_config(
            worker_name='critical_task',
            poll_interval=1000,
            domain='dev',
            thread_count=5,
            lease_extend_enabled=False
        )

        # Regular worker uses global overrides
        self.assertEqual(regular_config['domain'], 'production')
        self.assertEqual(regular_config['poll_interval'], 250.0)
        self.assertEqual(regular_config['thread_count'], 5)  # No global override
        self.assertTrue(regular_config['lease_extend_enabled'])

        # Critical worker uses worker-specific overrides where set
        self.assertEqual(critical_config['domain'], 'production')  # From global
        self.assertEqual(critical_config['poll_interval'], 100.0)  # Worker-specific
        self.assertEqual(critical_config['thread_count'], 20)      # Worker-specific
        self.assertTrue(critical_config['lease_extend_enabled'])   # From global

    def test_development_with_debug_settings(self):
        """Test development environment with debug-friendly settings"""
        os.environ['conductor.worker.all.poll_interval'] = '5000'  # Slower polling
        os.environ['conductor.worker.all.poll_timeout'] = '1000'   # Longer timeout
        os.environ['conductor.worker.all.thread_count'] = '1'       # Single-threaded

        config = resolve_worker_config(
            worker_name='dev_task',
            poll_interval=100,
            poll_timeout=100,
            thread_count=10
        )

        self.assertEqual(config['poll_interval'], 5000.0)
        self.assertEqual(config['poll_timeout'], 1000)
        self.assertEqual(config['thread_count'], 1)

    def test_staging_environment_selective_override(self):
        """Test staging environment with selective overrides"""
        # Only override domain for staging, keep other settings from code
        os.environ['conductor.worker.all.domain'] = 'staging'

        config = resolve_worker_config(
            worker_name='test_task',
            poll_interval=500,
            domain='dev',
            thread_count=10,
            poll_timeout=150
        )

        # Only domain changes
        self.assertEqual(config['domain'], 'staging')
        self.assertEqual(config['poll_interval'], 500)
        self.assertEqual(config['thread_count'], 10)
        self.assertEqual(config['poll_timeout'], 150)


if __name__ == '__main__':
    unittest.main()
