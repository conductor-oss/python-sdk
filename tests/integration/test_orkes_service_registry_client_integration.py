import os
import uuid

import pytest

from conductor.client.adapters.models.request_param_adapter import \
    RequestParamAdapter as RequestParam
from conductor.client.adapters.models.service_method_adapter import \
    ServiceMethodAdapter as ServiceMethod
from conductor.client.adapters.models.service_registry_adapter import (
    Config, OrkesCircuitBreakerConfig)
from conductor.client.adapters.models.service_registry_adapter import \
    ServiceRegistryAdapter as ServiceRegistry
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.service_registry import ServiceType
from conductor.client.http.rest import ApiException
from conductor.client.orkes.orkes_service_registry_client import \
    OrkesServiceRegistryClient


class TestOrkesServiceRegistryClientIntegration:
    """
    Integration tests for OrkesServiceRegistryClient.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest.fixture(scope="class")
    def service_registry_client(
        self, configuration: Configuration
    ) -> OrkesServiceRegistryClient:
        return OrkesServiceRegistryClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_service_name(self, test_suffix: str) -> str:
        return f"test_service_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_http_service(self, test_suffix: str) -> ServiceRegistry:
        circuit_breaker_config = OrkesCircuitBreakerConfig(
            failure_rate_threshold=50.0,
            sliding_window_size=10,
            minimum_number_of_calls=5,
            wait_duration_in_open_state=60,
            permitted_number_of_calls_in_half_open_state=3,
            slow_call_rate_threshold=100.0,
            slow_call_duration_threshold=60,
            automatic_transition_from_open_to_half_open_enabled=True,
            max_wait_duration_in_half_open_state=30,
        )
        config = Config(circuit_breaker_config=circuit_breaker_config)

        return ServiceRegistry(
            name=f"test_http_service_{test_suffix}",
            type=ServiceType.HTTP,
            service_uri="http://localhost:8080/api",
            methods=[],
            request_params=[],
            config=config,
        )

    @pytest.fixture(scope="class")
    def simple_grpc_service(self, test_suffix: str) -> ServiceRegistry:
        circuit_breaker_config = OrkesCircuitBreakerConfig(
            failure_rate_threshold=30.0,
            sliding_window_size=20,
            minimum_number_of_calls=10,
            wait_duration_in_open_state=120,
            permitted_number_of_calls_in_half_open_state=5,
            slow_call_rate_threshold=80.0,
            slow_call_duration_threshold=30,
            automatic_transition_from_open_to_half_open_enabled=False,
            max_wait_duration_in_half_open_state=60,
        )
        config = Config(circuit_breaker_config=circuit_breaker_config)

        return ServiceRegistry(
            name=f"test_grpc_service_{test_suffix}",
            type=ServiceType.GRPC,
            service_uri="grpc://localhost:9090",
            methods=[],
            request_params=[],
            config=config,
        )

    @pytest.fixture(scope="class")
    def sample_service_method(self) -> ServiceMethod:
        request_params = [
            RequestParam(name="id", type="string", required=True),
            RequestParam(name="name", type="string", required=False),
        ]

        return ServiceMethod(
            id=1,
            operation_name="getUser",
            method_name="getUser",
            method_type="GET",
            input_type="string",
            output_type="User",
            request_params=request_params,
            example_input={"id": "123", "name": "John Doe"},
        )

    @pytest.fixture(scope="class")
    def sample_proto_data(self) -> bytes:
        return b"""
            syntax = "proto3";

            package user;

            service UserService {
            rpc GetUser(GetUserRequest) returns (GetUserResponse);
            rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
            }

            message GetUserRequest {
            string id = 1;
            }

            message GetUserResponse {
            string id = 1;
            string name = 2;
            string email = 3;
            }

            message CreateUserRequest {
            string name = 1;
            string email = 2;
            }

            message CreateUserResponse {
            string id = 1;
            string name = 2;
            string email = 3;
            }
            """

    def test_service_lifecycle_http(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        simple_http_service: ServiceRegistry,
    ):
        try:
            service_registry_client.add_or_update_service(simple_http_service)

            retrieved_service = service_registry_client.get_service(
                simple_http_service.name
            )
            assert retrieved_service.name == simple_http_service.name
            assert retrieved_service.type == simple_http_service.type
            assert retrieved_service.service_uri == simple_http_service.service_uri

            all_services = service_registry_client.get_registered_services()
            service_names = [service.name for service in all_services]
            assert simple_http_service.name in service_names

        except Exception as e:
            print(f"Exception in test_service_lifecycle_http: {str(e)}")
            raise
        finally:
            try:
                service_registry_client.remove_service(simple_http_service.name)
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup service {simple_http_service.name}: {str(e)}"
                )

    def test_service_lifecycle_grpc(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        simple_grpc_service: ServiceRegistry,
    ):
        try:
            service_registry_client.add_or_update_service(simple_grpc_service)

            retrieved_service = service_registry_client.get_service(
                simple_grpc_service.name
            )
            assert retrieved_service.name == simple_grpc_service.name
            assert retrieved_service.type == simple_grpc_service.type
            assert retrieved_service.service_uri == simple_grpc_service.service_uri

        except Exception as e:
            print(f"Exception in test_service_lifecycle_grpc: {str(e)}")
            raise
        finally:
            try:
                service_registry_client.remove_service(simple_grpc_service.name)
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup service {simple_grpc_service.name}: {str(e)}"
                )

    def test_service_method_management(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        test_suffix: str,
        sample_service_method: ServiceMethod,
    ):
        service_name = f"test_method_service_{test_suffix}"
        try:
            service = ServiceRegistry(
                name=service_name,
                type=ServiceType.HTTP,
                service_uri="http://localhost:8080/api",
                methods=[],
                request_params=[],
            )

            service_registry_client.add_or_update_service(service)

            service_registry_client.add_or_update_method(
                service_name, sample_service_method
            )

            discovered_methods = service_registry_client.discover(service_name)
            assert len(discovered_methods) >= 1
            method_names = [method.method_name for method in discovered_methods]
            assert sample_service_method.method_name in method_names

            service_registry_client.remove_method(
                service_name,
                sample_service_method.method_name,
                sample_service_method.method_name,
                sample_service_method.method_type,
            )

            discovered_methods_after_remove = service_registry_client.discover(
                service_name
            )
            method_names_after_remove = [
                method.method_name for method in discovered_methods_after_remove
            ]
            assert sample_service_method.method_name not in method_names_after_remove

        except Exception as e:
            print(f"Exception in test_service_method_management: {str(e)}")
            raise
        finally:
            try:
                service_registry_client.remove_service(service_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup service {service_name}: {str(e)}")

    def test_circuit_breaker_operations(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        test_suffix: str,
    ):
        service_name = f"test_circuit_breaker_{test_suffix}"
        try:
            service = ServiceRegistry(
                name=service_name,
                type=ServiceType.HTTP,
                service_uri="http://localhost:8080/api",
                methods=[],
                request_params=[],
            )

            service_registry_client.add_or_update_service(service)

            initial_status = service_registry_client.get_circuit_breaker_status(
                service_name
            )
            assert initial_status is not None

            open_response = service_registry_client.open_circuit_breaker(service_name)
            assert open_response is not None

            open_status = service_registry_client.get_circuit_breaker_status(
                service_name
            )
            assert open_status is not None

            close_response = service_registry_client.close_circuit_breaker(service_name)
            assert close_response is not None

            close_status = service_registry_client.get_circuit_breaker_status(
                service_name
            )
            assert close_status is not None

            is_open = service_registry_client.is_circuit_breaker_open(service_name)
            assert isinstance(is_open, bool)

        except Exception as e:
            print(f"Exception in test_circuit_breaker_operations: {str(e)}")
            raise
        finally:
            try:
                service_registry_client.remove_service(service_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup service {service_name}: {str(e)}")

    def test_proto_management(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        test_suffix: str,
        sample_proto_data: bytes,
    ):
        service_name = f"test_proto_service_{test_suffix}"
        proto_filename = "user_service.proto"
        try:
            service = ServiceRegistry(
                name=service_name,
                type=ServiceType.GRPC,
                service_uri="grpc://localhost:9090",
                methods=[],
                request_params=[],
            )

            service_registry_client.add_or_update_service(service)

            service_registry_client.set_proto_data(
                service_name, proto_filename, sample_proto_data
            )

            retrieved_proto_data = service_registry_client.get_proto_data(
                service_name, proto_filename
            )
            assert retrieved_proto_data == sample_proto_data

            all_protos = service_registry_client.get_all_protos(service_name)
            assert len(all_protos) >= 1
            proto_filenames = [proto.filename for proto in all_protos]
            assert proto_filename in proto_filenames

            service_registry_client.delete_proto(service_name, proto_filename)

            all_protos_after_delete = service_registry_client.get_all_protos(
                service_name
            )
            proto_filenames_after_delete = [
                proto.filename for proto in all_protos_after_delete
            ]
            assert proto_filename not in proto_filenames_after_delete

        except Exception as e:
            print(f"Exception in test_proto_management: {str(e)}")
            raise
        finally:
            try:
                service_registry_client.remove_service(service_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup service {service_name}: {str(e)}")

    def test_service_update(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        test_suffix: str,
    ):
        service_name = f"test_service_update_{test_suffix}"
        try:
            initial_service = ServiceRegistry(
                name=service_name,
                type=ServiceType.HTTP,
                service_uri="http://localhost:8080/api",
                methods=[],
                request_params=[],
            )

            service_registry_client.add_or_update_service(initial_service)

            retrieved_service = service_registry_client.get_service(service_name)
            assert retrieved_service.service_uri == "http://localhost:8080/api"

            updated_service = ServiceRegistry(
                name=service_name,
                type=ServiceType.HTTP,
                service_uri="http://localhost:9090/api",
                methods=[],
                request_params=[],
            )

            service_registry_client.add_or_update_service(updated_service)

            updated_retrieved_service = service_registry_client.get_service(
                service_name
            )
            assert updated_retrieved_service.service_uri == "http://localhost:9090/api"

        except Exception as e:
            print(f"Exception in test_service_update: {str(e)}")
            raise
        finally:
            try:
                service_registry_client.remove_service(service_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup service {service_name}: {str(e)}")

    def test_service_not_found(
        self, service_registry_client: OrkesServiceRegistryClient
    ):
        non_existent_service = f"non_existent_{str(uuid.uuid4())}"

        with pytest.raises(ApiException) as exc_info:
            service_registry_client.get_service(non_existent_service)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            service_registry_client.remove_service(non_existent_service)
        assert exc_info.value.code == 404

        with pytest.raises(ApiException) as exc_info:
            service_registry_client.get_circuit_breaker_status(non_existent_service)
        assert exc_info.value.code == 404

    def test_concurrent_service_operations(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        test_suffix: str,
    ):
        try:
            import threading
            import time

            results = []
            errors = []
            created_services = []
            cleanup_lock = threading.Lock()

            def create_and_delete_service(service_suffix: str):
                service_name = None
                try:
                    service_name = f"concurrent_service_{service_suffix}"
                    service = ServiceRegistry(
                        name=service_name,
                        type=ServiceType.HTTP,
                        service_uri=f"http://localhost:808{service_suffix}/api",
                        methods=[],
                        request_params=[],
                    )

                    service_registry_client.add_or_update_service(service)

                    with cleanup_lock:
                        created_services.append(service_name)

                    time.sleep(0.1)

                    retrieved_service = service_registry_client.get_service(
                        service_name
                    )
                    assert retrieved_service.name == service_name

                    if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                        try:
                            service_registry_client.remove_service(service_name)
                            with cleanup_lock:
                                if service_name in created_services:
                                    created_services.remove(service_name)
                        except Exception as cleanup_error:
                            print(
                                f"Warning: Failed to cleanup service {service_name} in thread: {str(cleanup_error)}"
                            )

                    results.append(f"service_{service_suffix}_success")
                except Exception as e:
                    errors.append(f"service_{service_suffix}_error: {str(e)}")
                    if service_name and service_name not in created_services:
                        with cleanup_lock:
                            created_services.append(service_name)

            threads = []
            for i in range(3):
                thread = threading.Thread(
                    target=create_and_delete_service, args=(f"{test_suffix}_{i}",)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            assert (
                len(results) == 3
            ), f"Expected 3 successful operations, got {len(results)}. Errors: {errors}"
            assert len(errors) == 0, f"Unexpected errors: {errors}"

        except Exception as e:
            print(f"Exception in test_concurrent_service_operations: {str(e)}")
            raise
        finally:
            for service_name in created_services:
                try:
                    service_registry_client.remove_service(service_name)
                except Exception as e:
                    print(f"Warning: Failed to delete service {service_name}: {str(e)}")

    def test_complex_service_management_flow(
        self, service_registry_client: OrkesServiceRegistryClient, test_suffix: str
    ):
        created_resources = {"services": []}

        try:
            service_types = {
                "user_service": ServiceType.HTTP,
                "payment_service": ServiceType.HTTP,
                "notification_service": ServiceType.GRPC,
                "analytics_service": ServiceType.GRPC,
            }

            for service_type_name, service_type in service_types.items():
                service_name = f"complex_{service_type_name}_{test_suffix}"
                service_uri = (
                    f"http://localhost:8080/{service_type_name}"
                    if service_type == ServiceType.HTTP
                    else f"grpc://localhost:9090/{service_type_name}"
                )

                service = ServiceRegistry(
                    name=service_name,
                    type=service_type,
                    service_uri=service_uri,
                    methods=[],
                    request_params=[],
                )

                service_registry_client.add_or_update_service(service)
                created_resources["services"].append(service_name)

            all_services = service_registry_client.get_registered_services()
            service_names = [service.name for service in all_services]
            for service_name in created_resources["services"]:
                assert (
                    service_name in service_names
                ), f"Service {service_name} not found in list"

            for service_type_name, service_type in service_types.items():
                service_name = f"complex_{service_type_name}_{test_suffix}"
                retrieved_service = service_registry_client.get_service(service_name)
                assert retrieved_service.name == service_name
                assert retrieved_service.type == service_type

            bulk_services = []
            for i in range(3):
                service_name = f"bulk_service_{i}_{test_suffix}"
                service = ServiceRegistry(
                    name=service_name,
                    type=ServiceType.HTTP,
                    service_uri=f"http://localhost:808{i}/api",
                    methods=[],
                    request_params=[],
                )
                service_registry_client.add_or_update_service(service)
                bulk_services.append(service_name)
                created_resources["services"].append(service_name)

            all_services_after_bulk = service_registry_client.get_registered_services()
            service_names_after_bulk = [
                service.name for service in all_services_after_bulk
            ]
            for service_name in bulk_services:
                assert (
                    service_name in service_names_after_bulk
                ), f"Bulk service {service_name} not found in list"

            queue_sizes = service_registry_client.get_queue_sizes_for_all_tasks()
            assert isinstance(queue_sizes, dict)

            for service_type_name in ["user_service", "payment_service"]:
                service_name = f"complex_{service_type_name}_{test_suffix}"
                status = service_registry_client.get_circuit_breaker_status(
                    service_name
                )
                assert status is not None

        except Exception as e:
            print(f"Exception in test_complex_service_management_flow: {str(e)}")
            raise
        finally:
            self._perform_comprehensive_cleanup(
                service_registry_client, created_resources
            )

    def _perform_comprehensive_cleanup(
        self,
        service_registry_client: OrkesServiceRegistryClient,
        created_resources: dict,
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for service_name in created_resources["services"]:
            try:
                service_registry_client.remove_service(service_name)
            except Exception as e:
                print(f"Warning: Failed to delete service {service_name}: {str(e)}")

        remaining_services = []
        for service_name in created_resources["services"]:
            try:
                service_registry_client.get_service(service_name)
                remaining_services.append(service_name)
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_services.append(service_name)
            except Exception:
                remaining_services.append(service_name)

        if remaining_services:
            print(
                f"Warning: {len(remaining_services)} services could not be verified as deleted: {remaining_services}"
            )
