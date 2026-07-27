# Connect the Python SDK to a Conductor server

**Audience:** developers running workflows or Conductor agents locally or against a hosted cluster.

## Hosted or remote server

Set the API URL, including `/api`, then add credentials only when the target
requires them:

```shell
export CONDUCTOR_SERVER_URL=https://your-server.example/api
export CONDUCTOR_AUTH_KEY=<key-id>
export CONDUCTOR_AUTH_SECRET=<key-secret>
```

## Local development

The Conductor CLI is the preferred local path:

```shell
conductor server start
conductor server status
export CONDUCTOR_SERVER_URL=http://localhost:8080/api
```

Docker is an alternative: `docker run --rm -p 8080:8080 conductoross/conductor:latest`.
Stop CLI-managed servers with `conductor server stop` and containers with
`docker stop <container>`.

For agent runs, configure the LLM provider credential on the server before
starting it. Continue with [connection/authentication](connection-authentication.md).
