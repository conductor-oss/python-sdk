# Connection and authentication

`Configuration()` reads `CONDUCTOR_SERVER_URL`, then defaults to
`http://localhost:8080/api`. It reads `CONDUCTOR_AUTH_KEY` and
`CONDUCTOR_AUTH_SECRET` together when the server requires key/secret auth.

```python
from conductor.client.configuration.configuration import Configuration

config = Configuration()
print(config.host)
```

**OSS:** a local development server may allow anonymous access. **Orkes:** use
the tenant API endpoint and an application access key. Never put credentials in
workflow inputs, agent prompts, or source control.

If requests fail, verify that the URL ends in `/api`, the server is reachable,
and the credentials belong to that endpoint. Next: [core quickstart](core-quickstart.md).
