from conductor.client.codegen.models import AuthorizationRequest


class AuthorizationRequestAdapter(AuthorizationRequest):
    def __init__(self, subject=None, target=None, access=None):
        super().__init__(access=access, subject=subject, target=target)

    @property
    def subject(self):
        return super().subject

    @subject.setter
    def subject(self, subject):
        self._subject = subject

    @property
    def target(self):
        return super().target

    @target.setter
    def target(self, target):
        self._target = target

    @property
    def access(self):
        return super().access

    @access.setter
    def access(self, access):
        allowed_values = ["CREATE", "READ", "EXECUTE", "UPDATE", "DELETE"]  # noqa: E501
        if not set(access).issubset(set(allowed_values)):
            raise ValueError(
                "Invalid values for `access` [{0}], must be a subset of [{1}]"  # noqa: E501
                .format(", ".join(map(str, set(access) - set(allowed_values))),  # noqa: E501
                        ", ".join(map(str, allowed_values)))
            )

        self._access = access
