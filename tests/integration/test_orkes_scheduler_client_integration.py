import os
import time
import uuid

import pytest

from conductor.client.http.models.save_schedule_request import \
    SaveScheduleRequestAdapter as SaveScheduleRequest
from conductor.client.http.models.start_workflow_request import \
    StartWorkflowRequestAdapter as StartWorkflowRequest
from conductor.client.configuration.configuration import Configuration
from conductor.client.codegen.rest import ApiException
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient


class TestOrkesSchedulerClientIntegration:
    """
    Integration tests for OrkesSchedulerClient.

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
    def scheduler_client(self, configuration: Configuration) -> OrkesSchedulerClient:
        return OrkesSchedulerClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_schedule_name(self, test_suffix: str) -> str:
        return f"test_schedule_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_start_workflow_request(self) -> StartWorkflowRequest:
        return StartWorkflowRequest(
            name="test_workflow",
            version=1,
            input={"param1": "value1", "param2": "value2"},
            correlation_id="test_correlation_id",
            priority=0,
        )

    @pytest.fixture(scope="class")
    def simple_save_schedule_request(
        self, test_suffix: str, simple_start_workflow_request: StartWorkflowRequest
    ) -> SaveScheduleRequest:
        return SaveScheduleRequest(
            name=f"test_schedule_{test_suffix}",
            cron_expression="0 */5 * * * ?",
            description="A simple test schedule",
            start_workflow_request=simple_start_workflow_request,
            paused=False,
            run_catchup_schedule_instances=True,
            schedule_start_time=int(time.time() * 1000),
            schedule_end_time=int((time.time() + 86400) * 1000),
            zone_id="UTC",
        )

    @pytest.fixture(scope="class")
    def complex_save_schedule_request(
        self, test_suffix: str, simple_start_workflow_request: StartWorkflowRequest
    ) -> SaveScheduleRequest:
        return SaveScheduleRequest(
            name=f"test_complex_schedule_{test_suffix}",
            cron_expression="0 0 12 * * ?",
            description="A complex test schedule that runs daily at noon",
            start_workflow_request=simple_start_workflow_request,
            paused=True,
            run_catchup_schedule_instances=False,
            schedule_start_time=int(time.time() * 1000),
            schedule_end_time=int((time.time() + 604800) * 1000),
            zone_id="America/New_York",
            created_by="integration_test",
            updated_by="integration_test",
        )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_lifecycle_simple(
        self,
        scheduler_client: OrkesSchedulerClient,
        simple_save_schedule_request: SaveScheduleRequest,
    ):
        try:
            scheduler_client.save_schedule(simple_save_schedule_request)

            retrieved_schedule = scheduler_client.get_schedule(
                simple_save_schedule_request.name
            )
            assert retrieved_schedule.name == simple_save_schedule_request.name
            assert (
                retrieved_schedule.cron_expression
                == simple_save_schedule_request.cron_expression
            )
            assert (
                retrieved_schedule.description
                == simple_save_schedule_request.description
            )

            all_schedules = scheduler_client.get_all_schedules()
            schedule_names = [schedule.name for schedule in all_schedules]
            assert simple_save_schedule_request.name in schedule_names

        except Exception as e:
            print(f"Exception in test_schedule_lifecycle_simple: {str(e)}")
            raise
        finally:
            try:
                scheduler_client.delete_schedule(simple_save_schedule_request.name)
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup schedule {simple_save_schedule_request.name}: {str(e)}"
                )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_lifecycle_complex(
        self,
        scheduler_client: OrkesSchedulerClient,
        complex_save_schedule_request: SaveScheduleRequest,
    ):
        try:
            scheduler_client.save_schedule(complex_save_schedule_request)

            retrieved_schedule = scheduler_client.get_schedule(
                complex_save_schedule_request.name
            )
            assert retrieved_schedule.name == complex_save_schedule_request.name
            assert (
                retrieved_schedule.cron_expression
                == complex_save_schedule_request.cron_expression
            )
            assert retrieved_schedule.zone_id == complex_save_schedule_request.zone_id

        except Exception as e:
            print(f"Exception in test_schedule_lifecycle_complex: {str(e)}")
            raise
        finally:
            try:
                scheduler_client.delete_schedule(complex_save_schedule_request.name)
            except Exception as e:
                print(
                    f"Warning: Failed to cleanup schedule {complex_save_schedule_request.name}: {str(e)}"
                )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_pause_resume(
        self,
        scheduler_client: OrkesSchedulerClient,
        test_suffix: str,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        schedule_name = f"test_pause_resume_{test_suffix}"
        try:
            schedule_request = SaveScheduleRequest(
                name=schedule_name,
                cron_expression="0 */10 * * * ?",
                description="Schedule for pause/resume testing",
                start_workflow_request=simple_start_workflow_request,
                paused=False,
            )

            scheduler_client.save_schedule(schedule_request)

            retrieved_schedule = scheduler_client.get_schedule(schedule_name)
            assert not retrieved_schedule.paused

            scheduler_client.pause_schedule(schedule_name)

            paused_schedule = scheduler_client.get_schedule(schedule_name)
            assert paused_schedule.paused

            scheduler_client.resume_schedule(schedule_name)

            resumed_schedule = scheduler_client.get_schedule(schedule_name)
            assert not resumed_schedule.paused

        except Exception as e:
            print(f"Exception in test_schedule_pause_resume: {str(e)}")
            raise
        finally:
            try:
                scheduler_client.delete_schedule(schedule_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup schedule {schedule_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_execution_times(
        self,
        scheduler_client: OrkesSchedulerClient,
    ):
        try:
            cron_expression = "0 0 12 * * ?"
            schedule_start_time = int(time.time() * 1000)
            schedule_end_time = int((time.time() + 86400 * 7) * 1000)
            limit = 5

            execution_times = scheduler_client.get_next_few_schedule_execution_times(
                cron_expression=cron_expression,
                schedule_start_time=schedule_start_time,
                schedule_end_time=schedule_end_time,
                limit=limit,
            )

            assert isinstance(execution_times, list)
            assert len(execution_times) <= limit
            assert all(isinstance(time_ms, int) for time_ms in execution_times)

            execution_times_without_params = (
                scheduler_client.get_next_few_schedule_execution_times(
                    cron_expression=cron_expression,
                )
            )

            assert isinstance(execution_times_without_params, list)
            assert all(
                isinstance(time_ms, int) for time_ms in execution_times_without_params
            )

        except Exception as e:
            print(f"Exception in test_schedule_execution_times: {str(e)}")
            raise

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_search(
        self,
        scheduler_client: OrkesSchedulerClient,
        test_suffix: str,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        schedule_name = f"test_search_schedule_{test_suffix}"
        try:
            schedule_request = SaveScheduleRequest(
                name=schedule_name,
                cron_expression="0 0 8 * * ?",
                description="Schedule for search testing",
                start_workflow_request=simple_start_workflow_request,
                paused=False,
            )

            scheduler_client.save_schedule(schedule_request)

            search_results = scheduler_client.search_schedule_executions(
                start=0, size=10, sort="startTime", query=1
            )

            assert search_results is not None
            assert hasattr(search_results, "total_hits")
            assert hasattr(search_results, "results")

            search_results_with_query = scheduler_client.search_schedule_executions(
                start=0,
                size=5,
                query=f"name:{schedule_name}",
            )

            assert search_results_with_query is not None

        except Exception as e:
            print(f"Exception in test_schedule_search: {str(e)}")
            raise
        finally:
            try:
                scheduler_client.delete_schedule(schedule_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup schedule {schedule_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_tags(
        self,
        scheduler_client: OrkesSchedulerClient,
        test_suffix: str,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        schedule_name = f"test_tagged_schedule_{test_suffix}"
        try:
            schedule_request = SaveScheduleRequest(
                name=schedule_name,
                cron_expression="0 0 6 * * ?",
                description="Schedule with tags",
                start_workflow_request=simple_start_workflow_request,
                paused=False,
            )

            scheduler_client.save_schedule(schedule_request)

            tags = [
                MetadataTag("environment", "test"),
                MetadataTag("team", "backend"),
                MetadataTag("priority", "high"),
            ]

            scheduler_client.set_scheduler_tags(tags, schedule_name)

            retrieved_tags = scheduler_client.get_scheduler_tags(schedule_name)
            assert len(retrieved_tags) >= 3
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "environment" in tag_keys
            assert "team" in tag_keys
            assert "priority" in tag_keys

            tags_to_delete = [MetadataTag("priority", "high")]
            scheduler_client.delete_scheduler_tags(tags_to_delete, schedule_name)

            retrieved_tags_after_delete = scheduler_client.get_scheduler_tags(
                schedule_name
            )
            remaining_tag_keys = [tag.key for tag in retrieved_tags_after_delete]
            assert "priority" not in remaining_tag_keys

        except Exception as e:
            print(f"Exception in test_schedule_tags: {str(e)}")
            raise
        finally:
            try:
                scheduler_client.delete_schedule(schedule_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup schedule {schedule_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_schedule_update(
        self,
        scheduler_client: OrkesSchedulerClient,
        test_suffix: str,
        simple_start_workflow_request: StartWorkflowRequest,
    ):
        schedule_name = f"test_update_schedule_{test_suffix}"
        try:
            initial_schedule = SaveScheduleRequest(
                name=schedule_name,
                cron_expression="0 0 9 * * ?",
                description="Initial schedule",
                start_workflow_request=simple_start_workflow_request,
                paused=False,
            )

            scheduler_client.save_schedule(initial_schedule)

            retrieved_schedule = scheduler_client.get_schedule(schedule_name)
            assert retrieved_schedule.description == "Initial schedule"

            updated_schedule = SaveScheduleRequest(
                name=schedule_name,
                cron_expression="0 0 10 * * ?",
                description="Updated schedule",
                start_workflow_request=simple_start_workflow_request,
                paused=True,
            )

            scheduler_client.save_schedule(updated_schedule)

            updated_retrieved_schedule = scheduler_client.get_schedule(schedule_name)
            assert updated_retrieved_schedule.description == "Updated schedule"
            assert updated_retrieved_schedule.paused

        except Exception as e:
            print(f"Exception in test_schedule_update: {str(e)}")
            raise
        finally:
            try:
                scheduler_client.delete_schedule(schedule_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup schedule {schedule_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_complex_schedule_management_flow(
        self, scheduler_client: OrkesSchedulerClient, test_suffix: str
    ):
        created_resources = {"schedules": []}

        try:
            schedule_types = {
                "daily": "0 0 8 * * ?",
                "hourly": "0 0 * * * ?",
                "weekly": "0 0 9 ? * MON",
                "monthly": "0 0 10 1 * ?",
            }

            for schedule_type, cron_expression in schedule_types.items():
                schedule_name = f"complex_{schedule_type}_{test_suffix}"
                start_workflow_request = StartWorkflowRequest(
                    name="test_workflow",
                    version=1,
                    input={
                        "schedule_type": schedule_type,
                        "timestamp": int(time.time()),
                    },
                    correlation_id=f"correlation_{schedule_type}",
                    priority=0,
                )

                schedule_request = SaveScheduleRequest(
                    name=schedule_name,
                    cron_expression=cron_expression,
                    description=f"Complex {schedule_type} schedule",
                    start_workflow_request=start_workflow_request,
                    paused=False,
                    run_catchup_schedule_instances=True,
                    schedule_start_time=int(time.time() * 1000),
                    schedule_end_time=int((time.time() + 2592000) * 1000),
                    zone_id="UTC",
                )

                scheduler_client.save_schedule(schedule_request)
                created_resources["schedules"].append(schedule_name)

                tags = [
                    MetadataTag("type", schedule_type),
                    MetadataTag("environment", "test"),
                    MetadataTag("owner", "integration_test"),
                ]

                scheduler_client.set_scheduler_tags(tags, schedule_name)

            all_schedules = scheduler_client.get_all_schedules()
            schedule_names = [schedule.name for schedule in all_schedules]
            for schedule_name in created_resources["schedules"]:
                assert (
                    schedule_name in schedule_names
                ), f"Schedule {schedule_name} not found in list"

            for schedule_type in schedule_types.keys():
                schedule_name = f"complex_{schedule_type}_{test_suffix}"
                retrieved_schedule = scheduler_client.get_schedule(schedule_name)
                assert retrieved_schedule.name == schedule_name

                retrieved_tags = scheduler_client.get_scheduler_tags(schedule_name)
                tag_keys = [tag.key for tag in retrieved_tags]
                assert "type" in tag_keys
                assert "environment" in tag_keys
                assert "owner" in tag_keys

            bulk_schedules = []
            for i in range(3):
                schedule_name = f"bulk_schedule_{i}_{test_suffix}"
                start_workflow_request = StartWorkflowRequest(
                    name="test_workflow",
                    version=1,
                    input={"bulk_index": i},
                    correlation_id=f"bulk_correlation_{i}",
                    priority=0,
                )

                schedule_request = SaveScheduleRequest(
                    name=schedule_name,
                    cron_expression=f"0 */{15 + i} * * * ?",
                    description=f"Bulk schedule {i}",
                    start_workflow_request=start_workflow_request,
                    paused=False,
                )

                scheduler_client.save_schedule(schedule_request)
                bulk_schedules.append(schedule_name)
                created_resources["schedules"].append(schedule_name)

            all_schedules_after_bulk = scheduler_client.get_all_schedules()
            schedule_names_after_bulk = [
                schedule.name for schedule in all_schedules_after_bulk
            ]
            for schedule_name in bulk_schedules:
                assert (
                    schedule_name in schedule_names_after_bulk
                ), f"Bulk schedule {schedule_name} not found in list"

            scheduler_client.requeue_all_execution_records()

            for schedule_type in ["daily", "hourly"]:
                schedule_name = f"complex_{schedule_type}_{test_suffix}"
                execution_times = (
                    scheduler_client.get_next_few_schedule_execution_times(
                        cron_expression=schedule_types[schedule_type],
                        limit=3,
                    )
                )
                assert isinstance(execution_times, list)
                assert len(execution_times) <= 3

        except Exception as e:
            print(f"Exception in test_complex_schedule_management_flow: {str(e)}")
            raise
        finally:
            self._perform_comprehensive_cleanup(scheduler_client, created_resources)

    def _perform_comprehensive_cleanup(
        self, scheduler_client: OrkesSchedulerClient, created_resources: dict
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for schedule_name in created_resources["schedules"]:
            try:
                scheduler_client.delete_schedule(schedule_name)
            except Exception as e:
                print(f"Warning: Failed to delete schedule {schedule_name}: {str(e)}")

        remaining_schedules = []
        for schedule_name in created_resources["schedules"]:
            try:
                scheduler_client.get_schedule(schedule_name)
                remaining_schedules.append(schedule_name)
            except ApiException as e:
                if e.code == 404:
                    pass
                else:
                    remaining_schedules.append(schedule_name)
            except Exception:
                remaining_schedules.append(schedule_name)

        if remaining_schedules:
            print(
                f"Warning: {len(remaining_schedules)} schedules could not be verified as deleted: {remaining_schedules}"
            )
