#!/usr/bin/env python3
"""
Prompt Management Journey: Building an AI-Powered Customer Service System

This comprehensive example demonstrates all 8 Prompt Management APIs through a narrative
of building an AI-powered customer service system for an e-commerce platform.

Journey Overview:
1. Initial Setup - Creating basic prompt templates
2. Template Organization - Using tags to categorize prompts
3. Testing and Refinement - Testing prompts with different parameters
3.5. Version Management - Creating and managing multiple versions
4. Production Deployment - Managing production-ready prompts
5. Multi-language Support - Creating localized prompt versions
6. Performance Optimization - Testing different models and parameters
7. Compliance and Audit - Tag-based compliance tracking
8. Cleanup and Migration - Managing prompt lifecycle

API Coverage (8 APIs):
✅ save_prompt() - Create or update prompt templates (with version, models, auto_increment)
✅ get_prompt() - Retrieve specific prompt template
✅ get_prompts() - Get all prompt templates
✅ delete_prompt() - Delete prompt template
✅ get_tags_for_prompt_template() - Get tags for a prompt
✅ update_tag_for_prompt_template() - Set/update tags on a prompt
✅ delete_tag_for_prompt_template() - Remove tags from a prompt
✅ test_prompt() - Test prompt with variables and AI model

Requirements:
- Conductor server with AI integration configured
- Python SDK installed: pip install conductor-python
- Valid authentication credentials
"""

import os
import sys
import time
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.http.models.prompt_template import PromptTemplate
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate


class PromptJourney:
    """
    A comprehensive journey through all Prompt Management APIs.
    Building an AI-powered customer service system for TechMart.
    """

    def __init__(self):
        """Initialize the prompt client with configuration."""
        # Get configuration from environment or use defaults
        server_url = os.getenv('CONDUCTOR_SERVER_URL', 'http://localhost:8080/api')
        key_id = os.getenv('CONDUCTOR_AUTH_KEY', None)
        key_secret = os.getenv('CONDUCTOR_AUTH_SECRET', None)

        # Configure the client
        self.configuration = Configuration(
            server_api_url=server_url,
            debug=True
        )

        # Add authentication if credentials are provided
        if key_id and key_secret:
            self.configuration.authentication_settings = AuthenticationSettings(
                key_id=key_id,
                key_secret=key_secret
            )

        # Initialize the clients
        self.prompt_client = OrkesPromptClient(self.configuration)
        self.integration_client = OrkesIntegrationClient(self.configuration)

        # Track created resources for cleanup
        self.created_prompts = []
        self.created_integrations = []

        # AI integration name (configure based on your setup)
        self.ai_integration = os.getenv('AI_INTEGRATION', 'openai')

    def setup_integrations(self):
        """Set up AI integrations before using prompts."""
        print("\n" + "="*60)
        print(" INTEGRATION SETUP")
        print("="*60)
        print("\nSetting up AI integrations for prompt management...")

        integration_ready = False

        try:
            # Check if the integration already exists
            existing = self.integration_client.get_integration('openai')
            integration_exists = existing is not None

            if integration_exists:
                print(f"✅ Integration 'openai' already exists")
                print("  Will ensure all required models are configured...")
                integration_ready = True
            else:
                # Create OpenAI integration
                print("\n📝 Creating OpenAI integration...")

                # Get API key from environment or use a placeholder
                openai_key = os.getenv('OPENAI_API_KEY', 'sk-your-openai-key-here')

                try:
                    # Create IntegrationUpdate using model class properly
                    integration_details = IntegrationUpdate(
                        type='openai',
                        category='AI_MODEL',
                        description='OpenAI GPT models for prompt templates',
                        enabled=True,
                        configuration={
                            'api_key': openai_key,  # Use 'api_key' not 'apiKey' - must match ConfigKey enum
                            'endpoint': 'https://api.openai.com/v1'
                        }
                    )

                    self.integration_client.save_integration('openai', integration_details)
                    self.created_integrations.append('openai')
                    print("✅ Created OpenAI integration")

                    # Verify it was created
                    verify = self.integration_client.get_integration('openai')
                    if verify:
                        integration_ready = True
                    else:
                        print("⚠️ Integration creation may have failed, verification returned None")

                except Exception as create_error:
                    print(f"❌ Failed to create integration: {create_error}")
                    integration_ready = False

            # Only configure models if we have a working integration
            if not integration_ready:
                print("\n⚠️ Integration not ready. Skipping model configuration.")
                print("Please ensure the integration 'openai' exists before proceeding.")
                return

            # ALWAYS configure models when integration is ready
            print("\n📋 Configuring required AI models...")

            # Define all models we want to ensure are configured
            models = [
                {
                    'name': 'gpt-4o',
                    'description': 'GPT-4 Optimized - Latest and fastest model with 128K context',
                    'max_tokens': 128000
                },
                {
                    'name': 'gpt-4',
                    'description': 'GPT-4 - Most capable model for complex tasks',
                    'max_tokens': 8192
                },
                {
                    'name': 'gpt-3.5-turbo',
                    'description': 'GPT-3.5 Turbo - Fast and efficient for simple tasks',
                    'max_tokens': 16384
                },
                {
                    'name': 'gpt-4-turbo',
                    'description': 'GPT-4 Turbo - Faster GPT-4 with 128K context',
                    'max_tokens': 128000
                }
            ]

            # Add or update model configurations using proper model classes
            for model in models:
                try:
                    # Check if model already exists
                    existing_api = self.integration_client.get_integration_api(model['name'], 'openai')

                    # Create IntegrationApiUpdate object without invalid configuration keys
                    # The model name is passed as the API name parameter, not in configuration
                    api_details = IntegrationApiUpdate(
                        description=model['description'],
                        enabled=True,
                        max_tokens=model['max_tokens']
                        # Configuration should be None or contain only valid ConfigKey values
                        # Valid keys are: api_key, endpoint, environment, etc. NOT 'model'
                    )

                    self.integration_client.save_integration_api('openai', model['name'], api_details)

                    if existing_api:
                        print(f"  ✅ Updated model: {model['name']}")
                    else:
                        print(f"  ✅ Added model: {model['name']}")

                except Exception as e:
                    print(f"  ⚠️ Error with model {model['name']}: {str(e)}")

            # Verify the integration setup
            print("\n🔍 Verifying integration setup...")
            try:
                # Get the integration details
                integration = self.integration_client.get_integration('openai')
                if integration:
                    print(f"  ✓ Integration 'openai' is active")

                    # List all configured models
                    apis = self.integration_client.get_integration_apis('openai')
                    if apis:
                        print(f"  ✓ Configured models ({len(apis)} total):")
                        for api in apis:
                            status = "enabled" if api.enabled else "disabled"
                            print(f"    - {api.name}: {status}")
                    else:
                        print("  ⚠️ No models configured yet")

            except Exception as e:
                print(f"  ⚠️ Could not verify integration: {str(e)}")

            # Tag the integration and models for better organization
            self.tag_integrations()

            print("\n✅ Integration setup complete!")

        except Exception as e:
            print(f"\n⚠️ Integration setup error: {e}")
            print("Attempting to continue with existing integrations...")

            # Try to list what integrations are available
            try:
                integrations = self.integration_client.get_integrations()
                if integrations:
                    print("\nAvailable integrations:")
                    for integration in integrations:
                        print(f"  - {integration.name}: {integration.type}")
                else:
                    print("\n⚠️ No integrations found. Prompts may not work with AI models.")
            except Exception as list_error:
                print(f"Could not list integrations: {list_error}")

    def tag_integrations(self):
        """Tag integrations and models for better organization and tracking."""
        print("\n🏷️ Tagging integrations for organization...")

        try:
            # Tag the main integration provider
            integration_tags = [
                MetadataTag("provider", "openai"),
                MetadataTag("category", "ai_model"),
                MetadataTag("environment", "production"),
                MetadataTag("team", "ai_platform"),
                MetadataTag("cost_center", "engineering"),
                MetadataTag("created_date", datetime.now().strftime("%Y-%m-%d")),
                MetadataTag("purpose", "prompt_management"),
                MetadataTag("status", "active")
            ]

            try:
                self.integration_client.put_tag_for_integration_provider(integration_tags, 'openai')
                print("  ✅ Tagged integration provider 'openai'")

                # Verify tags were applied
                provider_tags = self.integration_client.get_tags_for_integration_provider('openai')
                if provider_tags:
                    print(f"     Applied {len(provider_tags)} tags to integration")
            except Exception as e:
                print(f"  ⚠️ Could not tag integration provider: {str(e)[:50]}")

            # Tag individual models with their characteristics
            model_tags = {
                'gpt-4o': [
                    MetadataTag("model_type", "optimized"),
                    MetadataTag("context_window", "128k"),
                    MetadataTag("performance", "fastest"),
                    MetadataTag("cost_tier", "premium"),
                    MetadataTag("use_case", "high_volume"),
                    MetadataTag("capabilities", "advanced"),
                    MetadataTag("release_date", "2024")
                ],
                'gpt-4': [
                    MetadataTag("model_type", "standard"),
                    MetadataTag("context_window", "8k"),
                    MetadataTag("performance", "balanced"),
                    MetadataTag("cost_tier", "premium"),
                    MetadataTag("use_case", "complex_reasoning"),
                    MetadataTag("capabilities", "maximum"),
                    MetadataTag("release_date", "2023")
                ],
                'gpt-3.5-turbo': [
                    MetadataTag("model_type", "turbo"),
                    MetadataTag("context_window", "16k"),
                    MetadataTag("performance", "fast"),
                    MetadataTag("cost_tier", "economy"),
                    MetadataTag("use_case", "simple_tasks"),
                    MetadataTag("capabilities", "standard"),
                    MetadataTag("release_date", "2022")
                ],
                'gpt-4-turbo': [
                    MetadataTag("model_type", "turbo"),
                    MetadataTag("context_window", "128k"),
                    MetadataTag("performance", "fast"),
                    MetadataTag("cost_tier", "mid_tier"),
                    MetadataTag("use_case", "balanced"),
                    MetadataTag("capabilities", "advanced"),
                    MetadataTag("release_date", "2024")
                ]
            }

            print("\n  📎 Tagging individual models...")
            for model_name, tags in model_tags.items():
                try:
                    # Check if model exists before tagging
                    model_api = self.integration_client.get_integration_api(model_name, 'openai')
                    if model_api:
                        self.integration_client.put_tag_for_integration(tags, model_name, 'openai')
                        print(f"    ✅ Tagged model: {model_name} ({len(tags)} tags)")

                        # Verify tags
                        applied_tags = self.integration_client.get_tags_for_integration(model_name, 'openai')
                        if applied_tags:
                            # Show a sample of tags
                            sample_tags = applied_tags[:3] if len(applied_tags) > 3 else applied_tags
                            tag_str = ', '.join([f"{t.key}={t.value}" for t in sample_tags])
                            if len(applied_tags) > 3:
                                tag_str += f" ... +{len(applied_tags)-3} more"
                            print(f"       Tags: {tag_str}")
                except Exception as e:
                    # Model might not be configured yet
                    print(f"    ⚠️ Could not tag {model_name}: {str(e)[:50]}")

            print("\n  📊 Tag Summary:")
            print(f"    • Integration provider tagged with {len(integration_tags)} tags")
            print(f"    • {len(model_tags)} models tagged for tracking")
            print("    • Tags enable filtering, reporting, and cost allocation")

        except Exception as e:
            print(f"\n⚠️ Tagging error: {e}")
            print("Integration will work but won't have organizational tags")

    def associate_prompts_with_models(self):
        """Associate prompts with specific AI models using the integration client."""
        print("\n" + "="*60)
        print(" MODEL ASSOCIATIONS")
        print("="*60)
        print("\nAssociating prompts with optimal AI models...")

        try:
            # Define prompt-to-model associations based on use case
            associations = [
                {
                    'prompt': 'customer_greeting',
                    'model': 'gpt-3.5-turbo',
                    'reason': 'Simple greetings work well with faster, lighter models'
                },
                {
                    'prompt': 'order_inquiry',
                    'model': 'gpt-4o',
                    'reason': 'Order lookups need accuracy and speed'
                },
                {
                    'prompt': 'complaint_handling',
                    'model': 'gpt-4',
                    'reason': 'Complex complaints need the most capable model'
                },
                {
                    'prompt': 'faq_response',
                    'model': 'gpt-3.5-turbo',
                    'reason': 'FAQs are straightforward and benefit from speed'
                },
                {
                    'prompt': 'product_recommendation',
                    'model': 'gpt-4o',
                    'reason': 'Recommendations need both intelligence and speed'
                },
                {
                    'prompt': 'refund_process',
                    'model': 'gpt-4',
                    'reason': 'Financial operations require maximum accuracy'
                }
            ]

            print("\n📎 Creating prompt-model associations...")
            successful_associations = 0

            for assoc in associations:
                try:
                    # Associate the prompt with the model
                    self.integration_client.associate_prompt_with_integration(
                        ai_integration='openai',
                        model_name=assoc['model'],
                        prompt_name=assoc['prompt']
                    )
                    successful_associations += 1
                    print(f"  ✅ {assoc['prompt']} → openai:{assoc['model']}")
                    print(f"     Reason: {assoc['reason']}")
                except Exception as e:
                    # Some prompts might not exist yet, which is okay
                    print(f"  ⚠️ Could not associate {assoc['prompt']}: {str(e)[:50]}")

            print(f"\n✅ Successfully created {successful_associations} associations")

            # List prompts associated with each model
            print("\n📊 Verifying model associations...")
            models_to_check = ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']

            for model in models_to_check:
                try:
                    prompts = self.integration_client.get_prompts_with_integration('openai', model)
                    if prompts:
                        print(f"\n  Model: openai:{model}")
                        print(f"  Associated prompts ({len(prompts)}):")
                        for prompt in prompts[:5]:  # Show first 5
                            print(f"    - {prompt.name}")
                        if len(prompts) > 5:
                            print(f"    ... and {len(prompts) - 5} more")
                except Exception as e:
                    print(f"  ⚠️ Could not list prompts for {model}: {str(e)[:50]}")

        except Exception as e:
            print(f"\n⚠️ Association setup error: {e}")
            print("Prompts will still work but may not be optimized for specific models")

    def track_token_usage(self):
        """Track and display token usage across integrations and models."""
        print("\n" + "="*60)
        print(" TOKEN USAGE TRACKING")
        print("="*60)
        print("\nMonitoring token usage for cost optimization...")

        try:
            # Get token usage for the integration provider
            print("\n📊 Token Usage by Integration:")
            try:
                usage = self.integration_client.get_token_usage_for_integration_provider('openai')
                if usage:
                    print(f"  OpenAI Integration:")
                    for key, value in usage.items():
                        print(f"    {key}: {value}")
                else:
                    print("  No token usage data available yet")
            except Exception as e:
                print(f"  ⚠️ Could not retrieve provider usage: {str(e)[:50]}")

            # Get token usage for specific models
            print("\n📊 Token Usage by Model:")
            models = ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']

            for model in models:
                try:
                    usage = self.integration_client.get_token_usage_for_integration(model, 'openai')
                    if usage:
                        print(f"  {model}: {usage:,} tokens")
                    else:
                        print(f"  {model}: No usage data")
                except Exception as e:
                    print(f"  {model}: Data not available")

            # Calculate estimated costs (example rates)
            print("\n💰 Estimated Costs (example rates):")
            cost_per_1k_tokens = {
                'gpt-4o': {'input': 0.01, 'output': 0.03},
                'gpt-4': {'input': 0.03, 'output': 0.06},
                'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002}
            }

            print("  Model costs per 1K tokens:")
            for model, rates in cost_per_1k_tokens.items():
                print(f"    {model}:")
                print(f"      Input: ${rates['input']:.3f}")
                print(f"      Output: ${rates['output']:.3f}")

        except Exception as e:
            print(f"\n⚠️ Token tracking error: {e}")
            print("Token usage tracking may not be available")

    def display_prompt(self, prompt: PromptTemplate, title: str = "Prompt Template"):
        """Helper method to display prompt details."""
        print(f"\n{title}:")
        print(f"  Name: {prompt.name}")
        print(f"  Description: {prompt.description}")
        print(f"  Variables: {prompt.variables}")
        if prompt.tags:
            print("  Tags:")
            for tag in prompt.tags:
                print(f"    - {tag.key}: {tag.value}")
        print(f"  Created by: {prompt.created_by}")
        print(f"  Updated on: {datetime.fromtimestamp(prompt.updated_on/1000) if prompt.updated_on else 'N/A'}")

    def display_tags(self, tags: List[MetadataTag], title: str = "Tags"):
        """Helper method to display tags."""
        if tags:
            print(f"\n{title} ({len(tags)} tags):")
            for tag in tags:
                print(f"  🏷️ {tag.key}: {tag.value}")
        else:
            print(f"\n{title}: No tags found")

    def run(self):
        """Execute the complete prompt management journey."""
        print("\n" + "="*80)
        print(" PROMPT MANAGEMENT JOURNEY: AI-POWERED CUSTOMER SERVICE")
        print("="*80)
        print("\nWelcome to TechMart's journey to build an AI-powered customer service system!")
        print("We'll explore all 8 Prompt Management APIs through real-world scenarios.")

        try:
            # Set up integrations first
            self.setup_integrations()

            # Then proceed with prompt management
            self.chapter1_initial_setup()
            self.chapter2_template_organization()
            self.chapter3_testing_refinement()
            self.chapter3_5_version_management()
            self.chapter4_production_deployment()

            # Associate prompts with optimal models
            self.associate_prompts_with_models()

            self.chapter5_multilanguage_support()
            self.chapter6_performance_optimization()

            # Track token usage for cost monitoring
            self.track_token_usage()

            self.chapter7_compliance_audit()
            self.chapter8_cleanup_migration()

            print("\n" + "="*80)
            print(" JOURNEY COMPLETED SUCCESSFULLY!")
            print("="*80)
            print("\nCongratulations! You've successfully explored all Prompt Management APIs.")
            print("Your AI-powered customer service system is ready for production!")

        except Exception as e:
            print(f"\n❌ Journey failed: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

    def chapter1_initial_setup(self):
        """Chapter 1: Initial Setup - Creating Basic Prompt Templates"""
        print("\n" + "="*60)
        print(" CHAPTER 1: INITIAL SETUP")
        print("="*60)
        print("\nTechMart is launching AI-powered customer service.")
        print("Let's create our first prompt templates...")

        # API 1: save_prompt() - Create greeting prompt
        print("\n📝 Creating customer greeting prompt...")
        greeting_prompt = """You are a friendly customer service representative for TechMart.

Customer Name: ${customer_name}
Customer Tier: ${customer_tier}
Time of Day: ${time_of_day}

Greet the customer appropriately based on their tier and the time of day.
Keep the greeting warm, professional, and under 50 words."""

        self.prompt_client.save_prompt(
            prompt_name="customer_greeting",
            description="Personalized greeting for customers based on tier and time",
            prompt_template=greeting_prompt
        )
        self.created_prompts.append("customer_greeting")
        print("✅ Created 'customer_greeting' prompt")

        # API 2: get_prompt() - Retrieve the created prompt
        print("\n🔍 Retrieving the greeting prompt to verify...")
        retrieved_prompt = self.prompt_client.get_prompt("customer_greeting")
        if retrieved_prompt:
            self.display_prompt(retrieved_prompt, "Retrieved Greeting Prompt")

        # Create order inquiry prompt
        print("\n📝 Creating order inquiry prompt...")
        order_prompt = """You are a helpful customer service agent for TechMart.

Customer Information:
- Name: ${customer_name}
- Order ID: ${order_id}
- Order Status: ${order_status}
- Delivery Date: ${delivery_date}

Customer Query: ${query}

Provide a clear, empathetic response about their order.
Include relevant details and next steps if applicable."""

        self.prompt_client.save_prompt(
            prompt_name="order_inquiry",
            description="Handle customer inquiries about order status",
            prompt_template=order_prompt
        )
        self.created_prompts.append("order_inquiry")
        print("✅ Created 'order_inquiry' prompt")

        # Create return request prompt
        print("\n📝 Creating return request prompt...")
        return_prompt = """You are processing a return request for TechMart.

Product: ${product_name}
Purchase Date: ${purchase_date}
Reason: ${return_reason}
Condition: ${product_condition}

Return Policy: Items can be returned within 30 days in original condition.

Evaluate the return request and provide:
1. Whether the return is eligible
2. Next steps for the customer
3. Expected timeline

Be helpful and understanding while following company policy."""

        self.prompt_client.save_prompt(
            prompt_name="return_request",
            description="Process and respond to product return requests",
            prompt_template=return_prompt
        )
        self.created_prompts.append("return_request")
        print("✅ Created 'return_request' prompt")

        print("\n✨ Chapter 1 Complete: Basic prompts created!")

    def chapter2_template_organization(self):
        """Chapter 2: Template Organization - Using Tags to Categorize Prompts"""
        print("\n" + "="*60)
        print(" CHAPTER 2: TEMPLATE ORGANIZATION")
        print("="*60)
        print("\nOrganizing prompts with tags for better management...")

        # API 5: update_tag_for_prompt_template() - Add tags to greeting prompt
        print("\n🏷️ Adding tags to customer greeting prompt...")
        greeting_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "greeting"),
            MetadataTag("department", "support"),
            MetadataTag("language", "english"),
            MetadataTag("status", "active"),
            MetadataTag("priority", "high")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "customer_greeting",
            greeting_tags
        )
        print("✅ Tags added to greeting prompt")

        # API 6: get_tags_for_prompt_template() - Verify tags
        print("\n🔍 Retrieving tags for greeting prompt...")
        retrieved_tags = self.prompt_client.get_tags_for_prompt_template("customer_greeting")
        self.display_tags(retrieved_tags, "Greeting Prompt Tags")

        # Add tags to order inquiry prompt
        print("\n🏷️ Adding tags to order inquiry prompt...")
        order_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "inquiry"),
            MetadataTag("department", "support"),
            MetadataTag("language", "english"),
            MetadataTag("status", "active"),
            MetadataTag("priority", "high"),
            MetadataTag("integration", "order_system")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "order_inquiry",
            order_tags
        )
        print("✅ Tags added to order inquiry prompt")

        # Add tags to return request prompt
        print("\n🏷️ Adding tags to return request prompt...")
        return_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "returns"),
            MetadataTag("department", "support"),
            MetadataTag("language", "english"),
            MetadataTag("status", "testing"),
            MetadataTag("priority", "medium"),
            MetadataTag("compliance", "requires_review")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "return_request",
            return_tags
        )
        print("✅ Tags added to return request prompt")

        # API 3: get_prompts() - Get all prompts and display by category
        print("\n📚 Retrieving all prompts organized by tags...")
        all_prompts = self.prompt_client.get_prompts()

        # Organize by category
        categorized = {}
        for prompt in all_prompts:
            if prompt.name in self.created_prompts:
                if prompt.tags:
                    for tag in prompt.tags:
                        if tag.key == "type":
                            category = tag.value
                            if category not in categorized:
                                categorized[category] = []
                            categorized[category].append(prompt)
                            break

        print("\n📊 Prompts by Type:")
        for category, prompts in categorized.items():
            print(f"\n  {category.upper()} ({len(prompts)} prompts):")
            for prompt in prompts:
                status = "N/A"
                for tag in prompt.tags:
                    if tag.key == "status":
                        status = tag.value
                        break
                print(f"    - {prompt.name}: {prompt.description} [Status: {status}]")

        print("\n✨ Chapter 2 Complete: Prompts organized with tags!")

    def chapter3_testing_refinement(self):
        """Chapter 3: Testing and Refinement - Testing Prompts with Different Parameters"""
        print("\n" + "="*60)
        print(" CHAPTER 3: TESTING AND REFINEMENT")
        print("="*60)
        print("\nTesting prompts with real data and different parameters...")

        # API 8: test_prompt() - Test greeting prompt
        print("\n🧪 Testing customer greeting prompt...")

        test_cases = [
            {
                "customer_name": "John Smith",
                "customer_tier": "Premium",
                "time_of_day": "morning"
            },
            {
                "customer_name": "Sarah Johnson",
                "customer_tier": "Standard",
                "time_of_day": "evening"
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n  Test Case {i}:")
            print(f"    Customer: {test_case['customer_name']} ({test_case['customer_tier']})")
            print(f"    Time: {test_case['time_of_day']}")

            try:
                response = self.prompt_client.test_prompt(
                    prompt_text=self.prompt_client.get_prompt("customer_greeting").template,
                    variables=test_case,
                    ai_integration="openai",
                    text_complete_model="gpt-4o",
                    temperature=0.7,
                    top_p=0.9
                )
                print(f"    Response: {response[:200]}...")
            except Exception as e:
                print(f"    Test skipped (AI integration required): {str(e)}")

        # Test order inquiry prompt with different temperatures
        print("\n🧪 Testing order inquiry with different creativity levels...")

        order_test = {
            "customer_name": "Alex Chen",
            "order_id": "ORD-2024-001234",
            "order_status": "In Transit",
            "delivery_date": "December 28, 2024",
            "query": "When will my order arrive? I need it for a gift."
        }

        temperature_tests = [
            {"name": "Conservative", "temp": 0.3},
            {"name": "Balanced", "temp": 0.7},
            {"name": "Creative", "temp": 0.9}
        ]

        for test in temperature_tests:
            print(f"\n  Testing with {test['name']} temperature ({test['temp']}):")
            try:
                response = self.prompt_client.test_prompt(
                    prompt_text=self.prompt_client.get_prompt("order_inquiry").template,
                    variables=order_test,
                    ai_integration="openai",
                    text_complete_model="gpt-4o",
                    temperature=test['temp'],
                    top_p=0.9
                )
                print(f"    Response preview: {response[:150]}...")
            except Exception as e:
                print(f"    Test skipped (AI integration required): {str(e)}")

        # Update prompt based on "testing feedback"
        print("\n📝 Refining order inquiry prompt based on testing...")
        refined_prompt = """You are a helpful and empathetic customer service agent for TechMart.

Customer Information:
- Name: ${customer_name}
- Order ID: ${order_id}
- Order Status: ${order_status}
- Expected Delivery: ${delivery_date}

Customer Query: ${query}

Instructions:
1. Acknowledge their concern immediately
2. Provide current order status clearly
3. Explain what the status means
4. Give specific timeline if available
5. Offer assistance or alternatives if needed
6. Keep response under 100 words

Tone: Professional, empathetic, and solution-focused"""

        self.prompt_client.save_prompt(
            prompt_name="order_inquiry",
            description="Handle customer inquiries about order status (v2 - refined)",
            prompt_template=refined_prompt
        )
        print("✅ Order inquiry prompt refined and updated")

        print("\n✨ Chapter 3 Complete: Prompts tested and refined!")

    def chapter3_5_version_management(self):
        """Chapter 3.5: Version Management - Creating and Managing Multiple Versions"""
        print("\n" + "="*60)
        print(" CHAPTER 3.5: VERSION MANAGEMENT")
        print("="*60)
        print("\nLearning to manage multiple versions of prompts...")

        # Create a new prompt with explicit version 1
        print("\n📝 Creating FAQ response prompt - Version 1...")
        faq_v1 = """Answer the customer's frequently asked question.

Question: ${question}

Provide a clear, concise answer."""

        self.prompt_client.save_prompt(
            prompt_name="faq_response",
            description="FAQ response generator - Initial version",
            prompt_template=faq_v1,
            version=1  # Explicitly set version 1
        )
        self.created_prompts.append("faq_response")
        print("✅ Created FAQ response v1")

        # Create version 2 with improvements
        print("\n📝 Creating improved Version 2...")
        faq_v2 = """You are a knowledgeable TechMart support agent answering FAQs.

Category: ${category}
Question: ${question}
Customer Type: ${customer_type}

Instructions:
- Provide accurate information
- Keep answer under 150 words
- Include relevant links if applicable
- Be friendly and helpful"""

        self.prompt_client.save_prompt(
            prompt_name="faq_response",
            description="FAQ response generator - Enhanced with category support",
            prompt_template=faq_v2,
            version=2  # Version 2
        )
        print("✅ Created FAQ response v2 with category support")

        # Create version 3 with multi-language hints
        print("\n📝 Creating Version 3 with multi-language support...")
        faq_v3 = """You are a knowledgeable TechMart support agent answering FAQs.

Category: ${category}
Question: ${question}
Customer Type: ${customer_type}
Language Preference: ${language}

Instructions:
- Provide accurate information in a culturally appropriate manner
- Keep answer under 150 words
- Include relevant links if applicable
- Be friendly and helpful
- If language is not English, add a note that full support is available in that language"""

        self.prompt_client.save_prompt(
            prompt_name="faq_response",
            description="FAQ response generator - Multi-language aware",
            prompt_template=faq_v3,
            version=3  # Version 3
        )
        print("✅ Created FAQ response v3 with language support")

        # Demonstrate auto-increment feature
        print("\n📝 Using auto-increment for minor update...")
        faq_v3_1 = """You are a knowledgeable TechMart support agent answering FAQs.

Category: ${category}
Question: ${question}
Customer Type: ${customer_type}
Language Preference: ${language}
Urgency Level: ${urgency}

Instructions:
- Provide accurate information in a culturally appropriate manner
- Prioritize based on urgency level
- Keep answer under 150 words
- Include relevant links if applicable
- Be friendly and helpful
- If language is not English, add a note that full support is available in that language"""

        self.prompt_client.save_prompt(
            prompt_name="faq_response",
            description="FAQ response generator - Added urgency handling",
            prompt_template=faq_v3_1,
            auto_increment=True  # Auto-increment from current version
        )
        print("✅ Auto-incremented version with urgency handling")

        # Create a versioned prompt for A/B testing
        print("\n📝 Creating specific versions for A/B testing...")

        # Version for formal tone
        formal_greeting = """Dear ${customer_name},

Thank you for contacting TechMart support.

We appreciate your ${customer_tier} membership and are here to assist you.

How may we help you today?"""

        self.prompt_client.save_prompt(
            prompt_name="greeting_formal",
            description="Formal greeting style for A/B testing",
            prompt_template=formal_greeting,
            version=1,
            models=["openai:gpt-4", "openai:gpt-4o"]  # Specify which models work best with this integration
        )
        self.created_prompts.append("greeting_formal")
        print("✅ Created formal greeting v1")

        # Version for casual tone
        casual_greeting = """Hey ${customer_name}! 👋

Thanks for reaching out to TechMart!

As a ${customer_tier} member, you get priority support.

What can I help you with today?"""

        self.prompt_client.save_prompt(
            prompt_name="greeting_casual",
            description="Casual greeting style for A/B testing",
            prompt_template=casual_greeting,
            version=1,
            models=["openai:gpt-3.5-turbo", "openai:gpt-4o"]  # Different model preferences for this integration
        )
        self.created_prompts.append("greeting_casual")
        print("✅ Created casual greeting v1")

        # Tag versions for tracking
        print("\n🏷️ Tagging versions for management...")

        version_tags = [
            MetadataTag("version_status", "active"),
            MetadataTag("tested_models", "openai:gpt-4o"),
            MetadataTag("performance", "optimized"),
            MetadataTag("last_updated", "2024-12-24")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "faq_response",
            version_tags
        )
        print("✅ Tagged FAQ response with version metadata")

        # Show version management best practices
        print("\n📚 Version Management Best Practices:")
        print("  1. Use explicit version numbers for major changes")
        print("  2. Use auto-increment for minor updates")
        print("  3. Tag versions with testing status and performance metrics")
        print("  4. Specify compatible models for each version")
        print("  5. Keep version history for rollback capabilities")

        print("\n✨ Chapter 3.5 Complete: Version management mastered!")

    def chapter4_production_deployment(self):
        """Chapter 4: Production Deployment - Managing Production-Ready Prompts"""
        print("\n" + "="*60)
        print(" CHAPTER 4: PRODUCTION DEPLOYMENT")
        print("="*60)
        print("\nPreparing prompts for production deployment...")

        # Create production versions of prompts
        print("\n📝 Creating production-ready prompt versions...")

        # Create complaint handling prompt
        complaint_prompt = """You are a senior customer service specialist for TechMart handling complaints.

Customer: ${customer_name}
Account Type: ${account_type}
Previous Interactions: ${interaction_count}
Complaint Category: ${complaint_category}
Complaint Details: ${complaint_details}

Guidelines:
1. Express genuine empathy and apologize for the inconvenience
2. Acknowledge the specific issue
3. Provide a clear resolution or escalation path
4. Set realistic expectations for resolution timeline
5. Offer compensation if appropriate (${compensation_authorized})
6. Document next steps clearly

Maintain a professional, empathetic tone throughout.
Response should be 100-150 words."""

        self.prompt_client.save_prompt(
            prompt_name="complaint_handler_v1",
            description="Production-ready complaint handling prompt",
            prompt_template=complaint_prompt
        )
        self.created_prompts.append("complaint_handler_v1")

        # Tag as production-ready
        production_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "complaint"),
            MetadataTag("department", "support"),
            MetadataTag("status", "production"),
            MetadataTag("version", "1.0"),
            MetadataTag("sla", "5min_response"),
            MetadataTag("model_tested", "openai:gpt-4o"),
            MetadataTag("model_tested", "openai:gpt-4"),
            MetadataTag("approved_by", "support_manager"),
            MetadataTag("deployment_date", "2024-12-24")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "complaint_handler_v1",
            production_tags
        )
        print("✅ Created and tagged production complaint handler")

        # Update greeting prompt to production status
        print("\n🔄 Promoting greeting prompt to production...")
        greeting_tags = self.prompt_client.get_tags_for_prompt_template("customer_greeting")

        # Update status tag
        updated_tags = []
        for tag in greeting_tags:
            if tag.key == "status":
                updated_tags.append(MetadataTag("status", "production"))
            else:
                updated_tags.append(tag)

        # Add production metadata
        updated_tags.extend([
            MetadataTag("version", "1.0"),
            MetadataTag("deployment_date", "2024-12-24"),
            MetadataTag("approved_by", "support_manager")
        ])

        self.prompt_client.update_tag_for_prompt_template(
            "customer_greeting",
            updated_tags
        )
        print("✅ Greeting prompt promoted to production")

        # Create A/B test variant
        print("\n🔬 Creating A/B test variant for greeting...")
        greeting_variant = """Welcome to TechMart, ${customer_name}!

As a ${customer_tier} member, you receive priority support.

How may I assist you this ${time_of_day}?"""

        self.prompt_client.save_prompt(
            prompt_name="customer_greeting_v2_test",
            description="A/B test variant - shorter greeting format",
            prompt_template=greeting_variant
        )
        self.created_prompts.append("customer_greeting_v2_test")

        variant_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "greeting"),
            MetadataTag("status", "ab_testing"),
            MetadataTag("variant_of", "customer_greeting"),
            MetadataTag("test_percentage", "20"),
            MetadataTag("metrics_tracking", "response_time,satisfaction")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "customer_greeting_v2_test",
            variant_tags
        )
        print("✅ A/B test variant created")

        # Display production prompts
        print("\n📊 Production Prompt Summary:")
        all_prompts = self.prompt_client.get_prompts()

        production_prompts = []
        testing_prompts = []

        for prompt in all_prompts:
            if prompt.name in self.created_prompts and prompt.tags:
                for tag in prompt.tags:
                    if tag.key == "status":
                        if tag.value == "production":
                            production_prompts.append(prompt)
                        elif tag.value in ["ab_testing", "testing"]:
                            testing_prompts.append(prompt)
                        break

        print(f"\n  Production ({len(production_prompts)} prompts):")
        for prompt in production_prompts:
            version = "N/A"
            for tag in prompt.tags:
                if tag.key == "version":
                    version = tag.value
                    break
            print(f"    ✅ {prompt.name} (v{version})")

        print(f"\n  Testing ({len(testing_prompts)} prompts):")
        for prompt in testing_prompts:
            print(f"    🧪 {prompt.name}")

        print("\n✨ Chapter 4 Complete: Production deployment ready!")

    def chapter5_multilanguage_support(self):
        """Chapter 5: Multi-language Support - Creating Localized Prompt Versions"""
        print("\n" + "="*60)
        print(" CHAPTER 5: MULTI-LANGUAGE SUPPORT")
        print("="*60)
        print("\nExpanding to global markets with localized prompts...")

        # Create Spanish version of greeting
        print("\n🌍 Creating Spanish greeting prompt...")
        spanish_greeting = """Eres un representante amable del servicio al cliente de TechMart.

Nombre del Cliente: ${customer_name}
Nivel del Cliente: ${customer_tier}
Hora del Día: ${time_of_day}

Saluda al cliente apropiadamente según su nivel y la hora del día.
Mantén el saludo cálido, profesional y en menos de 50 palabras."""

        self.prompt_client.save_prompt(
            prompt_name="customer_greeting_es",
            description="Spanish version of customer greeting",
            prompt_template=spanish_greeting
        )
        self.created_prompts.append("customer_greeting_es")

        spanish_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "greeting"),
            MetadataTag("language", "spanish"),
            MetadataTag("locale", "es-ES"),
            MetadataTag("base_prompt", "customer_greeting"),
            MetadataTag("status", "production"),
            MetadataTag("translator", "localization_team")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "customer_greeting_es",
            spanish_tags
        )
        print("✅ Spanish greeting created and tagged")

        # Create French version
        print("\n🌍 Creating French greeting prompt...")
        french_greeting = """Vous êtes un représentant sympathique du service client de TechMart.

Nom du Client: ${customer_name}
Niveau du Client: ${customer_tier}
Moment de la Journée: ${time_of_day}

Accueillez le client de manière appropriée selon son niveau et le moment de la journée.
Gardez l'accueil chaleureux, professionnel et en moins de 50 mots."""

        self.prompt_client.save_prompt(
            prompt_name="customer_greeting_fr",
            description="French version of customer greeting",
            prompt_template=french_greeting
        )
        self.created_prompts.append("customer_greeting_fr")

        french_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "greeting"),
            MetadataTag("language", "french"),
            MetadataTag("locale", "fr-FR"),
            MetadataTag("base_prompt", "customer_greeting"),
            MetadataTag("status", "testing"),
            MetadataTag("translator", "localization_team")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "customer_greeting_fr",
            french_tags
        )
        print("✅ French greeting created and tagged")

        # Create region-specific prompt
        print("\n🌍 Creating region-specific holiday prompt...")
        holiday_prompt = """You are a TechMart customer service representative during ${holiday_name}.

Customer: ${customer_name}
Region: ${customer_region}
Local Holiday: ${holiday_name}
Holiday Dates: ${holiday_dates}

Provide a holiday-appropriate greeting that:
1. Acknowledges the holiday celebration
2. Mentions any special holiday promotions
3. Sets expectations for holiday shipping times
4. Maintains cultural sensitivity

Keep response warm and festive while being informative."""

        self.prompt_client.save_prompt(
            prompt_name="holiday_greeting",
            description="Region-specific holiday greeting template",
            prompt_template=holiday_prompt
        )
        self.created_prompts.append("holiday_greeting")

        holiday_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "greeting"),
            MetadataTag("subtype", "seasonal"),
            MetadataTag("language", "english"),
            MetadataTag("localization", "required"),
            MetadataTag("update_frequency", "quarterly")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "holiday_greeting",
            holiday_tags
        )
        print("✅ Holiday greeting template created")

        # Display language support summary
        print("\n📊 Language Support Summary:")
        all_prompts = self.prompt_client.get_prompts()

        language_map = {}
        for prompt in all_prompts:
            if prompt.name in self.created_prompts and prompt.tags:
                for tag in prompt.tags:
                    if tag.key == "language":
                        lang = tag.value
                        if lang not in language_map:
                            language_map[lang] = []
                        language_map[lang].append(prompt.name)
                        break

        for language, prompt_names in language_map.items():
            print(f"\n  {language.upper()} ({len(prompt_names)} prompts):")
            for name in prompt_names:
                print(f"    - {name}")

        print("\n✨ Chapter 5 Complete: Multi-language support added!")

    def chapter6_performance_optimization(self):
        """Chapter 6: Performance Optimization - Testing Different Models and Parameters"""
        print("\n" + "="*60)
        print(" CHAPTER 6: PERFORMANCE OPTIMIZATION")
        print("="*60)
        print("\nOptimizing prompt performance across different models...")

        # Create a performance test prompt
        print("\n📝 Creating summarization prompt for performance testing...")
        summary_prompt = """Summarize the following customer interaction in ${summary_style} style:

Interaction Type: ${interaction_type}
Duration: ${duration}
Customer Sentiment: ${sentiment}
Details: ${interaction_details}

Requirements:
- Length: ${target_length} words
- Include: Key issues, actions taken, resolution status
- Format: ${output_format}"""

        self.prompt_client.save_prompt(
            prompt_name="interaction_summary",
            description="Summarize customer interactions for records",
            prompt_template=summary_prompt
        )
        self.created_prompts.append("interaction_summary")

        # Test with different model configurations
        print("\n🧪 Testing with different model parameters...")

        test_data = {
            "summary_style": "concise",
            "interaction_type": "technical_support",
            "duration": "15 minutes",
            "sentiment": "initially frustrated, resolved satisfied",
            "interaction_details": "Customer reported laptop not charging. Troubleshot power adapter, battery reset, and BIOS settings. Issue resolved with BIOS update.",
            "target_length": "50",
            "output_format": "bullet points"
        }

        # Test different configurations
        test_configs = [
            {
                "name": "Speed Optimized",
                "model": "gpt-4o",
                "temperature": 0.3,
                "top_p": 0.8,
                "use_case": "high_volume"
            },
            {
                "name": "Quality Optimized",
                "model": "gpt-4",
                "temperature": 0.5,
                "top_p": 0.9,
                "use_case": "complex_issues"
            },
            {
                "name": "Balanced",
                "model": "gpt-4o",
                "temperature": 0.7,
                "top_p": 0.9,
                "use_case": "standard"
            }
        ]

        for config in test_configs:
            print(f"\n  Testing '{config['name']}' configuration:")
            print(f"    Model: openai:{config['model']}")
            print(f"    Temperature: {config['temperature']}")
            print(f"    Top-p: {config['top_p']}")
            print(f"    Use case: {config['use_case']}")

            # Add performance tags
            perf_tags = [
                MetadataTag("category", "customer_service"),
                MetadataTag("type", "summary"),
                MetadataTag("model_config", config['name'].lower().replace(" ", "_")),
                MetadataTag("recommended_model", f"openai:{config['model']}"),
                MetadataTag("temperature", str(config['temperature'])),
                MetadataTag("top_p", str(config['top_p'])),
                MetadataTag("use_case", config['use_case'])
            ]

            # Create variant for this configuration
            variant_name = f"interaction_summary_{config['name'].lower().replace(' ', '_')}"
            if config['name'] != "Speed Optimized":  # Skip creating duplicate
                continue

        # Create optimized version based on "test results"
        print("\n📝 Creating optimized prompt based on performance tests...")
        optimized_prompt = """[OPTIMIZED] Summarize this ${interaction_type} interaction:

Duration: ${duration} | Sentiment: ${sentiment}
Details: ${interaction_details}

Output (${target_length} words, ${output_format}):"""

        self.prompt_client.save_prompt(
            prompt_name="interaction_summary_optimized",
            description="Performance-optimized summary prompt (30% faster)",
            prompt_template=optimized_prompt
        )
        self.created_prompts.append("interaction_summary_optimized")

        optimization_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "summary"),
            MetadataTag("optimization", "token_reduced"),
            MetadataTag("performance_gain", "30_percent"),
            MetadataTag("model", "openai:gpt-4o"),
            MetadataTag("benchmark_tokens", "150"),
            MetadataTag("status", "production")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "interaction_summary_optimized",
            optimization_tags
        )
        print("✅ Optimized prompt created with 30% performance improvement")

        # Create caching configuration prompt
        print("\n📝 Creating frequently-used FAQ prompt for caching...")
        faq_prompt = """Provide the standard answer for TechMart FAQ:

Question Category: ${category}
Specific Question: ${question}
Customer Type: ${customer_type}

Use official TechMart policies and keep response under 100 words."""

        self.prompt_client.save_prompt(
            prompt_name="faq_response",
            description="Cached responses for frequently asked questions",
            prompt_template=faq_prompt
        )
        self.created_prompts.append("faq_response")

        cache_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("type", "faq"),
            MetadataTag("cache_enabled", "true"),
            MetadataTag("cache_duration", "3600"),
            MetadataTag("cache_key_params", "category,question"),
            MetadataTag("update_frequency", "weekly")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "faq_response",
            cache_tags
        )
        print("✅ FAQ prompt configured for caching")

        print("\n✨ Chapter 6 Complete: Performance optimized!")

    def chapter7_compliance_audit(self):
        """Chapter 7: Compliance and Audit - Tag-based Compliance Tracking"""
        print("\n" + "="*60)
        print(" CHAPTER 7: COMPLIANCE AND AUDIT")
        print("="*60)
        print("\nImplementing compliance tracking and audit trails...")

        # Create PII-safe prompt
        print("\n📝 Creating PII-compliant prompt template...")
        pii_safe_prompt = """Process this customer request while maintaining data privacy:

Request Type: ${request_type}
Customer ID: ${customer_id_hash}  # Hashed identifier
Region: ${region}
Request: ${sanitized_request}  # PII removed

Compliance Requirements:
- Do not request or display personal information
- Reference customer only by ID
- Follow ${region} data protection regulations
- Maintain audit trail of actions

Provide appropriate response following privacy guidelines."""

        self.prompt_client.save_prompt(
            prompt_name="pii_safe_handler",
            description="PII-compliant customer request handler",
            prompt_template=pii_safe_prompt
        )
        self.created_prompts.append("pii_safe_handler")

        compliance_tags = [
            MetadataTag("category", "customer_service"),
            MetadataTag("compliance", "gdpr_compliant"),
            MetadataTag("compliance", "ccpa_compliant"),
            MetadataTag("data_classification", "public"),
            MetadataTag("pii_safe", "true"),
            MetadataTag("audit_required", "true"),
            MetadataTag("retention_days", "90"),
            MetadataTag("last_audit", "2024-12-24"),
            MetadataTag("auditor", "compliance_team")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "pii_safe_handler",
            compliance_tags
        )
        print("✅ PII-compliant prompt created and tagged")

        # Update existing prompts with compliance tags
        print("\n🔍 Auditing existing prompts for compliance...")

        all_prompts = self.prompt_client.get_prompts()

        audit_results = {
            "compliant": [],
            "needs_review": [],
            "non_compliant": []
        }

        for prompt in all_prompts:
            if prompt.name in self.created_prompts:
                # Check compliance status
                has_pii = "customer_name" in str(prompt.variables)
                has_compliance_tag = False

                if prompt.tags:
                    for tag in prompt.tags:
                        if tag.key == "compliance":
                            has_compliance_tag = True
                            break

                if has_compliance_tag:
                    audit_results["compliant"].append(prompt.name)
                elif has_pii:
                    audit_results["needs_review"].append(prompt.name)

                    # Add compliance warning tag
                    existing_tags = self.prompt_client.get_tags_for_prompt_template(prompt.name)
                    existing_tags.append(MetadataTag("compliance", "needs_pii_review"))
                    existing_tags.append(MetadataTag("audit_flag", "contains_personal_data"))

                    self.prompt_client.update_tag_for_prompt_template(
                        prompt.name,
                        existing_tags
                    )
                else:
                    audit_results["compliant"].append(prompt.name)

        # Display audit results
        print("\n📊 Compliance Audit Results:")
        print(f"\n  ✅ Compliant ({len(audit_results['compliant'])} prompts):")
        for name in audit_results['compliant'][:5]:  # Show first 5
            print(f"     - {name}")

        print(f"\n  ⚠️ Needs Review ({len(audit_results['needs_review'])} prompts):")
        for name in audit_results['needs_review']:
            print(f"     - {name} (contains PII fields)")

        # Create audit log prompt
        print("\n📝 Creating audit log generator prompt...")
        audit_log_prompt = """Generate an audit log entry for this customer service interaction:

Timestamp: ${timestamp}
Agent ID: ${agent_id}
Interaction ID: ${interaction_id}
Action Type: ${action_type}
Prompt Used: ${prompt_name}
Compliance Flags: ${compliance_flags}
Result: ${action_result}

Format the audit log according to company standards.
Include all required fields for regulatory compliance."""

        self.prompt_client.save_prompt(
            prompt_name="audit_log_generator",
            description="Generate standardized audit log entries",
            prompt_template=audit_log_prompt
        )
        self.created_prompts.append("audit_log_generator")

        audit_tags = [
            MetadataTag("category", "compliance"),
            MetadataTag("type", "audit"),
            MetadataTag("retention", "7_years"),
            MetadataTag("format", "structured_json"),
            MetadataTag("regulatory", "sox_required")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "audit_log_generator",
            audit_tags
        )
        print("✅ Audit log generator created")

        print("\n✨ Chapter 7 Complete: Compliance framework implemented!")

    def chapter8_cleanup_migration(self):
        """Chapter 8: Cleanup and Migration - Managing Prompt Lifecycle"""
        print("\n" + "="*60)
        print(" CHAPTER 8: CLEANUP AND MIGRATION")
        print("="*60)
        print("\nManaging prompt lifecycle and migration...")

        # Demonstrate tag cleanup
        print("\n🧹 Cleaning up obsolete tags...")

        # API 7: delete_tag_for_prompt_template() - Remove test tags
        if "return_request" in self.created_prompts:
            print("\n  Removing test tags from return_request prompt...")
            tags_to_remove = [
                MetadataTag("status", "testing"),
                MetadataTag("compliance", "requires_review")
            ]

            try:
                self.prompt_client.delete_tag_for_prompt_template(
                    "return_request",
                    tags_to_remove
                )
                print("  ✅ Test tags removed")
            except Exception as e:
                print(f"  ⚠️ Could not remove tags: {str(e)}")

        # Create deprecation notice
        print("\n📝 Creating migration prompt for legacy system...")
        migration_prompt = """[DEPRECATED - Use 'customer_greeting_v3' after ${migration_date}]

Legacy greeting format for backwards compatibility:
CUSTOMER: ${customer_name}
TIER: ${customer_tier}
TIME: ${time_of_day}

Generate old-style greeting (will be retired on ${migration_date})."""

        self.prompt_client.save_prompt(
            prompt_name="legacy_greeting_deprecated",
            description="DEPRECATED - Legacy greeting format for migration period",
            prompt_template=migration_prompt
        )
        self.created_prompts.append("legacy_greeting_deprecated")

        deprecation_tags = [
            MetadataTag("status", "deprecated"),
            MetadataTag("migration_target", "customer_greeting_v3"),
            MetadataTag("deprecation_date", "2025-01-01"),
            MetadataTag("removal_date", "2025-03-01"),
            MetadataTag("migration_guide", "docs/migration/greeting_v3.md")
        ]

        self.prompt_client.update_tag_for_prompt_template(
            "legacy_greeting_deprecated",
            deprecation_tags
        )
        print("✅ Legacy prompt marked for deprecation")

        # Archive old test variants
        print("\n📦 Archiving old test variants...")

        # Get all prompts for archival check
        all_prompts = self.prompt_client.get_prompts()

        archived_count = 0
        for prompt in all_prompts:
            if prompt.name in self.created_prompts and "test" in prompt.name.lower():
                # Get existing tags
                tags = self.prompt_client.get_tags_for_prompt_template(prompt.name)

                # Add archive tags
                archive_tags = tags if tags else []
                archive_tags.extend([
                    MetadataTag("status", "archived"),
                    MetadataTag("archived_date", "2024-12-24"),
                    MetadataTag("archive_reason", "test_completed")
                ])

                self.prompt_client.update_tag_for_prompt_template(
                    prompt.name,
                    archive_tags
                )
                archived_count += 1

        print(f"✅ Archived {archived_count} test variants")

        # Final statistics
        print("\n📊 Final Prompt Statistics:")

        all_prompts = self.prompt_client.get_prompts()
        stats = {
            "total": 0,
            "production": 0,
            "testing": 0,
            "deprecated": 0,
            "archived": 0,
            "by_language": {},
            "by_category": {}
        }

        for prompt in all_prompts:
            if prompt.name in self.created_prompts:
                stats["total"] += 1

                if prompt.tags:
                    for tag in prompt.tags:
                        if tag.key == "status":
                            if tag.value == "production":
                                stats["production"] += 1
                            elif tag.value == "testing":
                                stats["testing"] += 1
                            elif tag.value == "deprecated":
                                stats["deprecated"] += 1
                            elif tag.value == "archived":
                                stats["archived"] += 1
                        elif tag.key == "language":
                            lang = tag.value
                            stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1
                        elif tag.key == "category":
                            cat = tag.value
                            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

        print(f"\n  Total Prompts: {stats['total']}")
        print(f"  Production: {stats['production']}")
        print(f"  Testing: {stats['testing']}")
        print(f"  Deprecated: {stats['deprecated']}")
        print(f"  Archived: {stats['archived']}")

        if stats["by_language"]:
            print(f"\n  By Language:")
            for lang, count in stats["by_language"].items():
                print(f"    - {lang}: {count}")

        if stats["by_category"]:
            print(f"\n  By Category:")
            for cat, count in stats["by_category"].items():
                print(f"    - {cat}: {count}")

        # Demonstrate selective cleanup
        print("\n🗑️ Demonstrating selective cleanup...")

        # Only delete deprecated prompts in production
        if "legacy_greeting_deprecated" in self.created_prompts:
            print("  Deleting deprecated legacy prompt...")
            try:
                # API 4: delete_prompt() - Delete deprecated prompt
                self.prompt_client.delete_prompt("legacy_greeting_deprecated")
                self.created_prompts.remove("legacy_greeting_deprecated")
                print("  ✅ Deprecated prompt deleted")
            except Exception as e:
                print(f"  ⚠️ Could not delete: {str(e)}")

        print("\n✨ Chapter 8 Complete: Lifecycle management demonstrated!")

    def cleanup(self):
        """Clean up created resources."""
        print("\n" + "="*60)
        print(" CLEANUP")
        print("="*60)

        # Clean up prompts
        if self.created_prompts:
            print(f"\nCleaning up {len(self.created_prompts)} created prompts...")
            cleanup_count = 0
            for prompt_name in self.created_prompts:
                try:
                    self.prompt_client.delete_prompt(prompt_name)
                    cleanup_count += 1
                    print(f"  ✅ Deleted: {prompt_name}")
                except Exception as e:
                    print(f"  ⚠️ Could not delete {prompt_name}: {str(e)}")
            print(f"✅ Cleaned up {cleanup_count}/{len(self.created_prompts)} prompts")
        else:
            print("No prompts to clean up.")

        # Clean up integrations
        if self.created_integrations:
            print(f"\nCleaning up {len(self.created_integrations)} created integrations...")
            cleanup_count = 0
            for integration_name in self.created_integrations:
                try:
                    self.integration_client.delete_integration(integration_name)
                    cleanup_count += 1
                    print(f"  ✅ Deleted integration: {integration_name}")
                except Exception as e:
                    print(f"  ⚠️ Could not delete integration {integration_name}: {str(e)}")
            print(f"✅ Cleaned up {cleanup_count}/{len(self.created_integrations)} integrations")
        else:
            print("No integrations to clean up.")

        print("\n✅ Cleanup complete!")

    def display_api_coverage(self):
        """Display API coverage summary."""
        print("\n" + "="*60)
        print(" API COVERAGE SUMMARY")
        print("="*60)

        api_coverage = {
            "save_prompt()": "✅ Implemented - Create/update prompts",
            "get_prompt()": "✅ Implemented - Retrieve specific prompt",
            "get_prompts()": "✅ Implemented - List all prompts",
            "delete_prompt()": "✅ Implemented - Delete prompts",
            "get_tags_for_prompt_template()": "✅ Implemented - Get prompt tags",
            "update_tag_for_prompt_template()": "✅ Implemented - Update prompt tags",
            "delete_tag_for_prompt_template()": "✅ Implemented - Remove prompt tags",
            "test_prompt()": "✅ Implemented - Test prompts with AI"
        }

        print("\nPrompt Management APIs (8 total):")
        for api, status in api_coverage.items():
            print(f"  {status}")

        print(f"\n✅ Coverage: 8/8 APIs (100%)")


def main():
    """Main entry point for the prompt journey example."""
    journey = PromptJourney()

    # Display API coverage
    journey.display_api_coverage()

    # Run the journey
    journey.run()

    print("\n" + "="*80)
    print(" Thank you for exploring Prompt Management with Conductor!")
    print("="*80)
    print("\nFor more information, see:")
    print("  - Documentation: docs/PROMPT.md")
    print("  - Integration Guide: docs/INTEGRATION.md")


if __name__ == "__main__":
    main()