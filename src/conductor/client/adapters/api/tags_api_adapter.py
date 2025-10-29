from conductor.client.orkes.api.tags_api import TagsApi
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.http.models.tag import Tag


class TagsApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = TagsApi(api_client)

    def add_task_tag(self, body: Tag, task_name: str, **kwargs) -> object:
        """Add a task tag"""
        return self._api.add_task_tag(body, task_name, **kwargs)

    def add_workflow_tag(self, body: Tag, name: str, **kwargs) -> object:
        """Add a workflow tag"""
        return self._api.add_workflow_tag(body, name, **kwargs)

    def delete_task_tag(self, body: Tag, task_name: str, **kwargs) -> object:
        """Delete a task tag"""
        return self._api.delete_task_tag(body, task_name, **kwargs)

    def delete_workflow_tag(self, body: Tag, name: str, **kwargs) -> object:
        """Delete a workflow tag"""
        return self._api.delete_workflow_tag(body, name, **kwargs)

    def get_tags1(self, **kwargs) -> object:
        """List all tags"""
        return self._api.get_tags1(**kwargs)

    def get_task_tags(self, task_name: str, **kwargs) -> object:
        """Get task tags"""
        return self._api.get_task_tags(task_name, **kwargs)

    def get_workflow_tags(self, name: str, **kwargs) -> object:
        """Get workflow tags"""
        return self._api.get_workflow_tags(name, **kwargs)

    def set_task_tags(self, body: object, task_name: object, **kwargs) -> object:
        """Set task tags"""
        return self._api.set_task_tags(body, task_name, **kwargs)

    def set_workflow_tags(self, body: object, name: str, **kwargs) -> object:
        """Set workflow tags"""
        return self._api.set_workflow_tags(body, name, **kwargs)
