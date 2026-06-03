import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from conductor.client.http import async_rest


def _ok_response():
    response = MagicMock()
    response.status_code = 200
    response.reason_phrase = "OK"
    response.headers = {}
    response.text = ""
    return response


def _mock_async_client():
    """An httpx.AsyncClient stand-in whose request/aclose are awaitable."""
    c = MagicMock()
    c.request = AsyncMock()
    c.aclose = AsyncMock()
    return c


class TestAsyncRESTClientObject(unittest.TestCase):
    @patch.dict("os.environ", {"CONDUCTOR_HTTP2_ENABLED": "true"})
    @patch.object(async_rest.AsyncRESTClientObject, "_create_default_httpx_client")
    def test_http2_protocol_error_downgrades_to_http1(self, mock_create_client):
        first_client = _mock_async_client()
        second_client = _mock_async_client()
        mock_create_client.side_effect = [first_client, second_client]

        first_client.request.side_effect = httpx.RemoteProtocolError("ConnectionTerminated")
        second_client.request.return_value = _ok_response()

        client = async_rest.AsyncRESTClientObject(connection=None)
        self.assertTrue(client._http2_enabled)  # default on

        result = asyncio.run(client.request("GET", "http://example"))

        self.assertEqual(result.status, 200)
        self.assertFalse(client._http2_enabled)       # HTTP/2 turned off
        self.assertTrue(client._http2_downgraded)
        self.assertTrue(first_client.aclose.called)

    @patch.dict("os.environ", {"CONDUCTOR_HTTP2_ENABLED": "true",
                               "CONDUCTOR_HTTP2_AUTO_FALLBACK": "false"})
    @patch.object(async_rest.AsyncRESTClientObject, "_create_default_httpx_client")
    def test_http2_auto_fallback_can_be_disabled(self, mock_create_client):
        first_client = _mock_async_client()
        second_client = _mock_async_client()
        mock_create_client.side_effect = [first_client, second_client]

        first_client.request.side_effect = httpx.RemoteProtocolError("ConnectionTerminated")
        second_client.request.return_value = _ok_response()

        client = async_rest.AsyncRESTClientObject(connection=None)
        result = asyncio.run(client.request("GET", "http://example"))

        self.assertEqual(result.status, 200)
        self.assertTrue(client._http2_enabled)        # still HTTP/2
        self.assertFalse(client._http2_downgraded)


if __name__ == "__main__":
    unittest.main()
