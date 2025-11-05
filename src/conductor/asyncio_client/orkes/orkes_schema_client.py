from __future__ import annotations

from typing import List, Optional

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesSchemaClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        """Initialize the OrkesSchemaClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            schema_client = OrkesSchemaClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Core Schema Operations
    @deprecated("save_schemas is deprecated; use register_schema instead")
    @typing_deprecated("save_schemas is deprecated; use register_schema instead")
    async def save_schemas(
        self, schema_defs: List[SchemaDefAdapter], new_version: Optional[bool] = None
    ) -> None:
        """Save one or more schema definitions.

        .. deprecated::
            Use register_schemas instead for consistent API interface.

        Args:
            schema_defs: List of schema definitions to save
            new_version: If True, create new versions of existing schemas

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter

            schemas = [
                SchemaDefAdapter(name="user_schema", version=1, data={"type": "object"}),
                SchemaDefAdapter(name="order_schema", version=1, data={"type": "object"})
            ]
            await schema_client.save_schemas(schemas)
            ```
        """
        await self._schema_api.save(schema_defs, new_version=new_version)

    async def register_schemas(
        self, schema_defs: List[SchemaDefAdapter], new_version: Optional[bool] = None, **kwargs
    ) -> None:
        """Register one or more schema definitions.

        Schema definitions define data structures and validation rules for workflow inputs/outputs.

        Args:
            schema_defs: List of schema definitions to register
            new_version: If True, create new versions of existing schemas
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter

            # Register JSON schemas for data validation
            schemas = [
                SchemaDefAdapter(
                    name="user_schema",
                    version=1,
                    type="JSON",
                    data={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"}
                        },
                        "required": ["name", "email"]
                    }
                )
            ]
            await schema_client.register_schemas(schemas)
            ```
        """
        await self._schema_api.save(schema_def=schema_defs, new_version=new_version, **kwargs)

    @deprecated("save_schema is deprecated; use register_schema instead")
    @typing_deprecated("save_schema is deprecated; use register_schema instead")
    async def save_schema(
        self, schema_def: SchemaDefAdapter, new_version: Optional[bool] = None
    ) -> None:
        """Save a single schema definition.

        .. deprecated::
            Use register_schema instead for consistent API interface.

        Args:
            schema_def: Schema definition to save
            new_version: If True, create a new version of existing schema

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter

            schema = SchemaDefAdapter(name="user_schema", version=1, data={"type": "object"})
            await schema_client.save_schema(schema)
            ```
        """
        await self.save_schemas([schema_def], new_version=new_version)

    async def register_schema(
        self, schema_def: SchemaDefAdapter, new_version: Optional[bool] = None, **kwargs
    ) -> None:
        """Register a single schema definition.

        Args:
            schema_def: Schema definition to register
            new_version: If True, create a new version of existing schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter

            schema = SchemaDefAdapter(
                name="order_schema",
                version=1,
                type="JSON",
                data={
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "items": {"type": "array"},
                        "total": {"type": "number"}
                    }
                }
            )
            await schema_client.register_schema(schema)
            ```
        """
        await self.register_schemas(schema_defs=[schema_def], new_version=new_version, **kwargs)

    async def get_schema(self, name: str, version: int, **kwargs) -> SchemaDefAdapter:
        """Get a specific schema by name and version.

        Args:
            name: Name of the schema
            version: Version number
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SchemaDefAdapter instance containing the schema definition

        Example:
            ```python
            schema = await schema_client.get_schema("user_schema", version=1)
            print(f"Schema type: {schema.type}")
            print(f"Schema data: {schema.data}")
            ```
        """
        return await self._schema_api.get_schema_by_name_and_version(
            name=name, version=version, **kwargs
        )

    async def get_all_schemas(self, **kwargs) -> List[SchemaDefAdapter]:
        """Get all schema definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of all SchemaDefAdapter instances

        Example:
            ```python
            schemas = await schema_client.get_all_schemas()
            for schema in schemas:
                print(f"Schema: {schema.name} v{schema.version}")
            ```
        """
        return await self._schema_api.get_all_schemas(**kwargs)

    async def delete_schema_by_name(self, name: str, **kwargs) -> None:
        """Delete all versions of a schema by name.

        Args:
            name: Name of the schema to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Delete all versions of a schema
            await schema_client.delete_schema_by_name("old_user_schema")
            ```
        """
        await self._schema_api.delete_schema_by_name(name=name, **kwargs)

    async def delete_schema_by_name_and_version(self, name: str, version: int, **kwargs) -> None:
        """Delete a specific version of a schema.

        Args:
            name: Name of the schema
            version: Version number to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Delete only version 1 of the schema
            await schema_client.delete_schema_by_name_and_version("user_schema", 1)
            ```
        """
        await self._schema_api.delete_schema_by_name_and_version(
            name=name, version=version, **kwargs
        )

    # Convenience Methods
    async def create_schema(
        self, name: str, version: int, schema_definition: dict, schema_type: str = "JSON", **kwargs
    ) -> None:
        """Create a new schema with simplified parameters.

        Convenience method for creating schemas from dictionary definitions.

        Args:
            name: Name of the schema
            version: Version number
            schema_definition: Schema data as dictionary (e.g., JSON Schema)
            schema_type: Type of schema (default: "JSON")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Create a JSON schema for user data
            schema_def = {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0}
                },
                "required": ["user_id", "name"]
            }
            await schema_client.create_schema("user_schema", 1, schema_def)
            ```
        """
        schema_def = SchemaDefAdapter(
            name=name,
            version=version,
            data=schema_definition,
            type=schema_type,
        )
        await self.register_schema(schema_def=schema_def, **kwargs)

    async def update_schema(
        self,
        name: str,
        version: int,
        schema_definition: dict,
        schema_type: str = "JSON",
        create_new_version: bool = False,
        **kwargs,
    ) -> None:
        """Update an existing schema.

        Args:
            name: Name of the schema
            version: Version number
            schema_definition: Updated schema data as dictionary
            schema_type: Type of schema (default: "JSON")
            create_new_version: If True, create a new version instead of overwriting
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Update existing schema
            updated_schema = {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"}
                }
            }
            await schema_client.update_schema("user_schema", 1, updated_schema)

            # Create new version
            await schema_client.update_schema(
                "user_schema", 2, updated_schema, create_new_version=True
            )
            ```
        """
        schema_def = SchemaDefAdapter(
            name=name,
            version=version,
            data=schema_definition,
            type=schema_type,
        )
        await self.register_schema(schema_def=schema_def, new_version=create_new_version, **kwargs)

    async def schema_exists(self, name: str, version: int, **kwargs) -> bool:
        """Check if a specific schema version exists.

        Args:
            name: Name of the schema
            version: Version number to check
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            True if schema exists, False otherwise

        Example:
            ```python
            if await schema_client.schema_exists("user_schema", 1):
                print("Schema version 1 exists")
            else:
                print("Schema version 1 not found")
            ```
        """
        try:
            await self.get_schema(name=name, version=version, **kwargs)
            return True
        except Exception:
            return False

    async def get_latest_schema_version(self, name: str, **kwargs) -> Optional[SchemaDefAdapter]:
        """Get the latest version of a schema by name.

        Args:
            name: Name of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            SchemaDefAdapter instance for the latest version, or None if not found

        Example:
            ```python
            latest = await schema_client.get_latest_schema_version("user_schema")
            if latest:
                print(f"Latest version: {latest.version}")
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)
        matching_schemas = [schema for schema in all_schemas if schema.name == name]

        if not matching_schemas:
            return None

        # Find the schema with the highest version number
        return max(matching_schemas, key=lambda schema: schema.version or 0)

    async def get_schema_versions(self, name: str, **kwargs) -> List[int]:
        """Get all version numbers for a schema.

        Args:
            name: Name of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Sorted list of version numbers

        Example:
            ```python
            versions = await schema_client.get_schema_versions("user_schema")
            print(f"Available versions: {versions}")  # [1, 2, 3]
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)
        versions = [
            schema.version
            for schema in all_schemas
            if schema.name == name and schema.version is not None
        ]
        return sorted(versions)

    async def get_schemas_by_name(self, name: str, **kwargs) -> List[SchemaDefAdapter]:
        """Get all versions of a schema by name.

        Args:
            name: Name of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of SchemaDefAdapter instances for all versions

        Example:
            ```python
            versions = await schema_client.get_schemas_by_name("user_schema")
            for schema in versions:
                print(f"Version {schema.version}: {schema.data}")
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)
        return [schema for schema in all_schemas if schema.name == name]

    async def get_schema_count(self, **kwargs) -> int:
        """Get the total number of schema definitions.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Total count of schemas as integer

        Example:
            ```python
            count = await schema_client.get_schema_count()
            print(f"Total schemas: {count}")
            ```
        """
        schemas = await self.get_all_schemas(**kwargs)
        return len(schemas)

    async def get_unique_schema_names(self, **kwargs) -> List[str]:
        """Get a list of unique schema names.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Sorted list of unique schema names

        Example:
            ```python
            names = await schema_client.get_unique_schema_names()
            print(f"Schema names: {names}")
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)
        names = {schema.name for schema in all_schemas if schema.name}
        return sorted(names)

    async def bulk_save_schemas(
        self, schemas: List[dict], new_version: Optional[bool] = None, **kwargs
    ) -> None:
        """Save multiple schemas from dictionary definitions.

        Convenience method for bulk schema creation from dictionaries.

        Args:
            schemas: List of schema dictionaries with keys: name, version, data, type
            new_version: If True, create new versions of existing schemas
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            schemas = [
                {
                    "name": "user_schema",
                    "version": 1,
                    "data": {"type": "object", "properties": {"name": {"type": "string"}}},
                    "type": "JSON"
                },
                {
                    "name": "order_schema",
                    "version": 1,
                    "data": {"type": "object", "properties": {"order_id": {"type": "string"}}},
                    "type": "JSON"
                }
            ]
            await schema_client.bulk_save_schemas(schemas)
            ```
        """
        schema_defs = []
        for schema_dict in schemas:
            schema_def = SchemaDefAdapter(
                name=schema_dict.get("name"),
                version=schema_dict.get("version"),
                data=schema_dict.get("data"),
                type=schema_dict.get("type", "JSON"),
            )
            schema_defs.append(schema_def)

        await self.register_schemas(schema_defs=schema_defs, new_version=new_version, **kwargs)

    async def clone_schema(
        self, source_name: str, source_version: int, target_name: str, target_version: int, **kwargs
    ) -> None:
        """Clone an existing schema to a new name/version.

        Args:
            source_name: Name of the source schema
            source_version: Version of the source schema
            target_name: Name for the cloned schema
            target_version: Version for the cloned schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Clone user_schema v1 as customer_schema v1
            await schema_client.clone_schema(
                "user_schema", 1,
                "customer_schema", 1
            )
            ```
        """
        source_schema = await self.get_schema(name=source_name, version=source_version, **kwargs)

        cloned_schema = SchemaDefAdapter(
            name=target_name,
            version=target_version,
            data=source_schema.data,
            type=source_schema.type,
        )

        await self.register_schema(schema_def=cloned_schema, **kwargs)

    async def delete_all_schema_versions(self, name: str, **kwargs) -> None:
        """Delete all versions of a schema (alias for delete_schema_by_name).

        Args:
            name: Name of the schema
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await schema_client.delete_all_schema_versions("old_schema")
            ```
        """
        await self.delete_schema_by_name(name=name, **kwargs)

    async def search_schemas_by_name(self, name_pattern: str, **kwargs) -> List[SchemaDefAdapter]:
        """Search schemas by name pattern (case-insensitive).

        Args:
            name_pattern: Pattern to search for in schema names
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of SchemaDefAdapter instances matching the pattern

        Example:
            ```python
            # Find all schemas with "user" in the name
            schemas = await schema_client.search_schemas_by_name("user")
            for schema in schemas:
                print(f"Found: {schema.name} v{schema.version}")
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)
        return [
            schema for schema in all_schemas if name_pattern.lower() in (schema.name or "").lower()
        ]

    async def get_schemas_with_external_ref(
        self, external_ref_pattern: str, **kwargs
    ) -> List[SchemaDefAdapter]:
        """Find schemas that contain a specific text in their external ref.

        Args:
            external_ref_pattern: Pattern to search for in external references
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of SchemaDefAdapter instances with matching external ref

        Example:
            ```python
            # Find schemas referencing a specific URL
            schemas = await schema_client.get_schemas_with_external_ref("https://example.com")
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)
        return [
            schema
            for schema in all_schemas
            if schema.external_ref and external_ref_pattern.lower() in schema.external_ref.lower()
        ]

    async def validate_schema_structure(self, schema_definition: dict, **kwargs) -> bool:
        """Basic validation to check if schema definition has required structure.

        Args:
            schema_definition: Schema data to validate
            **kwargs: Additional optional parameters

        Returns:
            True if schema is valid (non-empty dict), False otherwise

        Example:
            ```python
            schema_def = {"type": "object", "properties": {}}
            is_valid = await schema_client.validate_schema_structure(schema_def)
            if is_valid:
                print("Schema structure is valid")
            ```
        """
        # This is a basic validation - you might want to add more sophisticated JSON schema validation
        return isinstance(schema_definition, dict) and len(schema_definition) > 0

    async def get_schema_statistics(self, **kwargs) -> dict:
        """Get comprehensive statistics about schemas.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Dictionary containing schema statistics

        Example:
            ```python
            stats = await schema_client.get_schema_statistics()
            print(f"Total schemas: {stats['total_schemas']}")
            print(f"Unique names: {stats['unique_schema_names']}")
            print(f"Version counts: {stats['version_counts']}")
            ```
        """
        all_schemas = await self.get_all_schemas(**kwargs)

        unique_names = set()
        version_counts: dict[str, int] = {}

        for schema in all_schemas:
            if schema.name:
                unique_names.add(schema.name)
                version_counts[schema.name] = version_counts.get(schema.name, 0) + 1

        return {
            "total_schemas": len(all_schemas),
            "unique_schema_names": len(unique_names),
            "schemas_with_external_ref": len([s for s in all_schemas if s.external_ref]),
            "version_counts": version_counts,
            "schema_names": sorted(unique_names),
        }

    # Legacy compatibility methods (aliasing new method names to match the original draft)
    async def list_schemas(self, **kwargs) -> List[SchemaDefAdapter]:
        """Get all schema definitions (legacy alias).

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of all SchemaDefAdapter instances

        Example:
            ```python
            schemas = await schema_client.list_schemas()
            ```
        """
        return await self.get_all_schemas(**kwargs)

    async def delete_schema(self, name: str, version: Optional[int] = None, **kwargs) -> None:
        """Delete a schema (by name only or by name and version).

        Args:
            name: Name of the schema to delete
            version: Optional version number. If None, deletes all versions
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Delete all versions
            await schema_client.delete_schema("old_schema")

            # Delete specific version
            await schema_client.delete_schema("user_schema", version=1)
            ```
        """
        if version is not None:
            await self.delete_schema_by_name_and_version(name=name, version=version, **kwargs)
        else:
            await self.delete_schema_by_name(name=name, **kwargs)

    async def create_schema_version(
        self, name: str, schema_definition: dict, schema_type: str = "JSON", **kwargs
    ) -> None:
        """Create a new version of an existing schema.

        Automatically increments the version number based on existing versions.

        Args:
            name: Name of the schema
            schema_definition: Schema data as dictionary
            schema_type: Type of schema (default: "JSON")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Automatically creates the next version
            new_schema_data = {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                }
            }
            await schema_client.create_schema_version("user_schema", new_schema_data)
            # If user_schema has versions 1,2,3, this creates version 4
            ```
        """
        # Get the highest version number for this schema
        versions = await self.get_schema_versions(name=name, **kwargs)
        new_version = max(versions) + 1 if versions else 1

        await self.create_schema(
            name=name,
            version=new_version,
            schema_definition=schema_definition,
            schema_type=schema_type,
            **kwargs,
        )
