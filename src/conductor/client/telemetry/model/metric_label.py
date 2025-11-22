from enum import Enum


class MetricLabel(str, Enum):
    ENTITY_NAME = "entityName"
    EXCEPTION = "exception"
    METHOD = "method"
    OPERATION = "operation"
    PAYLOAD_TYPE = "payload_type"
    STATUS = "status"
    TASK_TYPE = "taskType"
    URI = "uri"
    WORKFLOW_TYPE = "workflowType"
    WORKFLOW_VERSION = "version"
