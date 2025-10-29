from typing import ClassVar, Dict

from conductor.client.codegen.models import ConductorUser


class ConductorUserAdapter(ConductorUser):
    swagger_types: ClassVar[Dict[str, str]] = {
        **ConductorUser.swagger_types,
        "orkes_app": "bool",
        "orkes_api_gateway": "bool",
        "contact_information": "dict(str, str)",
    }

    attribute_map: ClassVar[Dict[str, str]] = {
        **ConductorUser.attribute_map,
        "orkes_app": "orkesApp",
        "orkes_api_gateway": "orkesApiGateway",
        "contact_information": "contactInformation",
    }

    def __init__(
        self,
        application_user=None,
        encrypted_id=None,
        encrypted_id_display_value=None,
        groups=None,
        id=None,
        name=None,
        orkes_workers_app=None,
        roles=None,
        uuid=None,
        orkes_app=None,
        orkes_api_gateway=None,
        contact_information=None,
    ):
        super().__init__(
            application_user,
            encrypted_id,
            encrypted_id_display_value,
            groups,
            id,
            name,
            orkes_workers_app,
            roles,
            uuid,
        )
        self._orkes_app = None
        self._orkes_api_gateway = None
        self._contact_information = None

        if orkes_app is not None:
            self.orkes_app = orkes_app
        if orkes_api_gateway is not None:
            self.orkes_api_gateway = orkes_api_gateway
        if contact_information is not None:
            self.contact_information = contact_information

    @property
    def orkes_app(self):
        return self._orkes_app

    @orkes_app.setter
    def orkes_app(self, orkes_app):
        self._orkes_app = orkes_app

    @property
    def orkes_api_gateway(self):
        return self._orkes_api_gateway

    @orkes_api_gateway.setter
    def orkes_api_gateway(self, orkes_api_gateway):
        self._orkes_api_gateway = orkes_api_gateway

    @property
    def contact_information(self):
        return self._contact_information

    @contact_information.setter
    def contact_information(self, contact_information):
        self._contact_information = contact_information
