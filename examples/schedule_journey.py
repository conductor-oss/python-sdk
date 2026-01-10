#!/usr/bin/env python3
"""
Schedule Management Journey - Comprehensive Example

This example demonstrates all 15 Schedule Management APIs through a narrative journey
of building an automated e-commerce order processing system with scheduled workflows.

APIs Covered (100%):
1. save_schedule() - Create/update schedules
2. get_schedule() - Retrieve specific schedule
3. get_all_schedules() - List all schedules
4. delete_schedule() - Remove schedule
5. pause_schedule() - Pause specific schedule
6. pause_all_schedules() - Pause all schedules
7. resume_schedule() - Resume specific schedule
8. resume_all_schedules() - Resume all schedules
9. get_next_few_schedule_execution_times() - Preview execution times
10. search_schedule_executions() - Search execution history
11. requeue_all_execution_records() - Requeue executions
12. set_scheduler_tags() - Set schedule tags
13. get_scheduler_tags() - Get schedule tags
14. delete_scheduler_tags() - Remove schedule tags
15. (Workflow filtering in get_all_schedules)

Run:
    python examples/schedule_journey.py
    python examples/schedule_journey.py --no-cleanup  # Keep schedules for inspection
"""

import os
import sys
import time
import argparse
from typing import List, Optional
from datetime import datetime, timedelta

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_scheduler_client import OrkesSchedulerClient
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.http.models.save_schedule_request import SaveScheduleRequest
from conductor.client.http.models.start_workflow_request import StartWorkflowRequest
from conductor.client.http.models.workflow_schedule import WorkflowSchedule
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.orkes.models.metadata_tag import MetadataTag


class ScheduleJourney:
    """
    A comprehensive journey through all Schedule Management APIs.

    Story: Building an automated e-commerce order processing system with various
    scheduled workflows for order processing, inventory checks, and reporting.
    """

    def __init__(self):
        """Initialize the clients."""
        # Get configuration from environment
        server_url = os.getenv('CONDUCTOR_SERVER_URL', 'http://localhost:8080/api')
        key_id = os.getenv('CONDUCTOR_AUTH_KEY')
        key_secret = os.getenv('CONDUCTOR_AUTH_SECRET')

        # Create configuration
        if key_id and key_secret:
            auth = AuthenticationSettings(key_id=key_id, key_secret=key_secret)
            config = Configuration(server_api_url=server_url, authentication_settings=auth)
        else:
            config = Configuration(server_api_url=server_url)

        # Initialize clients
        self.scheduler_client = OrkesSchedulerClient(config)
        self.metadata_client = OrkesMetadataClient(config)

        # Track created resources for cleanup
        self.created_schedules = []
        self.created_workflows = []

        print("=" * 80)
        print("🚀 SCHEDULE MANAGEMENT JOURNEY")
        print("=" * 80)
        print(f"Server: {server_url}")
        print()

    def _get_schedule_attr(self, schedule, attr_name, dict_key=None):
        """Helper to get attribute from schedule object or dict."""
        if isinstance(schedule, dict):
            # Map attribute names to dict keys
            key_mapping = {
                'name': 'name',
                'cron_expression': 'cronExpression',
                'zone_id': 'zoneId',
                'paused': 'paused',
                'next_execution_time': 'nextExecutionTime',
                'description': 'description'
            }
            key = dict_key or key_mapping.get(attr_name, attr_name)
            return schedule.get(key)
        else:
            return getattr(schedule, attr_name, None)

    def chapter1_setup_workflows(self):
        """Chapter 1: Create workflows that will be scheduled."""
        print("📖 CHAPTER 1: Setting Up Workflows")
        print("-" * 40)

        # Create order processing workflow
        order_workflow = WorkflowDef(
            name='scheduled_order_processing',
            version=1,
            description='Process pending orders in batches',
            tasks=[
                WorkflowTask(
                    name='fetch_pending_orders',
                    task_reference_name='fetch_orders_ref',
                    type='SIMPLE'
                ),
                WorkflowTask(
                    name='process_batch',
                    task_reference_name='process_batch_ref',
                    type='SIMPLE'
                )
            ]
        )

        # Create inventory check workflow
        inventory_workflow = WorkflowDef(
            name='scheduled_inventory_check',
            version=1,
            description='Check and update inventory levels',
            tasks=[
                WorkflowTask(
                    name='scan_inventory',
                    task_reference_name='scan_inventory_ref',
                    type='SIMPLE'
                )
            ]
        )

        # Create report generation workflow
        report_workflow = WorkflowDef(
            name='scheduled_report_generation',
            version=1,
            description='Generate daily/weekly reports',
            tasks=[
                WorkflowTask(
                    name='generate_report',
                    task_reference_name='generate_report_ref',
                    type='SIMPLE'
                )
            ]
        )

        # Register workflows
        try:
            self.metadata_client.register_workflow_def(order_workflow, overwrite=True)
            self.created_workflows.append(('scheduled_order_processing', 1))
            print("✅ Created order processing workflow")

            self.metadata_client.register_workflow_def(inventory_workflow, overwrite=True)
            self.created_workflows.append(('scheduled_inventory_check', 1))
            print("✅ Created inventory check workflow")

            self.metadata_client.register_workflow_def(report_workflow, overwrite=True)
            self.created_workflows.append(('scheduled_report_generation', 1))
            print("✅ Created report generation workflow")
        except Exception as e:
            print(f"⚠️  Workflows may already exist: {e}")

        print()

    def chapter2_create_schedules(self):
        """Chapter 2: Create various schedules (API: save_schedule)."""
        print("📖 CHAPTER 2: Creating Schedules")
        print("-" * 40)

        # 1. Daily order processing at midnight
        order_schedule = SaveScheduleRequest(
            name="daily_order_batch",
            description="Process all pending orders daily at midnight",
            cron_expression="0 0 0 * * ?",  # Daily at midnight (Spring cron format)
            zone_id="America/New_York",
            start_workflow_request=StartWorkflowRequest(
                name="scheduled_order_processing",
                version=1,
                input={
                    "batch_type": "daily",
                    "source": "scheduled",
                    "max_orders": 1000
                },
                correlation_id="DAILY_ORDER_BATCH"
            ),
            paused=False
        )

        # 2. Hourly inventory check
        inventory_schedule = SaveScheduleRequest(
            name="hourly_inventory_check",
            description="Check inventory levels every hour",
            cron_expression="0 0 * * * ?",  # Every hour (Spring cron format)
            zone_id="America/New_York",
            start_workflow_request=StartWorkflowRequest(
                name="scheduled_inventory_check",
                version=1,
                input={
                    "check_type": "regular",
                    "alert_threshold": 10
                }
            ),
            paused=False
        )

        # 3. Weekly report on Mondays
        weekly_report_schedule = SaveScheduleRequest(
            name="weekly_sales_report",
            description="Generate weekly sales report every Monday at 9 AM",
            cron_expression="0 0 9 ? * MON",  # Mondays at 9 AM (Spring cron format)
            zone_id="America/New_York",
            start_workflow_request=StartWorkflowRequest(
                name="scheduled_report_generation",
                version=1,
                input={
                    "report_type": "weekly_sales",
                    "format": "pdf"
                }
            ),
            paused=True  # Start paused, will resume later
        )

        # 4. Daily report at 6 PM
        daily_report_schedule = SaveScheduleRequest(
            name="daily_summary_report",
            description="Generate daily summary report at 6 PM",
            cron_expression="0 0 18 * * ?",  # Daily at 6 PM (Spring cron format)
            zone_id="America/New_York",
            start_workflow_request=StartWorkflowRequest(
                name="scheduled_report_generation",
                version=1,
                input={
                    "report_type": "daily_summary",
                    "format": "email"
                }
            ),
            paused=False
        )

        # Save all schedules
        self.scheduler_client.save_schedule(order_schedule)
        self.created_schedules.append("daily_order_batch")
        print("✅ Created daily order batch schedule")

        self.scheduler_client.save_schedule(inventory_schedule)
        self.created_schedules.append("hourly_inventory_check")
        print("✅ Created hourly inventory check schedule")

        self.scheduler_client.save_schedule(weekly_report_schedule)
        self.created_schedules.append("weekly_sales_report")
        print("✅ Created weekly sales report schedule (paused)")

        self.scheduler_client.save_schedule(daily_report_schedule)
        self.created_schedules.append("daily_summary_report")
        print("✅ Created daily summary report schedule")

        print()

    def chapter3_retrieve_schedules(self):
        """Chapter 3: Retrieve schedules (APIs: get_schedule, get_all_schedules)."""
        print("📖 CHAPTER 3: Retrieving Schedules")
        print("-" * 40)

        # Get specific schedule
        print("Getting daily order batch schedule...")
        schedule = self.scheduler_client.get_schedule("daily_order_batch")
        if schedule:
            print(f"  📅 Name: {self._get_schedule_attr(schedule, 'name')}")
            print(f"  ⏰ Cron: {self._get_schedule_attr(schedule, 'cron_expression')}")
            print(f"  🌍 TimeZone: {self._get_schedule_attr(schedule, 'zone_id')}")
            print(f"  ⏸️ Paused: {self._get_schedule_attr(schedule, 'paused')}")

            # Check if tags are present in the schedule object
            if hasattr(schedule, 'tags') and schedule.tags:
                print(f"  🏷️ Tags in schedule: {len(schedule.tags)}")
                for tag in schedule.tags[:3]:  # Show first 3 tags
                    if hasattr(tag, 'key') and hasattr(tag, 'value'):
                        print(f"    - {tag.key}: {tag.value}")

            next_exec = self._get_schedule_attr(schedule, 'next_execution_time')
            if next_exec:
                next_time = datetime.fromtimestamp(next_exec / 1000)
                print(f"  ⏭️ Next Run: {next_time}")
        print()

        # Get all schedules
        print("Getting all schedules...")
        all_schedules = self.scheduler_client.get_all_schedules()
        if all_schedules is None:
            all_schedules = []
        print(f"Found {len(all_schedules)} total schedules")
        for sched in all_schedules[:5]:  # Show first 5
            name = self._get_schedule_attr(sched, 'name')
            cron = self._get_schedule_attr(sched, 'cron_expression')
            paused = self._get_schedule_attr(sched, 'paused')
            print(f"  - {name}: {cron} (Paused: {paused})")
        print()

        # Get schedules for specific workflow
        print("Getting schedules for report generation workflow...")
        report_schedules = self.scheduler_client.get_all_schedules("scheduled_report_generation")
        if report_schedules is None:
            report_schedules = []
        print(f"Found {len(report_schedules)} schedules for report generation")
        for sched in report_schedules:
            name = self._get_schedule_attr(sched, 'name')
            desc = self._get_schedule_attr(sched, 'description')
            print(f"  - {name}: {desc}")
        print()

    def chapter4_preview_execution_times(self):
        """Chapter 4: Preview future execution times (API: get_next_few_schedule_execution_times)."""
        print("📖 CHAPTER 4: Previewing Execution Times")
        print("-" * 40)

        # Preview daily schedule
        print("Next 5 executions for daily midnight schedule:")
        next_times = self.scheduler_client.get_next_few_schedule_execution_times(
            cron_expression="0 0 0 * * ?",
            schedule_start_time=int(time.time() * 1000),
            limit=5
        )
        if next_times:
            for timestamp in next_times:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  📅 {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            print("  No execution times returned")
        print()

        # Preview hourly schedule
        print("Next 10 executions for hourly schedule:")
        next_times = self.scheduler_client.get_next_few_schedule_execution_times(
            cron_expression="0 0 * * * ?",
            schedule_start_time=int(time.time() * 1000),
            limit=10
        )
        if next_times:
            for i, timestamp in enumerate(next_times[:5], 1):  # Show first 5
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            if len(next_times) > 5:
                print(f"  ... and {len(next_times) - 5} more")
        else:
            print("  No execution times returned")
        print()

        # Preview with end time (next 7 days only)
        print("Executions in next 7 days for weekly schedule:")
        seven_days_later = int((time.time() + 7 * 24 * 3600) * 1000)
        next_times = self.scheduler_client.get_next_few_schedule_execution_times(
            cron_expression="0 0 9 ? * MON",
            schedule_start_time=int(time.time() * 1000),
            schedule_end_time=seven_days_later,
            limit=10
        )
        if next_times:
            for timestamp in next_times:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  📅 {dt.strftime('%A, %Y-%m-%d %H:%M')}")
        else:
            print("  No executions in next 7 days")
        print()

    def chapter5_tag_management(self):
        """Chapter 5: Manage schedule tags (APIs: set_scheduler_tags, get_scheduler_tags, delete_scheduler_tags)."""
        print("📖 CHAPTER 5: Tag Management")
        print("-" * 40)

        # Set tags on daily order batch
        print("Setting tags on daily order batch schedule...")
        tags = [
            MetadataTag("environment", "production"),
            MetadataTag("priority", "high"),
            MetadataTag("team", "order-processing"),
            MetadataTag("cost-center", "operations")
        ]
        self.scheduler_client.set_scheduler_tags(tags, "daily_order_batch")
        print("✅ Set 4 tags on daily order batch")

        # Set tags on inventory check
        print("\nSetting tags on inventory check schedule...")
        inventory_tags = [
            MetadataTag("environment", "production"),
            MetadataTag("priority", "medium"),
            MetadataTag("team", "inventory-management"),
            MetadataTag("alert-enabled", "true")
        ]
        self.scheduler_client.set_scheduler_tags(inventory_tags, "hourly_inventory_check")
        print("✅ Set 4 tags on inventory check")

        # Get tags using the dedicated API
        print("\nRetrieving tags using get_scheduler_tags()...")
        retrieved_tags = self.scheduler_client.get_scheduler_tags("daily_order_batch")
        if retrieved_tags:
            print(f"Found {len(retrieved_tags)} tags:")
            for tag in retrieved_tags:
                print(f"  🏷️ {tag.key}: {tag.value}")
        else:
            print("No tags found")

        # Verify tags are included in the schedule object
        print("\nVerifying tags are included when getting the schedule...")
        schedule = self.scheduler_client.get_schedule("daily_order_batch")
        if schedule:
            if hasattr(schedule, 'tags') and schedule.tags:
                print(f"✅ Tags are included in schedule object: {len(schedule.tags)} tags")
                for tag in schedule.tags[:3]:  # Show first 3
                    if hasattr(tag, 'key') and hasattr(tag, 'value'):
                        print(f"    - {tag.key}: {tag.value}")
            else:
                print("⚠️ Tags not found in schedule object (tags might be managed separately)")
        else:
            print("⚠️ Could not retrieve schedule")

        # Delete specific tags
        print("\nDeleting specific tags from daily order batch...")
        tags_to_delete = [
            MetadataTag("cost-center", "operations"),
            MetadataTag("priority", "high")
        ]
        try:
            remaining_tags = self.scheduler_client.delete_scheduler_tags(
                tags_to_delete,
                "daily_order_batch"
            )
            if remaining_tags is not None:
                print(f"✅ Deleted 2 tags, {len(remaining_tags)} tags remaining:")
                for tag in remaining_tags:
                    print(f"  🏷️ {tag.key}: {tag.value}")
            else:
                print("✅ Deleted tags")
                # Get the remaining tags to verify
                remaining_tags = self.scheduler_client.get_scheduler_tags("daily_order_batch")
                if remaining_tags:
                    print(f"  {len(remaining_tags)} tags remaining:")
                    for tag in remaining_tags:
                        print(f"  🏷️ {tag.key}: {tag.value}")

            # Verify tags are updated in the schedule object after deletion
            print("\nVerifying tags in schedule object after deletion...")
            schedule_after = self.scheduler_client.get_schedule("daily_order_batch")
            if schedule_after and hasattr(schedule_after, 'tags') and schedule_after.tags:
                print(f"✅ Schedule object has {len(schedule_after.tags)} tags after deletion")
                for tag in schedule_after.tags:
                    if hasattr(tag, 'key') and hasattr(tag, 'value'):
                        print(f"    - {tag.key}: {tag.value}")
            else:
                print("  ⚠️ Tags not found in schedule object after deletion")

        except Exception as e:
            print(f"  ⚠️ Could not delete tags: {e}")
        print()

    def chapter6_pause_and_resume(self):
        """Chapter 6: Control schedule execution (APIs: pause_schedule, resume_schedule, pause_all_schedules, resume_all_schedules)."""
        print("📖 CHAPTER 6: Pause and Resume Schedules")
        print("-" * 40)

        # Pause specific schedule
        print("Pausing hourly inventory check...")
        self.scheduler_client.pause_schedule("hourly_inventory_check")
        schedule = self.scheduler_client.get_schedule("hourly_inventory_check")
        print(f"✅ Inventory check paused: {self._get_schedule_attr(schedule, 'paused')}")

        # Resume previously paused schedule
        print("\nResuming weekly sales report...")
        self.scheduler_client.resume_schedule("weekly_sales_report")
        schedule = self.scheduler_client.get_schedule("weekly_sales_report")
        print(f"✅ Weekly report resumed: Paused={self._get_schedule_attr(schedule, 'paused')}")

        # Pause all schedules
        print("\n⏸️ PAUSING ALL SCHEDULES (System maintenance)...")
        self.scheduler_client.pause_all_schedules()
        print("✅ All schedules paused")

        # Verify all are paused
        print("\nVerifying schedules are paused...")
        for schedule_name in self.created_schedules[:3]:  # Check first 3
            schedule = self.scheduler_client.get_schedule(schedule_name)
            print(f"  - {schedule_name}: Paused={self._get_schedule_attr(schedule, 'paused')}")

        # Resume all schedules
        print("\n▶️ RESUMING ALL SCHEDULES...")
        self.scheduler_client.resume_all_schedules()
        print("✅ All schedules resumed")

        # Verify all are resumed
        print("\nVerifying schedules are resumed...")
        for schedule_name in self.created_schedules[:3]:  # Check first 3
            schedule = self.scheduler_client.get_schedule(schedule_name)
            print(f"  - {schedule_name}: Paused={self._get_schedule_attr(schedule, 'paused')}")
        print()

    def chapter7_update_schedule(self):
        """Chapter 7: Update existing schedules (API: save_schedule with existing name)."""
        print("📖 CHAPTER 7: Updating Schedules")
        print("-" * 40)

        # Get current schedule
        print("Current daily order batch schedule:")
        current = self.scheduler_client.get_schedule("daily_order_batch")
        print(f"  Cron: {self._get_schedule_attr(current, 'cron_expression')}")
        print(f"  Description: {self._get_schedule_attr(current, 'description')}")

        # Update the schedule
        print("\nUpdating to run twice daily...")
        updated_schedule = SaveScheduleRequest(
            name="daily_order_batch",  # Same name = update
            description="Process orders at midnight and noon (updated)",
            cron_expression="0 0 0,12 * * ?",  # Midnight and noon (Spring cron format)
            zone_id="America/New_York",
            start_workflow_request=StartWorkflowRequest(
                name="scheduled_order_processing",
                version=1,
                input={
                    "batch_type": "bi-daily",
                    "source": "scheduled",
                    "max_orders": 500,  # Smaller batches
                    "updated": True
                }
            ),
            paused=False
        )

        self.scheduler_client.save_schedule(updated_schedule)
        print("✅ Schedule updated")

        # Verify update
        updated = self.scheduler_client.get_schedule("daily_order_batch")
        print(f"\nUpdated schedule:")
        print(f"  Cron: {self._get_schedule_attr(updated, 'cron_expression')}")
        print(f"  Description: {self._get_schedule_attr(updated, 'description')}")

        # Preview new execution times
        print("\nNext 5 executions with new schedule:")
        next_times = self.scheduler_client.get_next_few_schedule_execution_times(
            cron_expression="0 0 0,12 * * ?",
            schedule_start_time=int(time.time() * 1000),
            limit=5
        )
        if next_times:
            for timestamp in next_times:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  📅 {dt.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("  No execution times returned")
        print()

    def chapter8_search_executions(self):
        """Chapter 8: Search execution history (API: search_schedule_executions)."""
        print("📖 CHAPTER 8: Searching Execution History")
        print("-" * 40)

        # Note: This will only return results if schedules have actually executed
        print("Searching recent executions...")

        try:
            # Search all recent executions
            results = self.scheduler_client.search_schedule_executions(
                start=0,
                size=10,
                query='*',
                sort="startTime:DESC"
            )

            # Handle results that might be dict or None
            if results is None:
                total_hits = 0
                result_list = []
            elif isinstance(results, dict):
                total_hits = results.get('totalHits', 0)
                result_list = results.get('results', [])
            else:
                total_hits = getattr(results, 'total_hits', 0)
                result_list = getattr(results, 'results', [])

            print(f"Total executions found: {total_hits}")
            if result_list:
                print(f"Showing first {len(result_list)} executions:")
                for exec_record in result_list:
                    if isinstance(exec_record, dict):
                        workflow_id = exec_record.get('workflowId')
                        schedule_name = exec_record.get('scheduleName')
                        status = exec_record.get('status')
                        start_time = exec_record.get('startTime')
                    else:
                        workflow_id = getattr(exec_record, 'workflow_id', None)
                        schedule_name = getattr(exec_record, 'schedule_name', None)
                        status = getattr(exec_record, 'status', None)
                        start_time = getattr(exec_record, 'start_time', None)

                    print(f"  - Workflow: {workflow_id}")
                    print(f"    Schedule: {schedule_name}")
                    print(f"    Status: {status}")
                    if start_time:
                        start = datetime.fromtimestamp(start_time / 1000)
                        print(f"    Started: {start}")
            else:
                print("  No executions yet (schedules may not have triggered)")

            # Search with filter
            print("\nSearching for specific schedule executions...")
            filtered_results = self.scheduler_client.search_schedule_executions(
                start=0,
                size=5,
                query="scheduleName='daily_order_batch'",
                sort="startTime:DESC"
            )

            # Handle filtered results
            if filtered_results is None:
                filtered_total = 0
            elif isinstance(filtered_results, dict):
                filtered_total = filtered_results.get('totalHits', 0)
            else:
                filtered_total = getattr(filtered_results, 'total_hits', 0)
            if filtered_total > 0:
                print(f"Found {filtered_total} executions for daily_order_batch")
            else:
                print("No executions found for daily_order_batch yet")

        except Exception as e:
            print(f"  Note: {e}")
            print("  Execution history may be empty if schedules haven't triggered yet")

        print()

    def chapter9_requeue_executions(self):
        """Chapter 9: Requeue execution records (API: requeue_all_execution_records)."""
        print("📖 CHAPTER 9: Requeue Execution Records")
        print("-" * 40)

        print("Requeuing all execution records...")
        try:
            self.scheduler_client.requeue_all_execution_records()
            print("✅ All execution records requeued for retry")
            print("  This will retry any failed or pending executions")
        except Exception as e:
            print(f"  Note: {e}")
            print("  This operation may require special permissions")
        print()

    def chapter10_advanced_patterns(self):
        """Chapter 10: Advanced scheduling patterns."""
        print("📖 CHAPTER 10: Advanced Scheduling Patterns")
        print("-" * 40)

        # Create a complex schedule with specific time range
        print("Creating time-limited campaign schedule...")

        # Campaign runs every 2 hours, but only for next 30 days
        campaign_start = int(time.time() * 1000)
        campaign_end = int((time.time() + 30 * 24 * 3600) * 1000)

        campaign_schedule = SaveScheduleRequest(
            name="black_friday_campaign",
            description="Black Friday campaign - runs every 2 hours for 30 days",
            cron_expression="0 0 */2 * * ?",  # Every 2 hours (Spring cron format)
            zone_id="America/New_York",
            start_workflow_request=StartWorkflowRequest(
                name="scheduled_order_processing",
                version=1,
                input={
                    "campaign": "black_friday",
                    "discount": 25,
                    "priority": "high"
                }
            ),
            schedule_start_time=campaign_start,
            schedule_end_time=campaign_end,
            paused=False
        )

        self.scheduler_client.save_schedule(campaign_schedule)
        self.created_schedules.append("black_friday_campaign")
        print("✅ Created time-limited campaign schedule")

        # Preview executions within campaign period
        print("\nCampaign will run:")
        next_times = self.scheduler_client.get_next_few_schedule_execution_times(
            cron_expression="0 0 */2 * * ?",
            schedule_start_time=campaign_start,
            schedule_end_time=campaign_end,
            limit=5
        )
        if next_times:
            for i, timestamp in enumerate(next_times, 1):
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("  No execution times returned")

        # Tag it appropriately
        campaign_tags = [
            MetadataTag("type", "campaign"),
            MetadataTag("campaign", "black_friday"),
            MetadataTag("auto-expire", "true"),
            MetadataTag("priority", "critical")
        ]
        self.scheduler_client.set_scheduler_tags(campaign_tags, "black_friday_campaign")
        print("\n✅ Tagged campaign schedule")
        print()

    def chapter11_monitoring_and_management(self):
        """Chapter 11: Monitor and manage all schedules."""
        print("📖 CHAPTER 11: Monitoring & Management Dashboard")
        print("-" * 40)

        print("📊 SCHEDULE DASHBOARD")
        print("=" * 60)

        # Get all our schedules
        all_schedules = []
        for schedule_name in self.created_schedules:
            try:
                schedule = self.scheduler_client.get_schedule(schedule_name)
                if schedule:
                    all_schedules.append(schedule)
            except:
                pass

        # Group by status
        active_schedules = [s for s in all_schedules if not self._get_schedule_attr(s, 'paused')]
        paused_schedules = [s for s in all_schedules if self._get_schedule_attr(s, 'paused')]

        print(f"Total Schedules: {len(all_schedules)}")
        print(f"  ✅ Active: {len(active_schedules)}")
        print(f"  ⏸️ Paused: {len(paused_schedules)}")
        print()

        # Show schedule details
        print("ACTIVE SCHEDULES:")
        for schedule in active_schedules:
            name = self._get_schedule_attr(schedule, 'name')
            print(f"\n  📅 {name}")
            print(f"     Cron: {self._get_schedule_attr(schedule, 'cron_expression')}")
            print(f"     Zone: {self._get_schedule_attr(schedule, 'zone_id')}")

            # Get tags
            try:
                tags = self.scheduler_client.get_scheduler_tags(name)
                if tags and len(tags) > 0:
                    tag_str = ", ".join([f"{t.key}={t.value}" for t in tags[:3]])
                    print(f"     Tags: {tag_str}")
            except:
                pass

            # Show next execution
            next_exec = self._get_schedule_attr(schedule, 'next_execution_time')
            if next_exec:
                next_time = datetime.fromtimestamp(next_exec / 1000)
                time_until = next_time - datetime.now()
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                print(f"     Next run: {next_time.strftime('%Y-%m-%d %H:%M')} ({hours}h {minutes}m)")

        if paused_schedules:
            print("\n⏸️ PAUSED SCHEDULES:")
            for schedule in paused_schedules:
                name = self._get_schedule_attr(schedule, 'name')
                print(f"  - {name}")

        print()

    def chapter12_cleanup(self, cleanup=True):
        """Chapter 12: Clean up resources (API: delete_schedule)."""
        print("📖 CHAPTER 12: Cleanup")
        print("-" * 40)

        if not cleanup:
            print("ℹ️ Cleanup skipped (--no-cleanup flag)")
            print("Resources left for inspection:")
            print(f"  - {len(self.created_schedules)} schedules")
            print(f"  - {len(self.created_workflows)} workflows")
            return

        print("Cleaning up created resources...")

        # Delete schedules
        for schedule_name in self.created_schedules:
            try:
                self.scheduler_client.delete_schedule(schedule_name)
                print(f"  ✅ Deleted schedule: {schedule_name}")
            except Exception as e:
                print(f"  ⚠️ Could not delete {schedule_name}: {e}")

        # Delete workflows
        for workflow_name, version in self.created_workflows:
            try:
                self.metadata_client.unregister_workflow_def(workflow_name, version)
                print(f"  ✅ Deleted workflow: {workflow_name} v{version}")
            except Exception as e:
                print(f"  ⚠️ Could not delete {workflow_name}: {e}")

        print("\n✅ Cleanup completed")

    def run_journey(self, cleanup=True):
        """Run the complete schedule management journey."""
        try:
            self.chapter1_setup_workflows()
            self.chapter2_create_schedules()
            self.chapter3_retrieve_schedules()
            self.chapter4_preview_execution_times()
            self.chapter5_tag_management()
            self.chapter6_pause_and_resume()
            self.chapter7_update_schedule()
            self.chapter8_search_executions()
            self.chapter9_requeue_executions()
            self.chapter10_advanced_patterns()
            self.chapter11_monitoring_and_management()

            print("=" * 80)
            print("✅ SCHEDULE MANAGEMENT JOURNEY COMPLETED!")
            print("=" * 80)
            print()
            print("📊 Summary:")
            print(f"  - Created {len(self.created_schedules)} schedules")
            print(f"  - Demonstrated all 15 schedule APIs")
            print(f"  - Covered CRUD operations + advanced patterns")
            print()

        except Exception as e:
            print(f"\n❌ Journey failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.chapter12_cleanup(cleanup)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Schedule Management Journey - Comprehensive Example'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup to keep schedules for inspection'
    )
    args = parser.parse_args()

    journey = ScheduleJourney()
    journey.run_journey(cleanup=not args.no_cleanup)


if __name__ == '__main__':
    main()