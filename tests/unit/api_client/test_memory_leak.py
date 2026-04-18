"""
Reproduction and regression test for GitHub issue #395:
httpx.Response objects leak due to reference cycle in BoundSyncStream.

The test creates real httpx responses (via httpx.Client against a local
transport), wraps them in RESTResponse, and verifies the httpx.Response
is eligible for garbage collection after the RESTResponse is consumed.
"""
import gc
import io
import weakref
import unittest

import httpx

from conductor.client.http.rest import RESTResponse


class _EchoTransport(httpx.BaseTransport):
    """Returns a small JSON body for every request - no network needed."""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b'{"ok": true}',
        )


class TestHttpxResponseMemoryLeak(unittest.TestCase):
    """Regression: RESTResponse must not prevent httpx.Response GC."""

    def test_httpx_response_does_not_leak(self):
        """After wrapping in RESTResponse the raw httpx.Response must be GC-able."""
        client = httpx.Client(transport=_EchoTransport())

        refs = []
        for _ in range(50):
            raw = client.get("http://test/ping")
            refs.append(weakref.ref(raw))
            rest_resp = RESTResponse(raw)
            # Simulate what api_client does: read body then discard
            _ = rest_resp.data
            del raw, rest_resp

        # Force full collection (including cyclic GC)
        gc.collect()

        alive = sum(1 for r in refs if r() is not None)
        # Before the fix, all 50 would be alive.
        # After the fix, none (or very few due to GC timing) should remain.
        self.assertLessEqual(alive, 2, f"{alive}/50 httpx.Response objects still alive - leak not fixed")

        client.close()

    def test_rest_response_attributes(self):
        """RESTResponse exposes .data, .json(), .getheader(), .getheaders()."""
        client = httpx.Client(transport=_EchoTransport())
        raw = client.get("http://test/ping")
        resp = RESTResponse(raw)

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.data, '{"ok": true}')
        self.assertEqual(resp.json(), {"ok": True})
        self.assertEqual(resp.getheader("content-type"), "application/json")
        self.assertIsNotNone(resp.getheaders())
        # After construction, the raw response should not be retained
        self.assertFalse(hasattr(resp, 'resp'))

        client.close()

    def test_no_io_base_inheritance(self):
        """RESTResponse must not inherit from io.IOBase (avoids __del__ overhead)."""
        client = httpx.Client(transport=_EchoTransport())
        raw = client.get("http://test/ping")
        resp = RESTResponse(raw)
        self.assertNotIsInstance(resp, io.IOBase)
        client.close()
