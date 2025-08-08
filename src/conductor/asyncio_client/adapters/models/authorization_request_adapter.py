from conductor.asyncio_client.adapters.models.subject_ref_adapter import SubjectRefAdapter
from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter
from conductor.asyncio_client.http.models import AuthorizationRequest


class AuthorizationRequestAdapter(AuthorizationRequest):
    subject: SubjectRefAdapter
    target: TargetRefAdapter
