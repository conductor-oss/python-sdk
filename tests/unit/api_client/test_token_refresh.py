import asyncio
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

import httpx

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.http.api_client import ApiClient
from conductor.client.http.async_api_client import AsyncApiClient
from conductor.client.http.async_rest import AsyncRESTClientObject

SERVER_URL = 'http://server/api'
INVALID_TOKEN = {'error': 'INVALID_TOKEN', 'message': 'Not a valid token'}
N = 20


def _configuration():
    return Configuration(
        server_api_url=SERVER_URL,
        authentication_settings=AuthenticationSettings(key_id='key', key_secret='secret'),
    )


def _is_token_request(request):
    return request.url.path.endswith('/token')


class TestTokenRefresh(unittest.TestCase):
    """After a failover every in-flight request is rejected at once; together they must fetch one new token."""

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_concurrent_rejections_fetch_one_new_token(self):
        issued = []
        rejected = []
        failed_over = threading.Event()
        all_rejected = threading.Barrier(N, timeout=5)
        lock = threading.Lock()

        def handler(request):
            if _is_token_request(request):
                # Hold the fetch open so the other requests' refreshes overlap it.
                time.sleep(0.05)
                with lock:
                    issued.append(None)
                    return httpx.Response(200, json={'token': f't{len(issued)}'})
            if failed_over.is_set() and request.headers.get('X-Authorization') == 't1':
                with lock:
                    rejected.append(None)
                try:
                    all_rejected.wait()
                except threading.BrokenBarrierError:
                    pass
                return httpx.Response(401, json=INVALID_TOKEN)
            return httpx.Response(200, json={})

        configuration = _configuration()
        configuration.http_connection = httpx.Client(transport=httpx.MockTransport(handler))
        client = ApiClient(configuration)  # fetches t1
        failed_over.set()

        with ThreadPoolExecutor(max_workers=N) as pool:
            futures = [pool.submit(client.call_api, '/thing', 'GET', _return_http_data_only=True) for _ in range(N)]
            for future in futures:
                future.result()

        self.assertEqual(N, len(rejected))
        self.assertEqual(2, len(issued))  # t1 before the failover, t2 shared by every retry

    def test_concurrent_rejections_fetch_one_new_token_async(self):
        issued = []
        rejected = []
        state = {'failed_over': False}

        async def scenario():
            all_rejected = asyncio.Event()

            async def handler(request):
                if _is_token_request(request):
                    await asyncio.sleep(0.05)
                    issued.append(None)
                    return httpx.Response(200, json={'token': f't{len(issued)}'})
                if state['failed_over'] and request.headers.get('X-Authorization') == 't1':
                    rejected.append(None)
                    if len(rejected) == N:
                        all_rejected.set()
                    try:
                        await asyncio.wait_for(all_rejected.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        pass
                    return httpx.Response(401, json=INVALID_TOKEN)
                return httpx.Response(200, json={})

            client = AsyncApiClient(_configuration())
            client.async_rest_client = AsyncRESTClientObject(
                connection=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
            await client.call_api('/thing', 'GET', _return_http_data_only=True)  # fetches t1
            state['failed_over'] = True
            await asyncio.gather(*(client.call_api('/thing', 'GET', _return_http_data_only=True) for _ in range(N)))

        self._run(scenario())

        self.assertEqual(N, len(rejected))
        self.assertEqual(2, len(issued))  # t1 before the failover, t2 shared by every retry

    def test_concurrent_first_calls_fetch_one_token_async(self):
        issued = []

        async def scenario():
            async def handler(request):
                if _is_token_request(request):
                    await asyncio.sleep(0.05)
                    issued.append(None)
                    return httpx.Response(200, json={'token': f't{len(issued)}'})
                return httpx.Response(200, json={})

            client = AsyncApiClient(_configuration())
            client.async_rest_client = AsyncRESTClientObject(
                connection=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
            await asyncio.gather(*(client.call_api('/thing', 'GET', _return_http_data_only=True) for _ in range(N)))

        self._run(scenario())

        self.assertEqual(1, len(issued))
