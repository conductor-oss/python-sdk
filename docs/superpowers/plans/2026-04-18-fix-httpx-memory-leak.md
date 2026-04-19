# Fix httpx Response Memory Leak (Issue #395)

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix unbounded memory growth caused by httpx.Response reference cycles retained in RESTResponse objects.

**Architecture:** RESTResponse eagerly reads the response body into `self.data` (a plain string), breaks the httpx `Response <-> BoundSyncStream` reference cycle by nulling `resp.stream`/`resp._request`, drops the `io.IOBase` base class, and adds `json()`/`getheader()` convenience methods. All consumers switch from `response.resp.text`/`response.resp.json()` to `response.data`/`response.json()`. The write-only `self.last_response` field is removed.

**Tech Stack:** Python, httpx, pytest, tracemalloc (for reproduction/validation script)

**Note — pre-existing bugs fixed as side effects:**
- `RESTResponse` previously lacked `.data` and `.getheader()` methods, yet `__deserialize_file()` in both `api_client.py:620-633` and `async_api_client.py:610-623` already called them. Those codepaths would have raised `AttributeError` at runtime. This fix adds both methods, resolving that latent bug.
- The `_preload_content=False` path in `rest.py:209-217` and `async_rest.py:202-210` returns a raw `httpx.Response` and then checks `r.status` (which doesn't exist on httpx.Response — it's `status_code`). This is a separate pre-existing bug and is **out of scope** for this fix.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/conductor/client/http/rest.py:10-44` | Sync RESTResponse: drop io.IOBase, eagerly read body, break cycle |
| Modify | `src/conductor/client/http/rest.py:286-370` | ApiException/AuthorizationException: use `http_resp.data` |
| Modify | `src/conductor/client/http/async_rest.py:10-44` | Async RESTResponse: same changes |
| Modify | `src/conductor/client/http/async_rest.py:279-363` | Async ApiException/AuthorizationException: same changes |
| Modify | `src/conductor/client/http/api_client.py:176,268-271` | Drop `last_response`, use `response.data`/`response.json()` |
| Modify | `src/conductor/client/http/async_api_client.py:187,279-282` | Drop `last_response`, use `response.data`/`response.json()` |
| Modify | `tests/unit/api_client/test_api_client_coverage.py:178-214` | Update deserialize tests for new API |
| Create | `tests/unit/api_client/test_memory_leak.py` | Reproduction test proving the leak is fixed |

---

## Chunk 1: Reproduction Script & Test

### Task 1: Create the memory leak reproduction test

This test proves the leak exists before the fix and passes after. It uses `tracemalloc` and `weakref` to detect that httpx.Response objects are retained.

**Files:**
- Create: `tests/unit/api_client/test_memory_leak.py`

- [ ] **Step 1: Write the reproduction test**

```python
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
```

- [ ] **Step 2: Run tests to verify the leak test FAILS (before the fix)**

Run: `python3 -m pytest tests/unit/api_client/test_memory_leak.py -v`
Expected: `test_httpx_response_does_not_leak` FAILS (most of the 50 refs still alive), `test_rest_response_attributes` FAILS (no `.data` attribute), `test_no_io_base_inheritance` FAILS (RESTResponse IS io.IOBase)

---

## Chunk 2: Fix RESTResponse (sync + async)

### Task 2: Fix sync RESTResponse in rest.py

**Files:**
- Modify: `src/conductor/client/http/rest.py:1-45`

- [ ] **Step 1: Replace RESTResponse class**

Replace the `RESTResponse` class (lines 10-44) with:

```python
class RESTResponse:

    def __init__(self, resp):
        self.status = resp.status_code
        self.reason = getattr(resp, 'reason_phrase', '') or self._get_reason_phrase(resp.status_code)
        self.data = resp.text                # eagerly read body
        self.headers = resp.headers
        # Break httpx Response <-> BoundSyncStream reference cycle (issue #395)
        resp.stream = None
        resp._request = None

    def _get_reason_phrase(self, status_code):
        """Get HTTP reason phrase from status code."""
        phrases = {
            200: 'OK', 201: 'Created', 202: 'Accepted', 204: 'No Content',
            301: 'Moved Permanently', 302: 'Found', 304: 'Not Modified',
            400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden',
            404: 'Not Found', 405: 'Method Not Allowed', 409: 'Conflict',
            429: 'Too Many Requests', 500: 'Internal Server Error',
            502: 'Bad Gateway', 503: 'Service Unavailable', 504: 'Gateway Timeout',
        }
        return phrases.get(status_code, 'Unknown')

    def json(self):
        return json.loads(self.data)

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def getheaders(self):
        return self.headers
```

Also remove the `import io` at line 1 (no longer needed — nothing else in the file uses it).

- [ ] **Step 2: Update ApiException to use `http_resp.data`**

In ApiException.__init__ (lines 288-309), replace every `http_resp.resp.text` with `http_resp.data`:

```python
def __init__(self, status=None, reason=None, http_resp=None, body=None):
    if http_resp:
        self.status = http_resp.status
        self.code = http_resp.status
        self.reason = http_resp.reason
        self.body = http_resp.data
        try:
            if http_resp.data:
                error = json.loads(http_resp.data)
                self.message = error['message']
            else:
                self.message = http_resp.data
        except Exception as e:
            self.message = http_resp.data
        self.headers = http_resp.getheaders()
    else:
        self.status = status
        self.code = status
        self.reason = reason
        self.body = body
        self.message = body
        self.headers = None
```

- [ ] **Step 3: Update AuthorizationException to use `http_resp.data`**

In AuthorizationException.__init__ (line 335), replace `http_resp.resp.text` with `http_resp.data`:

```python
def __init__(self, status=None, reason=None, http_resp=None, body=None):
    try:
        data = json.loads(http_resp.data)
        if 'error' in data:
            self._error_code = data['error']
        else:
            self._error_code = ''
    except (Exception):
        self._error_code = ''
    super().__init__(status, reason, http_resp, body)
```

- [ ] **Step 4: Run leak test to verify sync fix**

Run: `python3 -m pytest tests/unit/api_client/test_memory_leak.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Run existing rest client tests**

Run: `python3 -m pytest tests/unit/api_client/test_rest_client.py -v`
Expected: PASS (the test creates a mock response with `.status_code`, `.reason_phrase`, `.headers`, `.text` — all still work because RESTResponse reads `.text` in `__init__`)

### Task 3: Fix async RESTResponse in async_rest.py

**Files:**
- Modify: `src/conductor/client/http/async_rest.py:1-45,279-363`

- [ ] **Step 1: Apply identical RESTResponse changes to async_rest.py**

Mirror the exact same RESTResponse class from Task 2 Step 1 into async_rest.py (lines 10-44). Remove `import io` from line 1.

- [ ] **Step 2: Apply identical ApiException changes to async_rest.py**

Mirror the ApiException changes from Task 2 Step 2 into async_rest.py (lines 281-302).

- [ ] **Step 3: Apply identical AuthorizationException changes to async_rest.py**

Mirror the AuthorizationException changes from Task 2 Step 3 into async_rest.py (line 327).

- [ ] **Step 4: Run all unit tests so far**

Run: `python3 -m pytest tests/unit/api_client/ -v`
Expected: All PASS

---

## Chunk 3: Fix ApiClient consumers (sync + async) and update tests

### Task 4: Fix sync api_client.py

**Files:**
- Modify: `src/conductor/client/http/api_client.py:176,268-271`

- [ ] **Step 1: Remove `self.last_response` dead write**

In `__call_api_no_retry()` at line 176, delete:

```python
        self.last_response = response_data
```

- [ ] **Step 2: Update `deserialize()` to use new RESTResponse API**

In `deserialize()` (lines 268-271), change:

```python
        try:
            data = response.resp.json()
        except Exception:
            data = response.resp.text
```

to:

```python
        try:
            data = response.json()
        except Exception:
            data = response.data
```

- [ ] **Step 3: Run existing api_client tests**

Run: `python3 -m pytest tests/unit/api_client/test_api_client_coverage.py -v`
Expected: Some tests will FAIL because mocks still use `response.resp.json` / `response.resp.text`. This is expected — we fix them in Task 6.

### Task 5: Fix async_api_client.py

**Files:**
- Modify: `src/conductor/client/http/async_api_client.py:187,279-282`

- [ ] **Step 1: Remove `self.last_response` dead write**

In `__call_api_no_retry()` at line 187, delete:

```python
        self.last_response = response_data
```

- [ ] **Step 2: Update `deserialize()` to use new RESTResponse API**

In `deserialize()` (lines 279-282), change:

```python
        try:
            data = response.resp.json()
        except Exception:
            data = response.resp.text
```

to:

```python
        try:
            data = response.json()
        except Exception:
            data = response.data
```

### Task 6: Update existing tests for new RESTResponse API

**Files:**
- Modify: `tests/unit/api_client/test_api_client_coverage.py`

- [ ] **Step 1: Update `test_deserialize_with_json_response` (line 178)**

Change mock setup from:
```python
response.resp.json.return_value = {'key': 'value'}
```
to:
```python
response.json.return_value = {'key': 'value'}
```

- [ ] **Step 2: Update `test_deserialize_with_text_response` (line 190)**

Change mock setup from:
```python
response.resp.json.side_effect = Exception("Not JSON")
response.resp.text = "plain text"
```
to:
```python
response.json.side_effect = Exception("Not JSON")
response.data = "plain text"
```

- [ ] **Step 3: Update `test_deserialize_with_value_error` (line 204)**

Change mock setup from:
```python
response.resp.json.return_value = {'key': 'value'}
```
to:
```python
response.json.return_value = {'key': 'value'}
```

- [ ] **Step 4: Search for any other `response.resp.` references in tests**

Run: `grep -rn 'response\.resp\.' tests/` and update any remaining references.

- [ ] **Step 5: Run the full unit test suite**

Run: `python3 -m pytest tests/unit/ -v`
Expected: All PASS

- [ ] **Step 6: Run backward compatibility and serialization tests**

Run: `python3 -m pytest tests/backwardcompatibility/ tests/serdesertest/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/conductor/client/http/rest.py \
        src/conductor/client/http/async_rest.py \
        src/conductor/client/http/api_client.py \
        src/conductor/client/http/async_api_client.py \
        tests/unit/api_client/test_memory_leak.py \
        tests/unit/api_client/test_api_client_coverage.py
git commit -m "fix(http): break httpx Response reference cycle causing memory leak (#395)

RESTResponse now eagerly reads resp.text into self.data and breaks the
httpx Response <-> BoundSyncStream cycle by nulling resp.stream and
resp._request. Drops io.IOBase inheritance (removes __del__ finalizer
overhead). Removes write-only self.last_response retention.

Fixes #395"
```

---

## Chunk 4: Manual Validation Script

### Task 7: Create a standalone reproduction script

This is a script that can be run outside of pytest to visually confirm the leak is gone. It simulates the worker polling loop.

**Files:**
- Create: `tests/unit/api_client/repro_memory_leak.py`

- [ ] **Step 1: Write the reproduction script**

```python
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
```

- [ ] **Step 2: Run the reproduction script**

Run: `python tests/unit/api_client/repro_memory_leak.py`
Expected output (after fix):
```
Total memory growth after 2000 requests: <50 KB
OK - no significant leak detected
```

- [ ] **Step 3: Run the full test suite one final time**

Run: `python3 -m pytest tests/unit tests/backwardcompatibility tests/serdesertest -v`
Expected: All PASS
