import copy
import json
from pathlib import Path


class JsonTemplateResolver:
    """Utility class for resolving JSON templates from a predefined resource file."""

    _templates_root = None
    _template_resource_path = "ser_deser_json_string.json"

    @classmethod
    def load_templates(cls):
        """Loads the templates from the predefined resource file."""
        # Look for the file in the current directory
        current_dir = Path(__file__).parent
        file_path = current_dir / cls._template_resource_path

        if not file_path.exists():
            raise FileNotFoundError(
                f"Resource not found: {cls._template_resource_path}"
            )

        with open(file_path, "r") as f:
            root = json.load(f)

        if "templates" not in root:
            raise ValueError("JSON template does not contain 'templates' root element")

        cls._templates_root = root["templates"]

    @classmethod
    def get_json_string(cls, template_name):
        """
        Gets the JSON string for a specified template.

        Args:
            template_name: The name of the template to resolve

        Returns:
            The resolved template as a JSON string
        """
        if cls._templates_root is None:
            cls.load_templates()

        # Get the template with inheritance handling
        resolved_node = cls._resolve_template_with_inheritance(template_name, set())

        # Resolve references in the node
        cls._resolve_references(resolved_node, set())

        # Convert to string and return
        return json.dumps(resolved_node)

    @classmethod
    def _resolve_template_with_inheritance(cls, template_name, processed_templates):
        """
        Resolves a template including all inherited fields from parent templates.

        Args:
            template_name: The name of the template to resolve
            processed_templates: Set of already processed templates to avoid circular inheritance

        Returns:
            The resolved template content with all inherited fields
        """
        if template_name in processed_templates:
            print(f"Warning: Circular inheritance detected for {template_name}")
            return {}

        processed_templates.add(template_name)

        if template_name not in cls._templates_root:
            raise ValueError(f"Template '{template_name}' not found")

        template = cls._templates_root[template_name]

        if "content" not in template:
            raise ValueError(
                f"Template '{template_name}' does not contain 'content' node"
            )

        content_node = template["content"]

        # If content is not a dict (e.g., it's a string, number, boolean), return it directly
        if not isinstance(content_node, dict):
            return copy.deepcopy(content_node)

        # Create a deep copy of the content node
        result_node = copy.deepcopy(content_node)

        # Process inheritance if present
        if "inherits" in template and isinstance(template["inherits"], list):
            for parent_name in template["inherits"]:
                # Resolve parent template
                parent_node = cls._resolve_template_with_inheritance(
                    parent_name, set(processed_templates)
                )

                # Only merge if parent is a dict
                if isinstance(parent_node, dict):
                    cls._merge_nodes(result_node, parent_node)

        return result_node

    @classmethod
    def _merge_nodes(cls, target, source):
        """
        Merges fields from the source node into the target node.
        Fields in the target node are not overwritten if they already exist.
        """
        if isinstance(source, dict):
            for field_name, source_value in source.items():
                # Only add the field if it doesn't exist in the target
                if field_name not in target:
                    if (
                        isinstance(source_value, dict)
                        and field_name in target
                        and isinstance(target[field_name], dict)
                    ):
                        # Recursively merge objects
                        cls._merge_nodes(target[field_name], source_value)
                    else:
                        # Add the field
                        target[field_name] = copy.deepcopy(source_value)

    @classmethod
    def _resolve_references(cls, node, processed_dependencies):
        """Resolves references in a JSON node."""
        if isinstance(node, dict):
            cls._resolve_object_references(node, processed_dependencies)
        elif isinstance(node, list):
            cls._resolve_array_references(node, processed_dependencies)

    @classmethod
    def _resolve_object_references(cls, obj_node, processed_dependencies):
        """Resolves references in an object node."""
        # Collect field names to avoid RuntimeError during iteration
        fields_to_process = list(obj_node.keys())

        for i, field_name in enumerate(fields_to_process):
            field_value = obj_node[field_name]

            # Check if the field name is a reference that needs to be resolved
            if cls._is_reference(field_name):
                reference_name = cls._extract_reference_name(field_name)

                # Use a clone of the processed dependencies for each field name
                field_dependencies = set(processed_dependencies)

                if reference_name in field_dependencies:
                    # Circular reference detected
                    print(f"Warning: Circular reference detected for {reference_name}")
                    continue

                field_dependencies.add(reference_name)

                # Resolve the template to get the actual key name
                resolved_reference = cls._resolve_template_with_inheritance(
                    reference_name, set()
                )

                # Only apply if the resolved reference is a simple value (string, number, etc.)
                if not isinstance(resolved_reference, (dict, list)):
                    resolved_key = str(resolved_reference)

                    # Remove the original reference key and add the resolved key with the same value
                    original_value = obj_node.pop(field_name)
                    obj_node[resolved_key] = original_value

                    # Update the field name for further processing
                    fields_to_process[i] = resolved_key
                    field_value = original_value

            # Check if the field value is a string reference
            if isinstance(field_value, str):
                text_value = field_value
                if cls._is_reference(text_value):
                    reference_name = cls._extract_reference_name(text_value)

                    # Use a clone of the processed dependencies for each field
                    field_dependencies = set(processed_dependencies)

                    if reference_name in field_dependencies:
                        # Circular reference detected
                        print(
                            f"Warning: Circular reference detected for {reference_name}"
                        )
                        continue

                    field_dependencies.add(reference_name)

                    # Resolve the template WITH inheritance
                    resolved_reference = cls._resolve_template_with_inheritance(
                        reference_name, set()
                    )

                    # Resolve any references in the resolved template
                    cls._resolve_references(resolved_reference, field_dependencies)
                    obj_node[field_name] = resolved_reference
            elif isinstance(field_value, (dict, list)):
                # Use a clone of processed dependencies for nested structures
                cls._resolve_references(field_value, set(processed_dependencies))

    @classmethod
    def _resolve_array_references(cls, array_node, processed_dependencies):
        """Resolves references in an array node."""
        for i in range(len(array_node)):
            element = array_node[i]

            if isinstance(element, str):
                text_value = element
                if cls._is_reference(text_value):
                    reference_name = cls._extract_reference_name(text_value)

                    # Clone the dependencies for each array element
                    element_dependencies = set(processed_dependencies)

                    if reference_name in element_dependencies:
                        # Circular reference detected
                        print(
                            f"Warning: Circular reference detected for {reference_name}"
                        )
                        continue

                    element_dependencies.add(reference_name)

                    # Resolve the template WITH inheritance
                    resolved_reference = cls._resolve_template_with_inheritance(
                        reference_name, set()
                    )

                    # Resolve any references in the resolved template
                    cls._resolve_references(resolved_reference, element_dependencies)
                    array_node[i] = resolved_reference
            elif isinstance(element, (dict, list)):
                # Recursively process nested objects and arrays
                cls._resolve_references(element, set(processed_dependencies))

    @staticmethod
    def _is_reference(value):
        """Checks if a string value is a template reference."""
        return isinstance(value, str) and value.startswith("${") and value.endswith("}")

    @staticmethod
    def _extract_reference_name(reference):
        """Extracts the reference name from a reference string."""
        return reference[2:-1]
