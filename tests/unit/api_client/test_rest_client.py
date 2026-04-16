import threading
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


def _mock_client(is_closed=False):
    """A MagicMock httpx.Client with an explicit `is_closed` flag.

    Default MagicMock attributes are truthy, which would incorrectly trigger
    the pre-check heal path. Set the flag explicitly for test clarity.
    """
    c = MagicMock()
    c.is_closed = is_closed
    return c


class TestRESTClientObject(unittest.TestCase):
    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_resets_and_retries_on_remote_protocol_error(self, mock_create_client):
        first_client = _mock_client()
        second_client = _mock_client()
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
        first_client = _mock_client(is_closed=True)
        second_client = _mock_client(is_closed=False)
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
        first_client = _mock_client(is_closed=False)
        first_client.request.side_effect = RuntimeError(
            "Cannot send a request, as the client has been closed."
        )
        second_client = _mock_client(is_closed=False)
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
        first_client = _mock_client(is_closed=False)
        first_client.request.side_effect = RuntimeError(
            "Cannot send a request, as the client has been closed."
        )
        second_client = _mock_client(is_closed=False)
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
        first_client = _mock_client(is_closed=False)
        first_client.request.side_effect = RuntimeError("something totally unrelated")
        second_client = _mock_client()
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
        external = _mock_client(is_closed=True)
        replacement = _mock_client(is_closed=False)
        mock_create_client.return_value = replacement

        client = rest.RESTClientObject(connection=external)
        self.assertFalse(client._owns_connection)

        self.assertTrue(client._reset_connection())

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

    # -------- Thread-safe compare-and-swap reset --------

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_reset_connection_cas_no_ops_when_expected_mismatches(self, mock_create_client):
        """If another thread already healed, a stale caller must NOT close the
        replacement client or create yet another one."""
        initial = _mock_client()
        already_healed = _mock_client()
        # Only one client needed from `_create_default_httpx_client` (the initial
        # construction). If the CAS incorrectly fires, this list will be exhausted.
        mock_create_client.side_effect = [initial]

        client = rest.RESTClientObject(connection=None)
        # Simulate "some other thread already healed": swap the connection.
        client.connection = already_healed

        stale_reference = initial  # pretend we saw `initial` before the error
        did_reset = client._reset_connection(expected=stale_reference)

        self.assertFalse(did_reset)
        # The already-healed client must survive untouched.
        self.assertIs(client.connection, already_healed)
        self.assertFalse(already_healed.close.called)
        # Only the initial client was ever constructed.
        self.assertEqual(mock_create_client.call_count, 1)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_reset_connection_cas_replaces_when_expected_matches(self, mock_create_client):
        """With a matching `expected`, reset actually replaces the client."""
        initial = _mock_client()
        replacement = _mock_client()
        mock_create_client.side_effect = [initial, replacement]

        client = rest.RESTClientObject(connection=None)

        did_reset = client._reset_connection(expected=initial)

        self.assertTrue(did_reset)
        self.assertIs(client.connection, replacement)
        self.assertTrue(initial.close.called)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_thundering_herd_reset_produces_exactly_one_replacement(self, mock_create_client):
        """When N threads all see the same broken client and race to heal, we
        must end up with exactly one new client and exactly one
        `_reset_connection` returning True."""
        num_threads = 16
        initial = _mock_client()
        replacements = [_mock_client() for _ in range(num_threads + 1)]
        # +1 for the __init__ call, rest would be extras if CAS were broken.
        mock_create_client.side_effect = [initial] + replacements

        client = rest.RESTClientObject(connection=None)
        self.assertIs(client.connection, initial)

        start_barrier = threading.Barrier(num_threads)
        results = []
        results_lock = threading.Lock()

        def heal():
            start_barrier.wait()
            got = client._reset_connection(expected=initial)
            with results_lock:
                results.append(got)

        threads = [threading.Thread(target=heal) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one thread saw `expected == current` and actually reset.
        self.assertEqual(sum(1 for r in results if r), 1, msg=f"results={results}")
        self.assertEqual(sum(1 for r in results if not r), num_threads - 1)
        # Exactly one replacement client was created on top of the initial one.
        self.assertEqual(mock_create_client.call_count, 2)
        # The initial client was closed exactly once.
        self.assertEqual(initial.close.call_count, 1)
        # The replacement is now `client.connection` and was never closed.
        self.assertIsNot(client.connection, initial)
        self.assertFalse(client.connection.close.called)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_reset_connection_without_expected_always_resets(self, mock_create_client):
        """Backwards-compat: existing callers that don't pass `expected` still work."""
        initial = _mock_client()
        replacement = _mock_client()
        mock_create_client.side_effect = [initial, replacement]

        client = rest.RESTClientObject(connection=None)

        self.assertTrue(client._reset_connection())
        self.assertIs(client.connection, replacement)

    @patch.object(rest.RESTClientObject, "_create_default_httpx_client")
    def test_concurrent_request_failures_do_not_cascade_close(self, mock_create_client):
        """End-to-end: two threads' requests both fail on the same client; only
        one reset happens and each thread retries on the fresh client.

        This is the whole reason the thundering-herd guard exists - without
        CAS, thread B would close thread A's freshly-built replacement.
        """
        initial = _mock_client(is_closed=False)
        replacement = _mock_client(is_closed=False)
        mock_create_client.side_effect = [initial, replacement]

        barrier = threading.Barrier(2)

        def shared_error(*_, **__):
            # Force both threads into the error branch roughly simultaneously.
            barrier.wait()
            raise httpx.RemoteProtocolError("Received pseudo-header in trailer")

        initial.request.side_effect = shared_error
        replacement.request.return_value = _ok_response()

        client = rest.RESTClientObject(connection=None)

        results = []
        results_lock = threading.Lock()

        def do_get():
            try:
                resp = client.request("GET", "http://example")
                with results_lock:
                    results.append(resp.status)
            except Exception as e:  # noqa: BLE001
                with results_lock:
                    results.append(e)

        threads = [threading.Thread(target=do_get) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Both threads eventually succeeded on the replacement.
        self.assertEqual(results, [200, 200], msg=f"results={results}")
        # Only ONE replacement was ever created (init + 1 heal).
        self.assertEqual(mock_create_client.call_count, 2)
        # Initial client was closed exactly once, not twice.
        self.assertEqual(initial.close.call_count, 1)
        # Replacement is still the live client.
        self.assertIs(client.connection, replacement)
        self.assertFalse(replacement.close.called)

