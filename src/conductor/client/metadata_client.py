from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from conductor.client.adapters.models.workflow_def_adapter import WorkflowDefAdapter as WorkflowDef
from conductor.client.adapters.models.task_def_adapter import TaskDefAdapter as TaskDef
from conductor.client.orkes.models.metadata_tag import MetadataTag


class MetadataClient(ABC):
    @abstractmethod
    def register_workflow_def(
            self,
            workflow_def: WorkflowDef,
            overwrite: Optional[bool]):
        pass

    @abstractmethod
    def update_workflow_def(
            self,
            workflow_def: WorkflowDef,
            overwrite: Optional[bool]):
        pass

    @abstractmethod
    def unregister_workflow_def(self, workflow_name: str, version: int):
        pass

    @abstractmethod
    def get_workflow_def(self, name: str, version: Optional[int]) -> WorkflowDef:
        pass

    @abstractmethod
    def get_all_workflow_defs(self) -> List[WorkflowDef]:
        pass

    @abstractmethod
    def register_task_def(self, task_def: TaskDef):
        pass

    @abstractmethod
    def update_task_def(self, task_def: TaskDef):
        pass

    @abstractmethod
    def unregister_task_def(self, task_type: str):
        pass

    @abstractmethod
    def get_task_def(self, task_type: str) -> TaskDef:
        pass

    @abstractmethod
    def get_all_task_defs(self) -> List[TaskDef]:
        pass

    @abstractmethod
    def add_workflow_tag(self, tag: MetadataTag, workflow_name: str):
        pass

    @abstractmethod
    def get_workflow_tags(self, workflow_name: str) -> List[MetadataTag]:
        pass

    @abstractmethod
    def set_workflow_tags(self, tags: List[MetadataTag], workflow_name: str):
        pass

    @abstractmethod
    def delete_workflow_tag(self, tag: MetadataTag, workflow_name: str):
        pass
