import unittest
from unittest.mock import MagicMock, patch

import httpx

from conductor.client.http import rest


def _ok_response():
    response = MagicMock()
    response.status_code = 200
    response.reason_phrase = "OK"
    response.headers = {}
    response.text = ""
    return response


class TestRESTClientObject(unittest.TestCase):
    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_resets_and_retries_on_remote_protocol_error(self, mock_create_client):
        first_client = MagicMock()
        second_client = MagicMock()
        mock_create_client.side_effect = [first_client, second_client]

        first_client.request.side_effect = httpx.RemoteProtocolError("ConnectionTerminated")
        second_client.request.return_value = _ok_response()

        client = rest.RESTClientObject(connection=None)
        result = client.request("GET", "http://example", query_params={"a": "b"})

        self.assertEqual(mock_create_client.call_count, 2)
        self.assertTrue(first_client.close.called)
        self.assertEqual(result.status, 200)

    def test_is_closed_client_error_recognises_httpx_messages(self):
        self.assertTrue(
            rest._is_closed_client_error(
                RuntimeError("Cannot send a request, as the client has been closed.")
            )
        )
        self.assertTrue(
            rest._is_closed_client_error(RuntimeError("The transport is closed"))
        )
        self.assertFalse(rest._is_closed_client_error(RuntimeError("something else")))
        self.assertFalse(rest._is_closed_client_error(None))

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_heals_when_client_already_closed_before_request(self, mock_create_client):
        """If `is_closed` is already True we should reset before sending."""
        first_client = MagicMock()
        first_client.is_closed = True  # pretend it was closed mid-session
        second_client = MagicMock()
        second_client.is_closed = False
        second_client.request.return_value = _ok_response()
        mock_create_client.side_effect = [first_client, second_client]

        client = rest.RESTClientObject(connection=None)
        result = client.request("GET", "http://example")

        # The closed client must have been replaced and never used to send.
        self.assertFalse(first_client.request.called)
        self.assertTrue(first_client.close.called)
        self.assertTrue(second_client.request.called)
        self.assertEqual(result.status, 200)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_heals_on_runtime_error_closed_client_and_retries_get(self, mock_create_client):
        """The new RuntimeError branch should reset and retry idempotent calls."""
        first_client = MagicMock()
        first_client.is_closed = False
        first_client.request.side_effect = RuntimeError(
            "Cannot send a request, as the client has been closed."
        )
        second_client = MagicMock()
        second_client.is_closed = False
        second_client.request.return_value = _ok_response()
        mock_create_client.side_effect = [first_client, second_client]

        client = rest.RESTClientObject(connection=None)
        result = client.request("GET", "http://example")

        self.assertEqual(first_client.request.call_count, 1)
        self.assertTrue(first_client.close.called)
        self.assertEqual(second_client.request.call_count, 1)
        self.assertEqual(result.status, 200)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_non_idempotent_post_does_not_auto_retry_after_close(self, mock_create_client):
        """POST is not idempotent; we must reset the client but surface the error."""
        first_client = MagicMock()
        first_client.is_closed = False
        first_client.request.side_effect = RuntimeError(
            "Cannot send a request, as the client has been closed."
        )
        second_client = MagicMock()
        second_client.is_closed = False
        mock_create_client.side_effect = [first_client, second_client]

        client = rest.RESTClientObject(connection=None)

        with self.assertRaises(rest.ApiException) as ctx:
            client.request("POST", "http://example", body={"x": 1})

        # First attempt sent, reset happened, but no retry for POST.
        self.assertEqual(first_client.request.call_count, 1)
        self.assertTrue(first_client.close.called)
        self.assertEqual(second_client.request.call_count, 0)
        self.assertIn("Runtime error", str(ctx.exception))

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_unrelated_runtime_error_is_not_retried(self, mock_create_client):
        """RuntimeErrors that aren't about a closed client must not trigger heal-retry."""
        first_client = MagicMock()
        first_client.is_closed = False
        first_client.request.side_effect = RuntimeError("something totally unrelated")
        second_client = MagicMock()
        mock_create_client.side_effect = [first_client, second_client]

        client = rest.RESTClientObject(connection=None)

        with self.assertRaises(rest.ApiException):
            client.request("GET", "http://example")

        self.assertEqual(first_client.request.call_count, 1)
        self.assertFalse(first_client.close.called)
        self.assertEqual(mock_create_client.call_count, 1)  # no replacement created

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_reset_connection_heals_externally_provided_connection(self, mock_create_client):
        """Previously `_reset_connection` silently no-op'd for externally-provided
        connections. With the fix it should close the old one and create a fresh
        client that we own."""
        external = MagicMock()
        external.is_closed = True
        replacement = MagicMock()
        replacement.is_closed = False
        mock_create_client.return_value = replacement

        client = rest.RESTClientObject(connection=external)
        self.assertFalse(client._owns_connection)

        client._reset_connection()

        self.assertTrue(external.close.called)
        self.assertIs(client.connection, replacement)
        self.assertTrue(client._owns_connection)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_is_client_closed_defensive_on_missing_attribute(self, mock_create_client):
        """Mocks or subclasses that don't expose `is_closed` should be treated as open."""
        stub_client = MagicMock(spec=[])  # no `is_closed` attr
        mock_create_client.return_value = stub_client

        client = rest.RESTClientObject(connection=None)
        self.assertFalse(client._is_client_closed())

