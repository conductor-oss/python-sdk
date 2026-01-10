#!/usr/bin/env python3
"""
Metadata Management Journey - Comprehensive Example

This example demonstrates all 20 Metadata Management APIs through a narrative journey
of building a complete workflow system for an online education platform.

APIs Covered (100%):
Workflow Definition (5 APIs):
1. register_workflow_def() - Register new workflow
2. update_workflow_def() - Update workflow
3. get_workflow_def() - Get specific workflow
4. get_all_workflow_defs() - List all workflows
5. unregister_workflow_def() - Delete workflow

Task Definition (5 APIs):
6. register_task_def() - Register new task
7. update_task_def() - Update task
8. get_task_def() - Get specific task
9. get_all_task_defs() - List all tasks
10. unregister_task_def() - Delete task

Workflow Tags (4 APIs):
11. set_workflow_tags() - Set/overwrite workflow tags
12. add_workflow_tag() - Add single workflow tag
13. get_workflow_tags() - Get workflow tags
14. delete_workflow_tag() - Delete workflow tag

Task Tags (4 APIs):
15. setTaskTags() - Set/overwrite task tags
16. addTaskTag() - Add single task tag
17. getTaskTags() - Get task tags
18. deleteTaskTag() - Delete task tag

Rate Limiting (3 APIs):
19. setWorkflowRateLimit() - Set workflow rate limit
20. getWorkflowRateLimit() - Get workflow rate limit
21. removeWorkflowRateLimit() - Remove workflow rate limit

Run:
    python examples/metadata_journey.py
    python examples/metadata_journey.py --no-cleanup  # Keep metadata for inspection
"""

import os
import sys
import time
import argparse
from typing import List, Optional

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_metadata_client import OrkesMetadataClient
from conductor.client.http.models.workflow_def import WorkflowDef
from conductor.client.http.models.workflow_task import WorkflowTask
from conductor.client.http.models.task_def import TaskDef
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.fork_task import ForkTask
from conductor.client.workflow.task.join_task import JoinTask
from conductor.client.workflow.task.switch_task import SwitchTask


class MetadataJourney:
    """
    A comprehensive journey through all Metadata Management APIs.

    Story: Building a complete workflow system for an online education platform
    that handles course enrollment, content delivery, and student assessment.
    """

    def __init__(self):
        """Initialize the client and workflow executor."""
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
        self.metadata_client = OrkesMetadataClient(config)
        self.workflow_executor = WorkflowExecutor(config)

        # Track created resources for cleanup
        self.created_workflows = []
        self.created_tasks = []

        print("=" * 80)
        print("🚀 METADATA MANAGEMENT JOURNEY")
        print("=" * 80)
        print(f"Server: {server_url}")
        print()

    def chapter1_register_task_definitions(self):
        """Chapter 1: Register task definitions (API: register_task_def)."""
        print("📖 CHAPTER 1: Registering Task Definitions")
        print("-" * 40)

        # Define tasks for our education platform
        tasks = [
            TaskDef(
                name='validate_enrollment',
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
                name='process_payment',
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
                name='assign_instructor',
                description='Assign instructor to student',
                input_keys=['course_id', 'student_level'],
                output_keys=['instructor_id', 'instructor_name'],
                timeout_seconds=180,
                response_timeout_seconds=30,
                retry_count=2,
                concurrent_exec_limit=10
            ),
            TaskDef(
                name='send_welcome_email',
                description='Send welcome email to enrolled student',
                input_keys=['student_email', 'course_name', 'instructor_name'],
                output_keys=['email_sent', 'message_id'],
                timeout_seconds=120,
                retry_count=3,
                response_timeout_seconds=60
            ),
            TaskDef(
                name='setup_learning_path',
                description='Setup personalized learning path',
                input_keys=['student_id', 'course_id', 'assessment_results'],
                output_keys=['learning_path_id', 'modules'],
                timeout_seconds=400,
                response_timeout_seconds=30,
                retry_count=2
            ),
            TaskDef(
                name='grade_assignment',
                description='Grade student assignment',
                input_keys=['assignment_id', 'student_id', 'submission'],
                output_keys=['grade', 'feedback'],
                timeout_seconds=900,
                response_timeout_seconds=30,
                retry_count=1,
                poll_timeout_seconds=300
            )
        ]

        # Register all tasks
        for task_def in tasks:
            self.metadata_client.register_task_def(task_def)
            self.created_tasks.append(task_def.name)
            print(f"✅ Registered task: {task_def.name}")

        print(f"\nTotal tasks registered: {len(tasks)}")
        print()

    def chapter2_create_workflows(self):
        """Chapter 2: Create and register workflows (API: register_workflow_def)."""
        print("📖 CHAPTER 2: Creating and Registering Workflows")
        print("-" * 40)

        # 1. Simple enrollment workflow using ConductorWorkflow builder
        print("Creating course enrollment workflow...")
        enrollment_workflow = ConductorWorkflow(
            executor=self.workflow_executor,
            name='course_enrollment',
            version=1,
            description='Handle student course enrollment'
        )

        # Add tasks sequentially
        enrollment_workflow >> SimpleTask('validate_enrollment', 'validate_enrollment_ref')
        enrollment_workflow >> SimpleTask('process_payment', 'process_payment_ref')
        enrollment_workflow >> SimpleTask('assign_instructor', 'assign_instructor_ref')
        enrollment_workflow >> SimpleTask('send_welcome_email', 'send_welcome_email_ref')

        # Set input parameters
        enrollment_workflow.input_parameters(['student_id', 'course_id', 'payment_method'])

        # Register the workflow
        workflow_def = enrollment_workflow.to_workflow_def()
        self.metadata_client.register_workflow_def(workflow_def, overwrite=True)
        self.created_workflows.append(('course_enrollment', 1))
        print("✅ Registered course enrollment workflow")

        # 2. Complex assessment workflow with decision logic
        print("\nCreating student assessment workflow...")
        assessment_workflow = WorkflowDef(
            name='student_assessment',
            version=1,
            description='Assess student progress and assign grades',
            input_parameters=['student_id', 'course_id', 'assignment_ids'],
            timeout_seconds=3600,
            tasks=[
                WorkflowTask(
                    name='grade_assignment',
                    task_reference_name='grade_first_assignment',
                    input_parameters={
                        'assignment_id': '${workflow.input.assignment_ids[0]}',
                        'student_id': '${workflow.input.student_id}'
                    }
                ),
                WorkflowTask(
                    name='DECISION',
                    task_reference_name='check_grade',
                    type='DECISION',
                    case_value_param='grade_first_assignment.output.grade',
                    decision_cases={
                        'A': [WorkflowTask(
                            name='setup_learning_path',
                            task_reference_name='advanced_path',
                            input_parameters={'level': 'advanced'}
                        )],
                        'B': [WorkflowTask(
                            name='setup_learning_path',
                            task_reference_name='intermediate_path',
                            input_parameters={'level': 'intermediate'}
                        )],
                        'default': [WorkflowTask(
                            name='setup_learning_path',
                            task_reference_name='basic_path',
                            input_parameters={'level': 'basic'}
                        )]
                    }
                )
            ]
        )

        self.metadata_client.register_workflow_def(assessment_workflow, overwrite=True)
        self.created_workflows.append(('student_assessment', 1))
        print("✅ Registered student assessment workflow")

        # 3. Parallel processing workflow
        print("\nCreating course completion workflow...")
        completion_workflow = WorkflowDef(
            name='course_completion',
            version=1,
            description='Handle course completion and certification',
            tasks=[
                WorkflowTask(
                    name='FORK_JOIN',
                    task_reference_name='parallel_completion_tasks',
                    type='FORK_JOIN',
                    fork_tasks=[
                        [WorkflowTask(
                            name='grade_assignment',
                            task_reference_name='final_grade',
                            input_parameters={'type': 'final_exam'}
                        )],
                        [WorkflowTask(
                            name='send_welcome_email',
                            task_reference_name='send_certificate',
                            input_parameters={'type': 'certificate'}
                        )]
                    ]
                ),
                WorkflowTask(
                    name='JOIN',
                    task_reference_name='join_completion',
                    type='JOIN',
                    join_on=['final_grade', 'send_certificate']
                )
            ]
        )

        self.metadata_client.register_workflow_def(completion_workflow, overwrite=True)
        self.created_workflows.append(('course_completion', 1))
        print("✅ Registered course completion workflow")

        print(f"\nTotal workflows registered: {len(self.created_workflows)}")
        print()

    def chapter3_retrieve_definitions(self):
        """Chapter 3: Retrieve definitions (APIs: get_workflow_def, get_task_def, get_all_*)."""
        print("📖 CHAPTER 3: Retrieving Definitions")
        print("-" * 40)

        # Get specific workflow
        print("Retrieving course enrollment workflow...")
        workflow = self.metadata_client.get_workflow_def('course_enrollment', version=1)
        print(f"  📋 Name: {workflow.name}")
        print(f"  🔢 Version: {workflow.version}")
        print(f"  📝 Description: {workflow.description}")
        print(f"  ⚙️ Tasks: {len(workflow.tasks)}")
        print(f"  📥 Input Parameters: {workflow.input_parameters}")
        print()

        # Get latest version (no version specified)
        print("Getting latest version of student assessment...")
        latest = self.metadata_client.get_workflow_def('student_assessment')
        print(f"  Latest version: {latest.version}")
        print()

        # Get specific task
        print("Retrieving process_payment task definition...")
        task = self.metadata_client.get_task_def('process_payment')
        print(f"  📋 Name: {task.name}")
        print(f"  📝 Description: {task.description}")
        print(f"  ⏱️ Timeout: {task.timeout_seconds}s")
        print(f"  🔄 Retry: {task.retry_count} times ({task.retry_logic})")
        print(f"  📊 Rate Limit: {task.rate_limit_per_frequency}/{task.rate_limit_frequency_in_seconds}s")
        print()

        # Get all workflows
        print("Listing all workflows...")
        all_workflows = self.metadata_client.get_all_workflow_defs()
        print(f"Total workflows in system: {len(all_workflows)}")
        # Show our created workflows
        our_workflows = [w for w in all_workflows
                        if any(w.name == name for name, _ in self.created_workflows)]
        for wf in our_workflows:
            print(f"  - {wf.name} v{wf.version}: {wf.description}")
        print()

        # Get all tasks
        print("Listing all task definitions...")
        all_tasks = self.metadata_client.get_all_task_defs()
        print(f"Total tasks in system: {len(all_tasks)}")
        # Show our created tasks
        our_tasks = [t for t in all_tasks if t.name in self.created_tasks]
        for task in our_tasks[:3]:  # Show first 3
            print(f"  - {task.name}: {task.description}")
        if len(our_tasks) > 3:
            print(f"  ... and {len(our_tasks) - 3} more")
        print()

    def chapter4_workflow_tagging(self):
        """Chapter 4: Workflow tagging (APIs: set_workflow_tags, add_workflow_tag, get_workflow_tags, delete_workflow_tag)."""
        print("📖 CHAPTER 4: Workflow Tag Management")
        print("-" * 40)

        # Set multiple tags at once
        print("Setting tags on course enrollment workflow...")
        tags = [
            MetadataTag('department', 'education'),
            MetadataTag('priority', 'high'),
            MetadataTag('team', 'enrollment'),
            MetadataTag('sla', '99.9'),
            MetadataTag('region', 'global')
        ]
        self.metadata_client.set_workflow_tags(tags, 'course_enrollment')
        print(f"✅ Set {len(tags)} tags on course enrollment")

        # Add individual tag
        print("\nAdding cost center tag...")
        cost_tag = MetadataTag('cost-center', 'EDU-001')
        self.metadata_client.add_workflow_tag(cost_tag, 'course_enrollment')
        print("✅ Added cost center tag")

        # Get all tags
        print("\nRetrieving all tags...")
        retrieved_tags = self.metadata_client.get_workflow_tags('course_enrollment')
        print(f"Found {len(retrieved_tags)} tags:")
        for tag in retrieved_tags:
            print(f"  🏷️ {tag.key}: {tag.value}")

        # Delete specific tag
        print("\nDeleting region tag...")
        region_tag = MetadataTag('region', 'global')
        self.metadata_client.delete_workflow_tag(region_tag, 'course_enrollment')
        print("✅ Deleted region tag")

        # Verify deletion
        remaining_tags = self.metadata_client.get_workflow_tags('course_enrollment')
        print(f"Remaining tags: {len(remaining_tags)}")

        # Tag other workflows
        print("\nTagging assessment workflow...")
        assessment_tags = [
            MetadataTag('department', 'education'),
            MetadataTag('type', 'grading'),
            MetadataTag('automated', 'true')
        ]
        self.metadata_client.set_workflow_tags(assessment_tags, 'student_assessment')
        print("✅ Tagged assessment workflow")
        print()

    def chapter5_task_tagging(self):
        """Chapter 5: Task tagging (APIs: setTaskTags, addTaskTag, getTaskTags, deleteTaskTag)."""
        print("📖 CHAPTER 5: Task Tag Management")
        print("-" * 40)

        # Set multiple tags on task
        print("Setting tags on process_payment task...")
        payment_tags = [
            MetadataTag('type', 'financial'),
            MetadataTag('pci-compliant', 'true'),
            MetadataTag('critical', 'true'),
            MetadataTag('retry-enabled', 'true')
        ]
        self.metadata_client.setTaskTags(payment_tags, 'process_payment')
        print(f"✅ Set {len(payment_tags)} tags on process_payment")

        # Add individual tag
        print("\nAdding monitoring tag...")
        monitor_tag = MetadataTag('monitoring', 'enhanced')
        self.metadata_client.addTaskTag(monitor_tag, 'process_payment')
        print("✅ Added monitoring tag")

        # Get task tags
        print("\nRetrieving task tags...")
        task_tags = self.metadata_client.getTaskTags('process_payment')
        print(f"Found {len(task_tags)} tags:")
        for tag in task_tags:
            print(f"  🏷️ {tag.key}: {tag.value}")

        # Delete a tag
        print("\nDeleting retry-enabled tag...")
        retry_tag = MetadataTag('retry-enabled', 'true')
        self.metadata_client.deleteTaskTag(retry_tag, 'process_payment')
        print("✅ Deleted retry-enabled tag")

        # Tag other tasks
        print("\nTagging other critical tasks...")

        # Tag validation task
        validation_tags = [
            MetadataTag('type', 'validation'),
            MetadataTag('async', 'false')
        ]
        self.metadata_client.setTaskTags(validation_tags, 'validate_enrollment')
        print("✅ Tagged validate_enrollment")

        # Tag email task
        email_tags = [
            MetadataTag('type', 'notification'),
            MetadataTag('channel', 'email'),
            MetadataTag('template-enabled', 'true')
        ]
        self.metadata_client.setTaskTags(email_tags, 'send_welcome_email')
        print("✅ Tagged send_welcome_email")
        print()

    def chapter6_update_definitions(self):
        """Chapter 6: Update definitions (APIs: update_workflow_def, update_task_def)."""
        print("📖 CHAPTER 6: Updating Definitions")
        print("-" * 40)

        # Update task definition
        print("Updating process_payment task...")
        payment_task = self.metadata_client.get_task_def('process_payment')

        # Display current settings
        print(f"Current settings:")
        print(f"  Timeout: {payment_task.timeout_seconds}s")
        print(f"  Retry: {payment_task.retry_count}")
        print(f"  Rate Limit: {payment_task.rate_limit_per_frequency}")

        # Update the task
        payment_task.description = 'Process course payment with enhanced security'
        payment_task.timeout_seconds = 900  # Increase timeout
        payment_task.retry_count = 7  # More retries
        payment_task.rate_limit_per_frequency = 200  # Higher rate limit
        payment_task.input_keys.append('security_token')  # New input

        self.metadata_client.update_task_def(payment_task)
        print("\n✅ Updated process_payment task")
        print(f"New settings:")
        print(f"  Timeout: {payment_task.timeout_seconds}s")
        print(f"  Retry: {payment_task.retry_count}")
        print(f"  Rate Limit: {payment_task.rate_limit_per_frequency}")
        print(f"  New Input: security_token")

        # Update workflow definition
        print("\n\nUpdating course enrollment workflow...")
        enrollment_wf = self.metadata_client.get_workflow_def('course_enrollment', version=1)

        print(f"Current task count: {len(enrollment_wf.tasks)}")

        # Update workflow
        enrollment_wf.description = 'Enhanced student enrollment with prerequisites check'
        enrollment_wf.timeout_seconds = 7200  # 2 hours
        enrollment_wf.timeout_policy = 'ALERT_ONLY'  # Don't terminate, just alert

        # Add a new task at the beginning
        prerequisite_task = WorkflowTask(
            name='validate_enrollment',
            task_reference_name='check_prerequisites',
            input_parameters={
                'student_id': '${workflow.input.student_id}',
                'check_type': 'prerequisites'
            }
        )
        enrollment_wf.tasks.insert(0, prerequisite_task)

        self.metadata_client.update_workflow_def(enrollment_wf, overwrite=True)
        print("✅ Updated enrollment workflow")
        print(f"New task count: {len(enrollment_wf.tasks)}")
        print(f"Timeout: {enrollment_wf.timeout_seconds}s ({enrollment_wf.timeout_policy})")
        print()

    def chapter7_rate_limiting(self):
        """Chapter 7: Rate limiting (APIs: setWorkflowRateLimit, getWorkflowRateLimit, removeWorkflowRateLimit)."""
        print("📖 CHAPTER 7: Rate Limit Management")
        print("-" * 40)

        # Set rate limit on enrollment workflow
        print("Setting rate limit on course enrollment...")
        self.metadata_client.setWorkflowRateLimit(10, 'course_enrollment')
        print("✅ Set rate limit: Max 10 concurrent enrollments")

        # Get rate limit
        print("\nChecking rate limit...")
        rate_limit = self.metadata_client.getWorkflowRateLimit('course_enrollment')
        print(f"Current rate limit: {rate_limit} concurrent executions")

        # Set different rate limits for different workflows
        print("\nSetting rate limits for other workflows...")
        self.metadata_client.setWorkflowRateLimit(5, 'student_assessment')
        print("✅ Assessment workflow: Max 5 concurrent")

        self.metadata_client.setWorkflowRateLimit(20, 'course_completion')
        print("✅ Completion workflow: Max 20 concurrent")

        # Check all rate limits
        print("\n📊 Rate Limit Summary:")
        for workflow_name, _ in self.created_workflows:
            limit = self.metadata_client.getWorkflowRateLimit(workflow_name)
            if limit:
                print(f"  {workflow_name}: {limit} concurrent")
            else:
                print(f"  {workflow_name}: No limit")

        # Remove rate limit from completion workflow
        print("\nRemoving rate limit from course_completion...")
        self.metadata_client.removeWorkflowRateLimit('course_completion')
        print("✅ Rate limit removed")

        # Verify removal
        limit = self.metadata_client.getWorkflowRateLimit('course_completion')
        print(f"Course completion limit after removal: {limit if limit else 'No limit'}")
        print()

    def chapter8_complex_workflows(self):
        """Chapter 8: Create complex workflow patterns."""
        print("📖 CHAPTER 8: Complex Workflow Patterns")
        print("-" * 40)

        print("Creating adaptive learning workflow with switch logic...")

        # Create a complex workflow with SWITCH task
        adaptive_workflow = WorkflowDef(
            name='adaptive_learning',
            version=1,
            description='Adaptive learning path based on student performance',
            input_parameters=['student_id', 'course_id', 'assessment_score'],
            tasks=[
                WorkflowTask(
                    name='SWITCH',
                    task_reference_name='determine_path',
                    type='SWITCH',
                    evaluator_type='value-param',
                    expression='switchCase',
                    input_parameters={
                        'switchCase': '${workflow.input.assessment_score}'
                    },
                    decision_cases={
                        '90-100': [
                            WorkflowTask(
                                name='setup_learning_path',
                                task_reference_name='advanced_curriculum',
                                input_parameters={
                                    'difficulty': 'advanced',
                                    'pace': 'accelerated'
                                }
                            ),
                            WorkflowTask(
                                name='assign_instructor',
                                task_reference_name='senior_instructor',
                                input_parameters={'level': 'senior'}
                            )
                        ],
                        '70-89': [
                            WorkflowTask(
                                name='setup_learning_path',
                                task_reference_name='standard_curriculum',
                                input_parameters={
                                    'difficulty': 'intermediate',
                                    'pace': 'normal'
                                }
                            )
                        ],
                        '50-69': [
                            WorkflowTask(
                                name='setup_learning_path',
                                task_reference_name='remedial_curriculum',
                                input_parameters={
                                    'difficulty': 'basic',
                                    'pace': 'slow',
                                    'extra_support': True
                                }
                            ),
                            WorkflowTask(
                                name='send_welcome_email',
                                task_reference_name='notify_support',
                                input_parameters={
                                    'type': 'support_needed',
                                    'priority': 'high'
                                }
                            )
                        ]
                    },
                    default_case=[
                        WorkflowTask(
                            name='validate_enrollment',
                            task_reference_name='review_eligibility',
                            input_parameters={'review_type': 'manual'}
                        )
                    ]
                )
            ],
            failure_workflow='enrollment_failure_handler',
            restartable=True,
            workflow_status_listener_enabled=True
        )

        self.metadata_client.register_workflow_def(adaptive_workflow, overwrite=True)
        self.created_workflows.append(('adaptive_learning', 1))
        print("✅ Created adaptive learning workflow with SWITCH logic")

        # Tag it appropriately
        adaptive_tags = [
            MetadataTag('type', 'adaptive'),
            MetadataTag('ai-enabled', 'true'),
            MetadataTag('complexity', 'high')
        ]
        self.metadata_client.set_workflow_tags(adaptive_tags, 'adaptive_learning')
        print("✅ Tagged adaptive workflow")
        print()

    def chapter9_version_management(self):
        """Chapter 9: Version management and updates."""
        print("📖 CHAPTER 9: Version Management")
        print("-" * 40)

        print("Creating version 2 of course enrollment workflow...")

        # Get v1
        v1_workflow = self.metadata_client.get_workflow_def('course_enrollment', version=1)

        # Create v2 with improvements
        v2_workflow = WorkflowDef(
            name='course_enrollment',
            version=2,
            description='Course enrollment v2 with payment verification',
            input_parameters=v1_workflow.input_parameters + ['discount_code'],
            tasks=v1_workflow.tasks.copy()
        )

        # Add payment verification step after payment
        verification_task = WorkflowTask(
            name='validate_enrollment',
            task_reference_name='verify_payment',
            input_parameters={
                'transaction_id': '${process_payment_ref.output.transaction_id}',
                'verification_type': 'payment'
            }
        )

        # Insert after payment task (position 2)
        v2_workflow.tasks.insert(2, verification_task)
        v2_workflow.schema_version = 2
        v2_workflow.owner_email = 'platform-team@education.com'

        self.metadata_client.register_workflow_def(v2_workflow, overwrite=True)
        self.created_workflows.append(('course_enrollment', 2))
        print("✅ Created version 2 of course enrollment")

        # Compare versions
        print("\n📊 Version Comparison:")
        print(f"  Version 1:")
        print(f"    Tasks: {len(v1_workflow.tasks)}")
        print(f"    Inputs: {len(v1_workflow.input_parameters)}")
        print(f"  Version 2:")
        print(f"    Tasks: {len(v2_workflow.tasks)}")
        print(f"    Inputs: {len(v2_workflow.input_parameters)}")
        print(f"    New input: discount_code")
        print(f"    New task: payment verification")

        # Tag v2
        v2_tags = [
            MetadataTag('version', '2'),
            MetadataTag('stable', 'true'),
            MetadataTag('backward-compatible', 'true')
        ]
        self.metadata_client.set_workflow_tags(v2_tags, 'course_enrollment')
        print("\n✅ Tagged version 2")
        print()

    def chapter10_monitoring_dashboard(self):
        """Chapter 10: Create a monitoring dashboard view."""
        print("📖 CHAPTER 10: Metadata Monitoring Dashboard")
        print("-" * 40)

        print("📊 METADATA DASHBOARD")
        print("=" * 60)

        # Workflow Statistics
        all_workflows = self.metadata_client.get_all_workflow_defs()
        our_workflows = [w for w in all_workflows
                        if any(w.name == name for name, _ in self.created_workflows)]

        print(f"\n📋 WORKFLOWS ({len(our_workflows)} total)")
        print("-" * 30)

        for workflow in our_workflows:
            print(f"\n{workflow.name} v{workflow.version}")
            print(f"  Description: {workflow.description[:50]}...")
            print(f"  Tasks: {len(workflow.tasks)}")

            # Get tags
            try:
                tags = self.metadata_client.get_workflow_tags(workflow.name)
                if tags:
                    tag_str = ", ".join([f"{t.key}={t.value}" for t in tags[:3]])
                    print(f"  Tags: {tag_str}")
            except:
                pass

            # Get rate limit
            try:
                limit = self.metadata_client.getWorkflowRateLimit(workflow.name)
                if limit:
                    print(f"  Rate Limit: {limit} concurrent")
            except:
                pass

        # Task Statistics
        all_tasks = self.metadata_client.get_all_task_defs()
        our_tasks = [t for t in all_tasks if t.name in self.created_tasks]

        print(f"\n\n📋 TASKS ({len(our_tasks)} total)")
        print("-" * 30)

        # Group tasks by type
        financial_tasks = []
        validation_tasks = []
        notification_tasks = []
        other_tasks = []

        for task in our_tasks:
            try:
                tags = self.metadata_client.getTaskTags(task.name)
                task_type = None
                for tag in tags:
                    if tag.key == 'type':
                        task_type = tag.value
                        break

                if task_type == 'financial':
                    financial_tasks.append(task)
                elif task_type == 'validation':
                    validation_tasks.append(task)
                elif task_type == 'notification':
                    notification_tasks.append(task)
                else:
                    other_tasks.append(task)
            except:
                other_tasks.append(task)

        if financial_tasks:
            print(f"\n💰 Financial Tasks ({len(financial_tasks)}):")
            for task in financial_tasks:
                print(f"  - {task.name}: Retry={task.retry_count}, Timeout={task.timeout_seconds}s")

        if validation_tasks:
            print(f"\n✅ Validation Tasks ({len(validation_tasks)}):")
            for task in validation_tasks:
                print(f"  - {task.name}: Retry={task.retry_count}, Timeout={task.timeout_seconds}s")

        if notification_tasks:
            print(f"\n📧 Notification Tasks ({len(notification_tasks)}):")
            for task in notification_tasks:
                print(f"  - {task.name}: Retry={task.retry_count}, Timeout={task.timeout_seconds}s")

        if other_tasks:
            print(f"\n📦 Other Tasks ({len(other_tasks)}):")
            for task in other_tasks[:3]:  # Show first 3
                print(f"  - {task.name}")

        # Summary statistics
        print(f"\n\n📈 STATISTICS")
        print("-" * 30)
        total_retry_count = sum(t.retry_count for t in our_tasks)
        avg_timeout = sum(t.timeout_seconds for t in our_tasks) / len(our_tasks)
        rate_limited_tasks = [t for t in our_tasks if t.rate_limit_per_frequency]

        print(f"  Total Workflows: {len(our_workflows)}")
        print(f"  Total Tasks: {len(our_tasks)}")
        print(f"  Avg Task Timeout: {avg_timeout:.0f}s")
        print(f"  Total Retry Capacity: {total_retry_count}")
        print(f"  Rate Limited Tasks: {len(rate_limited_tasks)}")
        print()

    def chapter11_cleanup(self, cleanup=True):
        """Chapter 11: Clean up resources (APIs: unregister_workflow_def, unregister_task_def)."""
        print("📖 CHAPTER 11: Cleanup")
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
                print(f"  ✅ Deleted workflow: {workflow_name} v{version}")
            except Exception as e:
                print(f"  ⚠️ Could not delete {workflow_name} v{version}: {e}")

        # Delete tasks
        for task_name in self.created_tasks:
            try:
                self.metadata_client.unregister_task_def(task_name)
                print(f"  ✅ Deleted task: {task_name}")
            except Exception as e:
                print(f"  ⚠️ Could not delete {task_name}: {e}")

        print("\n✅ Cleanup completed")

    def run_journey(self, cleanup=True):
        """Run the complete metadata management journey."""
        try:
            self.chapter1_register_task_definitions()
            self.chapter2_create_workflows()
            self.chapter3_retrieve_definitions()
            self.chapter4_workflow_tagging()
            self.chapter5_task_tagging()
            self.chapter6_update_definitions()
            self.chapter7_rate_limiting()
            self.chapter8_complex_workflows()
            self.chapter9_version_management()
            self.chapter10_monitoring_dashboard()

            print("=" * 80)
            print("✅ METADATA MANAGEMENT JOURNEY COMPLETED!")
            print("=" * 80)
            print()
            print("📊 Summary:")
            print(f"  - Created {len(self.created_tasks)} task definitions")
            print(f"  - Created {len(self.created_workflows)} workflow definitions")
            print(f"  - Demonstrated all 20 metadata APIs")
            print(f"  - Covered CRUD, tagging, rate limiting, and versioning")
            print()

        except Exception as e:
            print(f"\n❌ Journey failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.chapter11_cleanup(cleanup)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Metadata Management Journey - Comprehensive Example'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup to keep metadata for inspection'
    )
    args = parser.parse_args()

    journey = MetadataJourney()
    journey.run_journey(cleanup=not args.no_cleanup)


if __name__ == '__main__':
    main()