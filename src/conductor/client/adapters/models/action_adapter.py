from conductor.client.http.models import Action


class ActionAdapter(Action):
    def __init__(
        self,
        action=None,
        start_workflow=None,
        complete_task=None,
        fail_task=None,
        expand_inline_json=None,
        terminate_workflow=None,
        update_workflow_variables=None,
    ):
        super().__init__(
            action=action,
            complete_task=complete_task,
            expand_inline_json=expand_inline_json,
            fail_task=fail_task,
            start_workflow=start_workflow,
            terminate_workflow=terminate_workflow,
            update_workflow_variables=update_workflow_variables,
        )
