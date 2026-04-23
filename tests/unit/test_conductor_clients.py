from conductor.client.orkes_clients import OrkesClients, ConductorClients
from conductor.client import ConductorClients as ConductorClientsFromPkg
from conductor.client.configuration.configuration import Configuration


def test_alias_is_same_class():
    assert ConductorClients is OrkesClients


def test_package_export_is_same_class():
    assert ConductorClientsFromPkg is OrkesClients


def test_conductor_clients_instantiates():
    config = Configuration(server_api_url='http://localhost:8080/api')
    clients = ConductorClients(configuration=config)
    assert isinstance(clients, OrkesClients)


def test_conductor_clients_default_config():
    clients = ConductorClients()
    assert clients.configuration is not None


def test_conductor_clients_get_methods():
    config = Configuration(server_api_url='http://localhost:8080/api')
    clients = ConductorClients(configuration=config)
    assert clients.get_workflow_executor() is not None
    assert clients.get_workflow_client() is not None
    assert clients.get_task_client() is not None
    assert clients.get_metadata_client() is not None
    assert clients.get_scheduler_client() is not None
    assert clients.get_secret_client() is not None
