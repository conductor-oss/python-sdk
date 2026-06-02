import asyncio
import unittest
from unittest.mock import Mock, AsyncMock

from conductor.client.http.async_api_client import AsyncApiClient
from conductor.client.configuration.configuration import Configuration


class TestAsyncApiClientMetricUri(unittest.TestCase):

    def setUp(self):
        self.config = Configuration(
            base_url="http://localhost:8080",
            authentication_settings=None,
        )

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_request_passes_metric_uri_to_collector(self):
        """metric_uri kwarg is forwarded to record_api_request_time on success."""
        metrics_collector = Mock()
        client = AsyncApiClient(configuration=self.config, metrics_collector=metrics_collector)
        client.async_rest_client.GET = AsyncMock(return_value=Mock(status=200))

        self._run(client.request(
            'GET', 'http://localhost:8080/api/workflow/test-id',
            metric_uri='/api/workflow/{workflowId}',
        ))

        call_args = metrics_collector.record_api_request_time.call_args
        self.assertEqual(call_args[1]['metric_uri'], '/api/workflow/{workflowId}')

    def test_request_passes_metric_uri_to_collector_on_error(self):
        """metric_uri kwarg is forwarded to record_api_request_time on error."""
        metrics_collector = Mock()
        client = AsyncApiClient(configuration=self.config, metrics_collector=metrics_collector)

        error = Exception('Test error')
        error.status = 500
        client.async_rest_client.GET = AsyncMock(side_effect=error)

        with self.assertRaises(Exception):
            self._run(client.request(
                'GET', 'http://localhost:8080/api/workflow/test-id',
                metric_uri='/api/workflow/{workflowId}',
            ))

        call_args = metrics_collector.record_api_request_time.call_args
        self.assertEqual(call_args[1]['metric_uri'], '/api/workflow/{workflowId}')


if __name__ == '__main__':
    unittest.main()
