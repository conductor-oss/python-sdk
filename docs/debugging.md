# Debugging incidents

Start with safe evidence: workflow ID, task reference, status, retry count, and
`reasonForIncompletion`. Confirm server reachability and authentication before
changing application code.

| Symptom | First check |
|---|---|
| Connection error | `CONDUCTOR_SERVER_URL` includes `/api` and the server is healthy. |
| Task remains scheduled | A worker polls the exact task type and domain. |
| Authentication failure | `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` target the active server. |
| Agent cannot call a model | The provider credential is configured on the server. |

Use [WORKFLOW.md](WORKFLOW.md) and [agents/reference/client.md](agents/reference/client.md)
for the relevant inspection APIs.
