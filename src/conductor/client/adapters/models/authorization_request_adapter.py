from conductor.client.http.models import AuthorizationRequest


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
