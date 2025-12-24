#!/usr/bin/env python3
"""
Metadata Management Journey for Conductor OSS
=============================================

This example demonstrates the core Metadata Management APIs available in
Conductor OSS (Open Source) through a narrative journey of building a
workflow system for an online education platform.

This version is specifically designed for Conductor OSS and doesn't require
Orkes-specific features like authentication or advanced tagging.

APIs Covered:
------------
Workflow Definition:
- register_workflow_def() - Register new workflow
- update_workflow_def() - Update workflow
- get_workflow_def() - Get specific workflow
- get_all_workflow_defs() - List all workflows
- unregister_workflow_def() - Delete workflow

Task Definition:
- register_task_def() - Register new task
- update_task_def() - Update task
- get_task_def() - Get specific task
- get_all_task_defs() - List all tasks
- unregister_task_def() - Delete task

Run:
    python examples/metadata_journey_oss.py
    python examples/metadata_journey_oss.py --no-cleanup  # Keep metadata for inspection
"""

import os
import sys
import time
import argparse
from typing import List, Optional

from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from conductor.client.configuration.configuration import Configuration
from conductor.client.metadata_client import MetadataClient
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.http.models.task_def import TaskDef
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask


class MetadataJourneyOSS:
    """
    A comprehensive journey through Metadata Management APIs in Conductor OSS.

    Story: Building a workflow system for an online education platform
    that handles course enrollment, content delivery, and student assessment.
    """

    def __init__(self):
        """Initialize the client and workflow executor for Conductor OSS."""
        # Get configuration from environment or use localhost
        server_url = os.getenv('CONDUCTOR_SERVER_URL', 'http://localhost:8080/api')

        # Create configuration for Conductor OSS (no authentication needed)
        config = Configuration(server_api_url=server_url)

        # Initialize clients
        self.metadata_client = OrkesMetadataClient(config)
        self.workflow_executor = WorkflowExecutor(config)

        # Track created resources for cleanup
        self.created_workflows = []
        self.created_tasks = []

        print("=" * 80)
        print("🚀 CONDUCTOR OSS METADATA MANAGEMENT JOURNEY")
        print("=" * 80)
        print(f"Server: {server_url}")
        print(f"API Docs: {server_url.replace('/api', '')}/api-docs")
        print()

    def chapter1_register_task_definitions(self):
        """Chapter 1: Register task definitions for the education platform."""
        print("📖 CHAPTER 1: Registering Task Definitions")
        print("-" * 40)

        # Define tasks for our education platform
        tasks = [
            TaskDef(
                name='validate_enrollment_oss',
                description='Validate student enrollment request',
                input_keys=['student_id', 'course_id'],
                output_keys=['valid', 'errors', 'enrollment_id'],
                timeout_seconds=300,
                response_timeout_seconds=30,
                retry_count=3,
                retry_logic='FIXED',
                retry_delay_seconds=10
            ),
            TaskDef(
                name='process_payment_oss',
                description='Process course payment',
                input_keys=['student_id', 'amount', 'payment_method'],
                output_keys=['transaction_id', 'status'],
                timeout_seconds=600,
                response_timeout_seconds=30,
                retry_count=5,
                retry_logic='EXPONENTIAL_BACKOFF',
                retry_delay_seconds=5,
                rate_limit_per_frequency=100,
                rate_limit_frequency_in_seconds=60
            ),
            TaskDef(
                name='assign_instructor_oss',
                description='Assign instructor to student',
                input_keys=['course_id', 'student_level'],
                output_keys=['instructor_id', 'instructor_name'],
                timeout_seconds=180,
                response_timeout_seconds=30,
                retry_count=2,
                concurrent_exec_limit=10
            ),
            TaskDef(
                name='send_notification_oss',
                description='Send notification to student',
                input_keys=['student_email', 'message_type', 'content'],
                output_keys=['sent', 'message_id'],
                timeout_seconds=120,
                retry_count=3,
                response_timeout_seconds=60
            ),
            TaskDef(
                name='setup_course_oss',
                description='Setup course materials and access',
                input_keys=['student_id', 'course_id'],
                output_keys=['course_url', 'materials'],
                timeout_seconds=400,
                response_timeout_seconds=30,
                retry_count=2
            ),
            TaskDef(
                name='evaluate_student_oss',
                description='Evaluate student performance',
                input_keys=['student_id', 'test_results'],
                output_keys=['score', 'grade', 'feedback'],
                timeout_seconds=900,
                response_timeout_seconds=30,
                retry_count=1,
                poll_timeout_seconds=300
            )
        ]

        # Register all tasks
        print("Registering tasks...")
        for task_def in tasks:
            try:
                self.metadata_client.register_task_def(task_def)
                self.created_tasks.append(task_def.name)
                print(f"  ✅ Registered: {task_def.name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ℹ️ Task already exists: {task_def.name}")
                    self.created_tasks.append(task_def.name)
                else:
                    print(f"  ❌ Failed to register {task_def.name}: {e}")

        print(f"\nTotal tasks available: {len(self.created_tasks)}")
        print()

    def chapter2_create_simple_workflow(self):
        """Chapter 2: Create a simple sequential workflow."""
        print("📖 CHAPTER 2: Creating Simple Sequential Workflow")
        print("-" * 40)

        # Create enrollment workflow using ConductorWorkflow builder
        print("Creating basic enrollment workflow...")
        enrollment_workflow = ConductorWorkflow(
            executor=self.workflow_executor,
            name=f'enrollment_basic_oss_{time.strftime("%Y%m%d-%H%M%S")}',
            version=1,
            description='Basic student enrollment workflow'
        )

        # Add tasks sequentially
        enrollment_workflow >> SimpleTask('validate_enrollment_oss', 'validate_ref')
        enrollment_workflow >> SimpleTask('process_payment_oss', 'payment_ref')
        enrollment_workflow >> SimpleTask('assign_instructor_oss', 'instructor_ref')
        enrollment_workflow >> SimpleTask('send_notification_oss', 'notification_ref')
        enrollment_workflow >> SimpleTask('setup_course_oss', 'setup_ref')

        # Set input parameters
        enrollment_workflow.input_parameters([
            'student_id',
            'course_id',
            'payment_method',
            'student_email'
        ])

        # Register the workflow
        workflow_def = enrollment_workflow.to_workflow_def()
        try:
            self.metadata_client.register_workflow_def(workflow_def, overwrite=True)
            self.created_workflows.append(('enrollment_basic_oss', 1))
            print("✅ Registered basic enrollment workflow")
        except Exception as e:
            print(f"❌ Failed to register workflow: {e}")

        print()

    def chapter3_create_decision_workflow(self):
        """Chapter 3: Create workflow with decision logic."""
        print("📖 CHAPTER 3: Creating Workflow with Decision Logic")
        print("-" * 40)

        print("Creating assessment workflow with decisions...")

        assessment_workflow = WorkflowDef(
            name=f'assessment_workflow_oss_{time.strftime("%Y%m%d-%H%M%S")}',
            version=1,
            description='Student assessment with grade-based paths',
            input_parameters=['student_id', 'course_id', 'test_results'],
            timeout_seconds=3600,
            tasks=[
                # First evaluate the student
                WorkflowTask(
                    name='evaluate_student_oss',
                    task_reference_name='evaluation',
                    input_parameters={
                        'student_id': '${workflow.input.student_id}',
                        'test_results': '${workflow.input.test_results}'
                    }
                ),
                # Then make decision based on grade
                WorkflowTask(
                    name='DECISION',
                    task_reference_name='grade_decision',
                    type='DECISION',
                    case_value_param='evaluation.output.grade',
                    decision_cases={
                        'A': [
                            WorkflowTask(
                                name='send_notification_oss',
                                task_reference_name='notify_excellence',
                                input_parameters={
                                    'message_type': 'excellence',
                                    'content': 'Congratulations on your excellent performance!'
                                }
                            )
                        ],
                        'B': [
                            WorkflowTask(
                                name='send_notification_oss',
                                task_reference_name='notify_good',
                                input_parameters={
                                    'message_type': 'good_performance',
                                    'content': 'Good job on your assessment!'
                                }
                            )
                        ],
                        'C': [
                            WorkflowTask(
                                name='setup_course_oss',
                                task_reference_name='remedial_setup',
                                input_parameters={
                                    'course_id': 'remedial_${workflow.input.course_id}'
                                }
                            )
                        ]
                    },
                    default_case=[
                        WorkflowTask(
                            name='send_notification_oss',
                            task_reference_name='notify_retry',
                            input_parameters={
                                'message_type': 'retry_required',
                                'content': 'Please schedule a retry for the assessment'
                            }
                        )
                    ]
                )
            ]
        )

        try:
            self.metadata_client.register_workflow_def(assessment_workflow, overwrite=True)
            self.created_workflows.append(('assessment_workflow_oss', 1))
            print("✅ Registered assessment workflow with decision logic")
        except Exception as e:
            print(f"❌ Failed to register workflow: {e}")

        print()

    def chapter4_create_parallel_workflow(self):
        """Chapter 4: Create workflow with parallel execution."""
        print("📖 CHAPTER 4: Creating Workflow with Parallel Tasks")
        print("-" * 40)

        print("Creating onboarding workflow with parallel tasks...")

        onboarding_workflow = WorkflowDef(
            name=f'student_onboarding_oss_{time.strftime("%Y%m%d-%H%M%S")}',
            version=1,
            description='Parallel student onboarding tasks',
            input_parameters=['student_id', 'course_id', 'student_email'],
            tasks=[
                # First validate enrollment
                WorkflowTask(
                    name='validate_enrollment_oss',
                    task_reference_name='validate',
                    input_parameters={
                        'student_id': '${workflow.input.student_id}',
                        'course_id': '${workflow.input.course_id}'
                    }
                ),
                # Then run parallel tasks
                WorkflowTask(
                    name='FORK_JOIN',
                    task_reference_name='parallel_onboarding',
                    type='FORK_JOIN',
                    fork_tasks=[
                        # Branch 1: Setup course
                        [
                            WorkflowTask(
                                name='setup_course_oss',
                                task_reference_name='course_setup',
                                input_parameters={
                                    'student_id': '${workflow.input.student_id}',
                                    'course_id': '${workflow.input.course_id}'
                                }
                            )
                        ],
                        # Branch 2: Send welcome email
                        [
                            WorkflowTask(
                                name='send_notification_oss',
                                task_reference_name='welcome_email',
                                input_parameters={
                                    'student_email': '${workflow.input.student_email}',
                                    'message_type': 'welcome',
                                    'content': 'Welcome to the course!'
                                }
                            )
                        ],
                        # Branch 3: Assign instructor
                        [
                            WorkflowTask(
                                name='assign_instructor_oss',
                                task_reference_name='assign',
                                input_parameters={
                                    'course_id': '${workflow.input.course_id}',
                                    'student_level': 'beginner'
                                }
                            )
                        ]
                    ]
                ),
                WorkflowTask(
                    name='JOIN',
                    task_reference_name='join_onboarding',
                    type='JOIN',
                    join_on=['course_setup', 'welcome_email', 'assign']
                )
            ]
        )

        try:
            self.metadata_client.register_workflow_def(onboarding_workflow, overwrite=True)
            self.created_workflows.append(('student_onboarding_oss', 1))
            print("✅ Registered onboarding workflow with parallel tasks")
        except Exception as e:
            print(f"❌ Failed to register workflow: {e}")

        print()

    def chapter5_retrieve_definitions(self):
        """Chapter 5: Retrieve and display metadata."""
        print("📖 CHAPTER 5: Retrieving Metadata Definitions")
        print("-" * 40)

        # Get specific workflow
        print("📋 Retrieving workflow definitions...")
        for workflow_name, version in self.created_workflows:
            try:
                workflow = self.metadata_client.get_workflow_def(workflow_name, version=version)
                print(f"\n✨ {workflow.name} v{workflow.version}")
                print(f"   Description: {workflow.description}")
                print(f"   Tasks: {len(workflow.tasks)}")
                print(f"   Input Parameters: {workflow.input_parameters}")
                if workflow.timeout_seconds:
                    print(f"   Timeout: {workflow.timeout_seconds}s")
            except Exception as e:
                print(f"   ❌ Could not retrieve {workflow_name}: {e}")

        # Get all workflows
        print("\n📋 Listing all workflows in system...")
        try:
            all_workflows = self.metadata_client.get_all_workflow_defs()
            print(f"Total workflows in system: {len(all_workflows)}")

            # Show our workflows
            our_workflows = [w for w in all_workflows
                           if any(w.name == name for name, _ in self.created_workflows)]
            if our_workflows:
                print("Our workflows:")
                for wf in our_workflows:
                    task_types = set()
                    for task in wf.tasks:
                        task_types.add(task.type if hasattr(task, 'type') and task.type else 'SIMPLE')
                    print(f"  - {wf.name}: {', '.join(task_types)} tasks")
        except Exception as e:
            print(f"❌ Could not list workflows: {e}")

        # Get task definitions
        print("\n📋 Retrieving task definitions...")
        try:
            all_tasks = self.metadata_client.get_all_task_defs()
            our_tasks = [t for t in all_tasks if t.name in self.created_tasks]
            print(f"Our tasks ({len(our_tasks)} total):")
            for task in our_tasks[:5]:  # Show first 5
                retry_info = f"retry={task.retry_count}" if task.retry_count else "no-retry"
                print(f"  - {task.name}: {retry_info}, timeout={task.timeout_seconds}s")
            if len(our_tasks) > 5:
                print(f"  ... and {len(our_tasks) - 5} more")
        except Exception as e:
            print(f"❌ Could not list tasks: {e}")

        print()

    def chapter6_update_definitions(self):
        """Chapter 6: Update existing definitions."""
        print("📖 CHAPTER 6: Updating Definitions")
        print("-" * 40)

        # Update a task definition
        print("Updating task definition...")
        try:
            task = self.metadata_client.get_task_def('process_payment_oss')
            print(f"Current settings for {task.name}:")
            print(f"  Timeout: {task.timeout_seconds}s")
            print(f"  Retry: {task.retry_count}")

            # Update the task
            task.description = 'Process payment with enhanced validation'
            task.timeout_seconds = 900  # Increase timeout
            task.retry_count = 7  # More retries

            self.metadata_client.update_task_def(task)
            print(f"\n✅ Updated {task.name}")
            print(f"  New timeout: {task.timeout_seconds}s")
            print(f"  New retry: {task.retry_count}")
        except Exception as e:
            print(f"❌ Could not update task: {e}")

        # Update a workflow definition
        print("\n\nUpdating workflow definition...")
        try:
            workflow = self.metadata_client.get_workflow_def('enrollment_basic_oss', version=1)
            print(f"Current task count: {len(workflow.tasks)}")

            # Update workflow
            workflow.description = 'Enhanced enrollment workflow with validation'
            workflow.timeout_seconds = 7200  # 2 hours
            workflow.restartable = True
            workflow.workflow_status_listener_enabled = True

            # Add a final confirmation task
            confirmation_task = WorkflowTask(
                name='send_notification_oss',
                task_reference_name=f'final_confirmation_{time.strftime("%Y%m%d-%H%M%S")}',
                input_parameters={
                    'message_type': 'enrollment_complete',
                    'content': 'Your enrollment is complete!'
                }
            )
            workflow.tasks.append(confirmation_task)

            self.metadata_client.update_workflow_def(workflow, overwrite=True)
            print(f"✅ Updated {workflow.name}")
            print(f"  New task count: {len(workflow.tasks)}")
            print(f"  Restartable: {workflow.restartable}")
        except Exception as e:
            print(f"❌ Could not update workflow: {e}")

        print()

    def chapter7_create_version2(self):
        """Chapter 7: Create version 2 of workflows."""
        print("📖 CHAPTER 7: Version Management")
        print("-" * 40)

        print("Creating version 2 of enrollment workflow...")
        try:
            # Get v1
            v1_workflow = self.metadata_client.get_workflow_def('enrollment_basic_oss')
            version = v1_workflow.version + 1

            # Create v2 with improvements
            v2_workflow = WorkflowDef(
                name='enrollment_basic_oss',
                version=version,
                description='Enrollment v2 with payment verification',
                input_parameters=v1_workflow.input_parameters + ['discount_code'],
                tasks=v1_workflow.tasks.copy()
            )

            # Add payment verification after payment task
            verification_task = WorkflowTask(
                name='validate_enrollment_oss',
                task_reference_name='verify_payment',
                input_parameters={
                    'student_id': '${workflow.input.student_id}',
                    'course_id': 'payment_verification'
                }
            )

            # Insert after payment (position 2)
            # if len(v2_workflow.tasks) >= 2:
            #     v2_workflow.tasks.insert(2, verification_task)

            self.metadata_client.register_workflow_def(v2_workflow, overwrite=True)
            self.created_workflows.append(('enrollment_basic_oss', 2))

            print("✅ Created version 2")
            print(f"  Version 1 tasks: {len(v1_workflow.tasks)}")
            print(f"  Version 2 tasks: {len(v2_workflow.tasks)}")
            print(f"  New input: discount_code")
        except Exception as e:
            print(f"❌ Could not create v2: {e}")

        print()

    def chapter8_metadata_summary(self):
        """Chapter 8: Display metadata summary."""
        print("📖 CHAPTER 8: Metadata Summary Dashboard")
        print("-" * 40)

        print("📊 METADATA SUMMARY")
        print("=" * 60)

        try:
            # Workflow statistics
            all_workflows = self.metadata_client.get_all_workflow_defs()
            our_workflows = [w for w in all_workflows
                           if any(w.name == name for name, _ in self.created_workflows)]

            print(f"\n📋 WORKFLOWS ({len(our_workflows)} total)")
            print("-" * 30)

            for workflow in our_workflows:
                print(f"\n{workflow.name} v{workflow.version}")
                print(f"  Description: {workflow.description[:60]}...")
                print(f"  Tasks: {len(workflow.tasks)}")

                # Count task types
                task_types = {}
                for task in workflow.tasks:
                    task_type = task.type if hasattr(task, 'type') and task.type else 'SIMPLE'
                    task_types[task_type] = task_types.get(task_type, 0) + 1

                if task_types:
                    types_str = ", ".join([f"{t}:{c}" for t, c in task_types.items()])
                    print(f"  Task Types: {types_str}")

            # Task statistics
            all_tasks = self.metadata_client.get_all_task_defs()
            our_tasks = [t for t in all_tasks if t.name in self.created_tasks]

            print(f"\n\n📋 TASKS ({len(our_tasks)} total)")
            print("-" * 30)

            # Group by characteristics
            retriable_tasks = [t for t in our_tasks if t.retry_count and t.retry_count > 0]
            rate_limited_tasks = [t for t in our_tasks if t.rate_limit_per_frequency]
            concurrent_limited = [t for t in our_tasks if t.concurrent_exec_limit]

            print(f"\n  Retriable tasks: {len(retriable_tasks)}")
            for task in retriable_tasks[:3]:
                print(f"    - {task.name}: {task.retry_count} retries")

            if rate_limited_tasks:
                print(f"\n  Rate-limited tasks: {len(rate_limited_tasks)}")
                for task in rate_limited_tasks:
                    print(f"    - {task.name}: {task.rate_limit_per_frequency}/{task.rate_limit_frequency_in_seconds}s")

            if concurrent_limited:
                print(f"\n  Concurrency-limited tasks: {len(concurrent_limited)}")
                for task in concurrent_limited:
                    print(f"    - {task.name}: max {task.concurrent_exec_limit} concurrent")

            # Overall statistics
            print(f"\n\n📈 STATISTICS")
            print("-" * 30)
            total_retry_capacity = sum(t.retry_count for t in our_tasks if t.retry_count)
            avg_timeout = sum(t.timeout_seconds for t in our_tasks) / len(our_tasks) if our_tasks else 0

            print(f"  Total Workflows: {len(our_workflows)}")
            print(f"  Total Tasks: {len(our_tasks)}")
            print(f"  Avg Task Timeout: {avg_timeout:.0f}s")
            print(f"  Total Retry Capacity: {total_retry_capacity}")
            print(f"  Rate Limited Tasks: {len(rate_limited_tasks)}")

        except Exception as e:
            print(f"❌ Could not generate summary: {e}")

        print()

    def chapter9_cleanup(self, cleanup=True):
        """Chapter 9: Clean up resources."""
        print("📖 CHAPTER 9: Cleanup")
        print("-" * 40)

        if not cleanup:
            print("ℹ️ Cleanup skipped (--no-cleanup flag)")
            print("Resources left for inspection:")
            print(f"  - {len(self.created_workflows)} workflows")
            print(f"  - {len(self.created_tasks)} tasks")
            return

        print("Cleaning up created resources...")

        # Delete workflows
        for workflow_name, version in self.created_workflows:
            try:
                self.metadata_client.unregister_workflow_def(workflow_name, version)
                print(f"  ✅ Deleted: {workflow_name} v{version}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    print(f"  ⚠️ Could not delete {workflow_name} v{version}: {e}")

        # Delete tasks
        for task_name in self.created_tasks:
            try:
                self.metadata_client.unregister_task_def(task_name)
                print(f"  ✅ Deleted: {task_name}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    print(f"  ⚠️ Could not delete {task_name}: {e}")

        print("\n✅ Cleanup completed")

    def run_journey(self, cleanup=True):
        """Run the complete metadata management journey."""
        try:
            self.chapter1_register_task_definitions()
            self.chapter2_create_simple_workflow()
            self.chapter3_create_decision_workflow()
            self.chapter4_create_parallel_workflow()
            self.chapter5_retrieve_definitions()
            self.chapter6_update_definitions()
            self.chapter7_create_version2()
            self.chapter8_metadata_summary()

            print("=" * 80)
            print("✅ CONDUCTOR OSS METADATA JOURNEY COMPLETED!")
            print("=" * 80)
            print()
            print("📊 Summary:")
            print(f"  - Created {len(self.created_tasks)} task definitions")
            print(f"  - Created {len(self.created_workflows)} workflow definitions")
            print(f"  - Demonstrated core metadata management APIs")
            print(f"  - Covered sequential, decision, and parallel workflows")
            print()

        except Exception as e:
            print(f"\n❌ Journey failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.chapter9_cleanup(cleanup)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Conductor OSS Metadata Management Journey'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup to keep metadata for inspection'
    )
    args = parser.parse_args()

    journey = MetadataJourneyOSS()
    journey.run_journey(cleanup=False)


if __name__ == '__main__':
    main()