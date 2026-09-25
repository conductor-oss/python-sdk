# Core workflow and worker quickstart

**Prerequisites:** Python 3.10+, `pip install conductor-python`, and a reachable
Conductor server from [server setup](server-setup.md).

Run the maintained example from its directory so its sibling workflow module is
importable:

```shell
cd examples/helloworld
python helloworld.py
```

Expected result: the workflow completes and prints `workflow result: Hello World`.
The example registers its workflow, starts a local worker, executes the workflow,
and stops the worker. If the task stays scheduled, verify that the worker is
polling the exact task type. Continue with [workers](workers.md) or [workflows](workflows.md).
