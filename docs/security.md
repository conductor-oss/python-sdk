# Security and secrets

Keep API keys, provider credentials, and signing secrets in the Conductor server
or its configured secret provider. Do not put them in workflow inputs, agent
prompts, task output, example source, or version control.

Agent tools declare required credentials; a capable server delivers resolved values
only in task runtime metadata. Missing credentials fail before tool execution.
See [SECRET_MANAGEMENT.md](SECRET_MANAGEMENT.md) and [agent tools](agents/concepts/tools.md).
