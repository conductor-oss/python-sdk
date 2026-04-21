#!/usr/bin/env python3
"""
Standalone reproduction script for issue #395.
Run before and after the fix to see the difference.

Usage:
    python tests/unit/api_client/repro_memory_leak.py

Before fix: memory grows ~400+ KB over 2000 requests
After fix:  memory stays flat (< 50 KB growth)
"""
import gc
import tracemalloc

import httpx

from conductor.client.http.rest import RESTResponse


class _EchoTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b'{"status":"ok"}')


def main():
    tracemalloc.start()
    client = httpx.Client(transport=_EchoTransport())

    # Warm up
    for _ in range(100):
        r = client.get("http://test/poll")
        resp = RESTResponse(r)
        _ = resp.data
        del r, resp
    gc.collect()

    snapshot_before = tracemalloc.take_snapshot()

    # Simulate 2000 poll cycles (~ 30 min of a real worker at 1 req/s)
    for i in range(2000):
        r = client.get("http://test/poll")
        resp = RESTResponse(r)
        _ = resp.data
        del r, resp

    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()

    client.close()

    stats = snapshot_after.compare_to(snapshot_before, 'lineno')

    total_growth = sum(s.size_diff for s in stats if s.size_diff > 0)
    print(f"\nTotal memory growth after 2000 requests: {total_growth / 1024:.1f} KB")

    if total_growth > 50 * 1024:
        print("LEAK DETECTED - growth exceeds 50 KB threshold")
        print("\nTop allocations:")
        for s in stats[:10]:
            if s.size_diff > 0:
                print(f"  {s}")
        return 1
    else:
        print("OK - no significant leak detected")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
