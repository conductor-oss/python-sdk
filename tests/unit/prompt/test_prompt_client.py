"""
Unit tests for OrkesPromptClient

These tests verify the prompt client implementation including:
- Method implementations
- Return value handling
- Bug fixes (especially the get_tags_for_prompt_template return value)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_prompt_client import OrkesPromptClient
from conductor.client.http.models.prompt_template import PromptTemplate
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.http.rest import ApiException


class TestOrkesPromptClient(unittest.TestCase):
    """Test cases for OrkesPromptClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Configuration(server_api_url="http://test.com/api")

        # Create client and mock the promptApi
        with patch('conductor.client.orkes.orkes_prompt_client.OrkesBaseClient.__init__'):
            self.client = OrkesPromptClient.__new__(OrkesPromptClient)
            self.client.configuration = self.config
            self.client.promptApi = Mock()

    def test_save_prompt(self):
        """Test save_prompt method."""
        # Test normal save (default parameters)
        self.client.save_prompt("test_prompt", "Test description", "Template ${var}")

        # Verify API was called correctly without optional parameters
        self.client.promptApi.save_message_template.assert_called_once_with(
            "Template ${var}",
            "Test description",
            "test_prompt"
        )

    def test_save_prompt_with_auto_increment(self):
        """Test save_prompt with auto_increment=True."""
        self.client.save_prompt("test_prompt", "Test description", "Template ${var}", auto_increment=True)

        # Verify API was called with autoIncrement parameter
        self.client.promptApi.save_message_template.assert_called_once_with(
            "Template ${var}",
            "Test description",
            "test_prompt",
            autoIncrement=True
        )

    def test_save_prompt_with_all_options(self):
        """Test save_prompt with all optional parameters."""
        self.client.save_prompt(
            "test_prompt",
            "Test description",
            "Template ${var}",
            models=["gpt-4", "claude-3"],
            version=2,
            auto_increment=True
        )

        # Verify API was called with all parameters
        self.client.promptApi.save_message_template.assert_called_once_with(
            "Template ${var}",
            "Test description",
            "test_prompt",
            models=["gpt-4", "claude-3"],
            version=2,
            autoIncrement=True
        )

    def test_get_prompt_found(self):
        """Test get_prompt when prompt exists."""
        # Mock return value
        mock_prompt = PromptTemplate()
        mock_prompt.name = "test_prompt"
        mock_prompt.description = "Test"
        self.client.promptApi.get_message_template.return_value = mock_prompt

        # Call method
        result = self.client.get_prompt("test_prompt")

        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test_prompt")
        self.client.promptApi.get_message_template.assert_called_once_with("test_prompt")

    def test_get_prompt_not_found(self):
        """Test get_prompt when prompt doesn't exist (404)."""
        # Mock ApiException with 404
        api_exception = ApiException(status=404)
        api_exception.status = 404
        self.client.promptApi.get_message_template.side_effect = api_exception

        # Call method
        result = self.client.get_prompt("non_existent")

        # Should return None for not found
        self.assertIsNone(result)

    def test_get_prompt_other_error(self):
        """Test get_prompt with non-404 error."""
        # Mock ApiException with 500
        api_exception = ApiException(status=500)
        api_exception.status = 500
        self.client.promptApi.get_message_template.side_effect = api_exception

        # Should raise the exception
        with self.assertRaises(ApiException):
            self.client.get_prompt("test_prompt")

    def test_get_prompts(self):
        """Test get_prompts method."""
        # Mock return value
        mock_prompts = [
            Mock(name="prompt1"),
            Mock(name="prompt2")
        ]
        self.client.promptApi.get_message_templates.return_value = mock_prompts

        # Call method
        result = self.client.get_prompts()

        # Verify
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.client.promptApi.get_message_templates.assert_called_once()

    def test_delete_prompt(self):
        """Test delete_prompt method."""
        # Call method
        self.client.delete_prompt("test_prompt")

        # Verify API was called
        self.client.promptApi.delete_message_template.assert_called_once_with("test_prompt")

    def test_get_tags_for_prompt_template_returns_value(self):
        """Test that get_tags_for_prompt_template returns the value (bug fix verification)."""
        # Mock return value
        mock_tags = [
            MetadataTag("category", "test"),
            MetadataTag("status", "active")
        ]
        self.client.promptApi.get_tags_for_prompt_template.return_value = mock_tags

        # Call method
        result = self.client.get_tags_for_prompt_template("test_prompt")

        # CRITICAL: Verify it returns the value (this was the bug)
        self.assertIsNotNone(result, "get_tags_for_prompt_template must return a value")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].key, "category")
        self.assertEqual(result[0].value, "test")

    def test_update_tag_for_prompt_template(self):
        """Test update_tag_for_prompt_template method."""
        # Create tags
        tags = [
            MetadataTag("key1", "value1"),
            MetadataTag("key2", "value2")
        ]

        # Call method
        self.client.update_tag_for_prompt_template("test_prompt", tags)

        # Verify API was called with correct order
        self.client.promptApi.put_tag_for_prompt_template.assert_called_once_with(
            tags,
            "test_prompt"
        )

    def test_delete_tag_for_prompt_template(self):
        """Test delete_tag_for_prompt_template method."""
        # Create tags
        tags = [MetadataTag("key1", "value1")]

        # Call method
        self.client.delete_tag_for_prompt_template("test_prompt", tags)

        # Verify API was called
        self.client.promptApi.delete_tag_for_prompt_template.assert_called_once_with(
            tags,
            "test_prompt"
        )

    def test_test_prompt_basic(self):
        """Test test_prompt with basic parameters."""
        # Mock return
        self.client.promptApi.test_message_template.return_value = "AI response"

        # Call method
        result = self.client.test_prompt(
            prompt_text="Hello ${name}",
            variables={"name": "World"},
            ai_integration="openai",
            text_complete_model="gpt-3.5-turbo"
        )

        # Verify
        self.assertEqual(result, "AI response")

        # Check the request object passed
        call_args = self.client.promptApi.test_message_template.call_args[0]
        request = call_args[0]
        self.assertEqual(request.prompt, "Hello ${name}")
        self.assertEqual(request.prompt_variables, {"name": "World"})
        self.assertEqual(request.llm_provider, "openai")
        self.assertEqual(request.model, "gpt-3.5-turbo")
        self.assertEqual(request.temperature, 0.1)  # default
        self.assertEqual(request.top_p, 0.9)  # default

    def test_test_prompt_with_all_parameters(self):
        """Test test_prompt with all parameters including optionals."""
        # Mock return
        self.client.promptApi.test_message_template.return_value = "AI response"

        # Call with all parameters
        result = self.client.test_prompt(
            prompt_text="Generate text",
            variables={"topic": "AI"},
            ai_integration="openai",
            text_complete_model="gpt-4",
            temperature=0.8,
            top_p=0.95,
            stop_words=["END", "STOP"]
        )

        # Verify
        self.assertEqual(result, "AI response")

        # Check request
        call_args = self.client.promptApi.test_message_template.call_args[0]
        request = call_args[0]
        self.assertEqual(request.temperature, 0.8)
        self.assertEqual(request.top_p, 0.95)
        self.assertEqual(request.stop_words, ["END", "STOP"])

    def test_test_prompt_with_none_stop_words(self):
        """Test test_prompt handles None stop_words correctly."""
        # Mock return
        self.client.promptApi.test_message_template.return_value = "AI response"

        # Call with None stop_words
        result = self.client.test_prompt(
            prompt_text="Test",
            variables={},
            ai_integration="openai",
            text_complete_model="gpt-3.5-turbo",
            stop_words=None
        )

        # Verify the request doesn't have stop_words set when None
        call_args = self.client.promptApi.test_message_template.call_args[0]
        request = call_args[0]

        # The implementation should check if stop_words is not None before setting
        # If None, it shouldn't set the attribute
        if hasattr(request, 'stop_words'):
            # If it has the attribute, it should be None or empty
            self.assertIn(request.stop_words, [None, []])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Configuration(server_api_url="http://test.com/api")

        with patch('conductor.client.orkes.orkes_prompt_client.OrkesBaseClient.__init__'):
            self.client = OrkesPromptClient.__new__(OrkesPromptClient)
            self.client.configuration = self.config
            self.client.promptApi = Mock()

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        # Empty name should be passed through (let server validate)
        self.client.save_prompt("", "desc", "template")
        self.client.promptApi.save_message_template.assert_called()

        # Empty description
        self.client.save_prompt("name", "", "template")
        self.client.promptApi.save_message_template.assert_called()

        # Empty template
        self.client.save_prompt("name", "desc", "")
        self.client.promptApi.save_message_template.assert_called()

    def test_special_characters_in_names(self):
        """Test special characters in prompt names."""
        special_names = [
            "test-with-dash",
            "test_with_underscore",
            "test.with.dot",
            "TEST_UPPER",
            "test123"
        ]

        for name in special_names:
            self.client.save_prompt(name, "desc", "template")

        # All should be called
        self.assertEqual(self.client.promptApi.save_message_template.call_count, len(special_names))

    def test_unicode_handling(self):
        """Test Unicode characters."""
        # Unicode in name
        self.client.save_prompt("测试prompt", "desc", "template")

        # Unicode in template
        self.client.save_prompt("test", "desc", "你好 ${name} مرحبا")

        # Both calls should succeed
        self.assertEqual(self.client.promptApi.save_message_template.call_count, 2)

    def test_large_data(self):
        """Test handling of large data."""
        # Very long name
        long_name = "a" * 1000
        self.client.save_prompt(long_name, "desc", "template")

        # Very long template
        long_template = "Line ${var}\n" * 1000
        self.client.save_prompt("test", "desc", long_template)

        # Both should be called
        self.assertEqual(self.client.promptApi.save_message_template.call_count, 2)

    def test_empty_tag_list(self):
        """Test handling empty tag list."""
        # Empty list should be allowed
        self.client.update_tag_for_prompt_template("test", [])
        self.client.promptApi.put_tag_for_prompt_template.assert_called_with([], "test")

    def test_duplicate_tags(self):
        """Test duplicate tags with same key."""
        tags = [
            MetadataTag("env", "dev"),
            MetadataTag("env", "prod"),
            MetadataTag("env", "staging")
        ]

        self.client.update_tag_for_prompt_template("test", tags)

        # Should pass all tags (let server handle duplicates)
        call_args = self.client.promptApi.put_tag_for_prompt_template.call_args
        self.assertEqual(len(call_args[0][0]), 3)


class TestVersionDefault(unittest.TestCase):
    """Test version field default value."""

    def test_version_defaults_to_one(self):
        """Test that version defaults to 1, not 0 or None."""
        # Create template without version
        template = PromptTemplate()
        self.assertEqual(template.version, 1, "Version should default to 1")

        # Create with other fields but no version
        template2 = PromptTemplate(name="test", description="desc")
        self.assertEqual(template2.version, 1, "Version should still default to 1")

        # Explicit version should be preserved
        template3 = PromptTemplate(version=5)
        self.assertEqual(template3.version, 5, "Explicit version should be preserved")

        # Version 0 should be allowed if explicitly set
        template4 = PromptTemplate(version=0)
        self.assertEqual(template4.version, 0, "Version 0 should be allowed when explicit")


class TestReturnTypes(unittest.TestCase):
    """Verify return types of all methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Configuration(server_api_url="http://test.com/api")

        with patch('conductor.client.orkes.orkes_prompt_client.OrkesBaseClient.__init__'):
            self.client = OrkesPromptClient.__new__(OrkesPromptClient)
            self.client.configuration = self.config
            self.client.promptApi = Mock()

    def test_methods_returning_none(self):
        """Test methods that should return None."""
        # These methods should return None
        result = self.client.save_prompt("test", "desc", "template")
        self.assertIsNone(result)

        result = self.client.delete_prompt("test")
        self.assertIsNone(result)

        result = self.client.update_tag_for_prompt_template("test", [])
        self.assertIsNone(result)

        result = self.client.delete_tag_for_prompt_template("test", [])
        self.assertIsNone(result)

    def test_methods_returning_objects(self):
        """Test methods that return objects."""
        # get_prompt returns PromptTemplate or None
        self.client.promptApi.get_message_template.return_value = PromptTemplate()
        result = self.client.get_prompt("test")
        self.assertIsInstance(result, PromptTemplate)

        # get_prompts returns list
        self.client.promptApi.get_message_templates.return_value = []
        result = self.client.get_prompts()
        self.assertIsInstance(result, list)

        # get_tags_for_prompt_template returns list (THIS WAS THE BUG)
        self.client.promptApi.get_tags_for_prompt_template.return_value = []
        result = self.client.get_tags_for_prompt_template("test")
        self.assertIsInstance(result, list)

        # test_prompt returns string
        self.client.promptApi.test_message_template.return_value = "response"
        result = self.client.test_prompt("prompt", {}, "ai", "model")
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()