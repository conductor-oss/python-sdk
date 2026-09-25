# Recommended examples

The [examples catalog](../examples/README.md) is broad; start with these maintained
paths and review their side effects before using real credentials.

| Path | Use | Expected result |
|---|---|---|
| [Hello World](../examples/helloworld/helloworld.py) | Core workflow and worker | Prints a completed workflow result. |
| [Basic agent](../examples/agents/01_basic_agent.py) | First Conductor agent | Prints an `AgentResult`. |
| [Plan and compile](../examples/agents/103_plan_and_compile.py) | Inspect an agent workflow | Prints the compiled plan/workflow shape. |
| [Agent quickstart](../examples/agents/quickstart/README.md) | Focused agent patterns | Runs the selected quickstart script. |

Stop local servers and worker processes after experimenting. Provider credentials
must be configured on the Conductor server.
