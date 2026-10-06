"""Server guardrails — guardrails the Conductor server enforces on the agent's LLM calls.

``ServerGuardrail`` names a guardrail defined on the server (or a builtin such as
``"pii"``). The server checks it inside every LLM task the agent compiles, on the
prompt before it reaches the model and on the model's answer. Nothing runs in this
process, and sub-agents compiled with the agent are covered too.

Server guardrails sit in the same ``guardrails`` list as the SDK's own kinds:

- ``ServerGuardrail("pii", action="REDACT")`` — the server redacts personal data,
  so the email address in the prompt never reaches the model
- ``ServerGuardrail("secrets", action="BLOCK")`` — the LLM task fails if an API key
  or credential appears
- ``RegexGuardrail`` — unchanged: compiled into the agent's own retry loop

A server that does not enforce server guardrails rejects the agent rather than run
it unguarded.

Requirements:
    - Orkes Conductor server with guardrails enabled
    - CONDUCTOR_SERVER_URL=http://localhost:8080/api as environment variable
    - CONDUCTOR_AGENT_LLM_MODEL=openai/gpt-4o-mini as environment variable
"""

from conductor.ai.agents import Agent, AgentRuntime, OnFail, RegexGuardrail, ServerGuardrail
from settings import settings

agent = Agent(
    name="support_replier",
    model=settings.llm_model,
    instructions="Draft a short, friendly reply to the customer's message.",
    guardrails=[
        ServerGuardrail("pii", action="REDACT"),
        ServerGuardrail("secrets", action="BLOCK"),
        RegexGuardrail(
            name="no_internal_links",
            patterns=[r"https?://[\w.-]*\.internal\b"],
            message="Do not include internal links in the reply.",
            on_fail=OnFail.RETRY,
        ),
    ],
)

# REDACT: the email address is removed before the prompt reaches the model; the run completes.
prompt = (
    "Hi, I'm Jane Doe (jane.doe@example.com). My last invoice charged me twice. "
    "Can you help?"
)

# BLOCK: an API key in the message fails the LLM task, so the run fails instead of sending it.
block_prompt = (
    "Our integration stopped working. Here is the key we use: api_FAKEKEY0123456789EXAMPLE. "
    "Can you check what is wrong?"
)

if __name__ == "__main__":
    with AgentRuntime() as runtime:
        print("── REDACT ──")
        runtime.run(agent, prompt).print_result()

        print("── BLOCK ──")
        blocked = runtime.run(agent, block_prompt)
        print(f"Status: {blocked.status}")
        print(f"Error: {blocked.error}")
