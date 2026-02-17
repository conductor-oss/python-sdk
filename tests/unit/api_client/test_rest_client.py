import unittest
from unittest.mock import MagicMock, patch

import httpx

from conductor.client.http import rest


class TestRESTClientObject(unittest.TestCase):
    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_resets_and_retries_on_remote_protocol_error(self, mock_create_client):
        first_client = MagicMock()
        second_client = MagicMock()
        mock_create_client.side_effect = [first_client, second_client]

        first_client.request.side_effect = httpx.RemoteProtocolError("ConnectionTerminated")

        response = MagicMock()
        response.status_code = 200
        response.reason_phrase = "OK"
        response.headers = {}
        response.text = ""
        second_client.request.return_value = response

        client = rest.RESTClientObject(connection=None)
        result = client.request("GET", "http://example", query_params={"a": "b"})

        self.assertEqual(mock_create_client.call_count, 2)
        self.assertTrue(first_client.close.called)
        self.assertEqual(result.status, 200)

