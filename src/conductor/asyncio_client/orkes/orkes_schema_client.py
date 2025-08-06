from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.schema_def_adapter import SchemaDefAdapter
from conductor.asyncio_client.http.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient


class OrkesSchemaClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration):
        super(OrkesSchemaClient, self).__init__(configuration)

    # Core Schema Operations
    async def save_schemas(
        self, schema_defs: List[SchemaDefAdapter], new_version: Optional[bool] = None
    ) -> None:
        """Save one or more schema definitions"""
        await self.schema_api.save(schema_defs, new_version=new_version)

    async def save_schema(
        self, schema_def: SchemaDefAdapter, new_version: Optional[bool] = None
    ) -> None:
        """Save a single schema definition"""
        await self.save_schemas([schema_def], new_version=new_version)

    async def get_schema(self, name: str, version: int) -> SchemaDefAdapter:
        """Get a specific schema by name and version"""
        return await self.schema_api.get_schema_by_name_and_version(name, version)

    async def get_all_schemas(self) -> List[SchemaDefAdapter]:
        """Get all schema definitions"""
        return await self.schema_api.get_all_schemas()

    async def delete_schema_by_name(self, name: str) -> None:
        """Delete all versions of a schema by name"""
        await self.schema_api.delete_schema_by_name(name)

    async def delete_schema_by_name_and_version(self, name: str, version: int) -> None:
        """Delete a specific version of a schema"""
        await self.schema_api.delete_schema_by_name_and_version(name, version)

    # Convenience Methods
    async def create_schema(
        self,
        name: str,
        version: int,
        schema_definition: dict,
        description: Optional[str] = None,
    ) -> None:
        """Create a new schema with simplified parameters"""
        schema_def = SchemaDefAdapter(
            name=name,
            version=version,
            schema=schema_definition,
            description=description,
        )
        await self.save_schema(schema_def)

    async def update_schema(
        self,
        name: str,
        version: int,
        schema_definition: dict,
        description: Optional[str] = None,
        create_new_version: bool = False,
    ) -> None:
        """Update an existing schema"""
        schema_def = SchemaDefAdapter(
            name=name,
            version=version,
            schema=schema_definition,
            description=description,
        )
        await self.save_schema(schema_def, new_version=create_new_version)

    async def schema_exists(self, name: str, version: int) -> bool:
        """Check if a specific schema version exists"""
        try:
            await self.get_schema(name, version)
            return True
        except Exception:
            return False

    async def get_latest_schema_version(self, name: str) -> Optional[SchemaDefAdapter]:
        """Get the latest version of a schema by name"""
        all_schemas = await self.get_all_schemas()
        matching_schemas = [schema for schema in all_schemas if schema.name == name]

        if not matching_schemas:
            return None

        # Find the schema with the highest version number
        return max(matching_schemas, key=lambda schema: schema.version or 0)

    async def get_schema_versions(self, name: str) -> List[int]:
        """Get all version numbers for a schema"""
        all_schemas = await self.get_all_schemas()
        versions = [
            schema.version
            for schema in all_schemas
            if schema.name == name and schema.version is not None
        ]
        return sorted(versions)

    async def get_schemas_by_name(self, name: str) -> List[SchemaDefAdapter]:
        """Get all versions of a schema by name"""
        all_schemas = await self.get_all_schemas()
        return [schema for schema in all_schemas if schema.name == name]

    async def get_schema_count(self) -> int:
        """Get the total number of schema definitions"""
        schemas = await self.get_all_schemas()
        return len(schemas)

    async def get_unique_schema_names(self) -> List[str]:
        """Get a list of unique schema names"""
        all_schemas = await self.get_all_schemas()
        names = set(schema.name for schema in all_schemas if schema.name)
        return sorted(names)

    async def bulk_save_schemas(
        self, schemas: List[dict], new_version: Optional[bool] = None
    ) -> None:
        """Save multiple schemas from dictionary definitions"""
        schema_defs = []
        for schema_dict in schemas:
            schema_def = SchemaDefAdapter(
                name=schema_dict.get("name"),
                version=schema_dict.get("version"),
                schema=schema_dict.get("schema"),
                description=schema_dict.get("description"),
            )
            schema_defs.append(schema_def)

        await self.save_schemas(schema_defs, new_version=new_version)

    async def clone_schema(
        self,
        source_name: str,
        source_version: int,
        target_name: str,
        target_version: int,
    ) -> None:
        """Clone an existing schema to a new name/version"""
        source_schema = await self.get_schema(source_name, source_version)

        cloned_schema = SchemaDefAdapter(
            name=target_name,
            version=target_version,
            schema=source_schema.schema,
            description=f"Clone of {source_schema.name} v{source_schema.version}",
        )

        await self.save_schema(cloned_schema)

    async def delete_all_schema_versions(self, name: str) -> None:
        """Delete all versions of a schema (alias for delete_schema_by_name)"""
        await self.delete_schema_by_name(name)

    async def search_schemas_by_name(self, name_pattern: str) -> List[SchemaDefAdapter]:
        """Search schemas by name pattern (case-insensitive)"""
        all_schemas = await self.get_all_schemas()
        return [
            schema
            for schema in all_schemas
            if name_pattern.lower() in (schema.name or "").lower()
        ]

    async def get_schemas_with_description(
        self, description_pattern: str
    ) -> List[SchemaDefAdapter]:
        """Find schemas that contain a specific text in their description"""
        all_schemas = await self.get_all_schemas()
        return [
            schema
            for schema in all_schemas
            if schema.description
            and description_pattern.lower() in schema.description.lower()
        ]

    async def validate_schema_structure(self, schema_definition: dict) -> bool:
        """Basic validation to check if schema definition has required structure"""
        # This is a basic validation - you might want to add more sophisticated JSON schema validation
        return isinstance(schema_definition, dict) and len(schema_definition) > 0

    async def get_schema_statistics(self) -> dict:
        """Get comprehensive statistics about schemas"""
        all_schemas = await self.get_all_schemas()

        unique_names = set()
        version_counts = {}

        for schema in all_schemas:
            if schema.name:
                unique_names.add(schema.name)
                version_counts[schema.name] = version_counts.get(schema.name, 0) + 1

        return {
            "total_schemas": len(all_schemas),
            "unique_schema_names": len(unique_names),
            "schemas_with_descriptions": len([s for s in all_schemas if s.description]),
            "version_counts": version_counts,
            "schema_names": sorted(unique_names),
        }

    # Legacy compatibility methods (aliasing new method names to match the original draft)
    async def list_schemas(self) -> List[SchemaDefAdapter]:
        """Legacy method: Get all schema definitions"""
        return await self.get_all_schemas()

    async def delete_schema(self, name: str, version: Optional[int] = None) -> None:
        """Legacy method: Delete a schema (by name only or by name and version)"""
        if version is not None:
            await self.delete_schema_by_name_and_version(name, version)
        else:
            await self.delete_schema_by_name(name)

    async def create_schema_version(
        self, name: str, schema_definition: dict, description: Optional[str] = None
    ) -> None:
        """Create a new version of an existing schema"""
        # Get the highest version number for this schema
        versions = await self.get_schema_versions(name)
        new_version = max(versions) + 1 if versions else 1

        await self.create_schema(name, new_version, schema_definition, description)
