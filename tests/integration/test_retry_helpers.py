import unittest
from unittest.mock import patch

from conductor.client.http.rest import ApiException
from tests.integration.retry_helpers import retry_scenario


class TestRetryScenario(unittest.TestCase):

    @patch('tests.integration.retry_helpers.time.sleep')
    @patch('tests.integration.retry_helpers.time.monotonic', return_value=100.0)
    def test_retries_wrapped_explicit_status(self, monotonic, sleep):
        attempts = []

        def signal_fresh_workflow():
            attempts.append('attempt')
            if len(attempts) == 1:
                try:
                    raise ApiException(status=423, reason='Locked')
                except ApiException as exc:
                    raise RuntimeError('signal race') from exc
            return 'fresh-workflow'

        result = retry_scenario(
            'signal_race', signal_fresh_workflow, deadline=200.0,
            base_delay=0.25, max_delay=1.0, retry_statuses=(423,))

        self.assertEqual(result, 'fresh-workflow')
        self.assertEqual(attempts, ['attempt', 'attempt'])
        monotonic.assert_called_once_with()
        sleep.assert_called_once_with(0.25)
