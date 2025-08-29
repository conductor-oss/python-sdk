import os
import uuid

import pytest

from conductor.client.http.models.request_param import (
    RequestParamAdapter as RequestParam,
)
from conductor.client.http.models.service_method import (
    ServiceMethodAdapter as ServiceMethod,
)
from conductor.client.http.models.service_registry import (
    Config,
    OrkesCircuitBreakerConfig,
)
from conductor.client.http.models.service_registry import (
    ServiceRegistryAdapter as ServiceRegistry,
)
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.service_registry import ServiceType
from conductor.client.codegen.rest import ApiException
from conductor.client.orkes.orkes_service_registry_client import (
    OrkesServiceRegistryClient,
)


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

    @pytest.mark.v5_2_6
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

    @pytest.mark.v5_2_6
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

    @pytest.mark.v5_2_6
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

    @pytest.mark.v5_2_6
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
