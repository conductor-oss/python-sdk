"""Regression tests: a request with no explicit per-request timeout must use the
client's configured timeout, NOT disable it. Previously the code passed
timeout=None, which httpx interprets as "no timeout" — so a half-open
connection (request sent, no response, never closed) hung forever and the
worker stopped polling permanently. These tests point each client at a
half-open server and assert the request fails on a bounded timeout instead of
hanging."""
import asyncio
import socket
import threading
import time
import unittest

import httpx

from conductor.client.http.rest import RESTClientObject, ApiException as SyncApiException
from conductor.client.http.async_rest import AsyncRESTClientObject, ApiException as AsyncApiException

CLIENT_TIMEOUT = 2.0   # short client default; a hung request must fail near this
HANG_GUARD = 15.0      # if a request runs longer than this, it's "hanging"


def _start_blackhole_sync():
    """TCP server that accepts, reads the request, then never responds or closes."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)
    port = srv.getsockname()[1]
    conns = []

    def loop():
        while True:
            try:
                c, _ = srv.accept()
            except OSError:
                return
            conns.append(c)
            try:
                c.recv(65536)  # consume request; never reply, never close
            except OSError:
                pass

    threading.Thread(target=loop, daemon=True).start()
    return srv, port, conns


class TestPollTimeout(unittest.TestCase):

    def test_sync_request_does_not_hang_on_half_open(self):
        srv, port, conns = _start_blackhole_sync()
        client = httpx.Client(timeout=httpx.Timeout(CLIENT_TIMEOUT))
        rest = RESTClientObject(connection=client)
        try:
            start = time.monotonic()
            with self.assertRaises(SyncApiException):
                rest.GET(f"http://127.0.0.1:{port}/", _request_timeout=None)
            elapsed = time.monotonic() - start
            self.assertLess(
                elapsed, HANG_GUARD,
                "sync request hung — client default timeout was not applied",
            )
        finally:
            client.close()
            srv.close()
            for c in conns:
                try:
                    c.close()
                except OSError:
                    pass

    def test_async_request_does_not_hang_on_half_open(self):
        asyncio.run(self._async_body())

    async def _async_body(self):
        async def handle(reader, writer):
            try:
                await reader.read(65536)
            except Exception:
                pass
            await asyncio.Event().wait()  # never respond, never close

        server = await asyncio.start_server(handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        client = httpx.AsyncClient(timeout=httpx.Timeout(CLIENT_TIMEOUT))
        rest = AsyncRESTClientObject(connection=client)
        try:
            start = time.monotonic()
            with self.assertRaises(AsyncApiException):
                await asyncio.wait_for(
                    rest.GET(f"http://127.0.0.1:{port}/", _request_timeout=None),
                    timeout=HANG_GUARD,
                )
            elapsed = time.monotonic() - start
            self.assertLess(
                elapsed, HANG_GUARD,
                "async request hung — client default timeout was not applied",
            )
        finally:
            await client.aclose()
            server.close()


if __name__ == "__main__":
    unittest.main()
