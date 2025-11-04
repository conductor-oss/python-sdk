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
        super().__init__(configuration, api_client)

    # Core Schema Operations
    @deprecated("save_schemas is deprecated; use register_schema instead")
    @typing_deprecated("save_schemas is deprecated; use register_schema instead")
    async def save_schemas(
        self, schema_defs: List[SchemaDefAdapter], new_version: Optional[bool] = None
    ) -> None:
        """Save one or more schema definitions"""
        await self._schema_api.save(schema_defs, new_version=new_version)

    async def register_schemas(
        self, schema_defs: List[SchemaDefAdapter], new_version: Optional[bool] = None, **kwargs
    ) -> None:
        """Register a schema definition"""
        await self._schema_api.save(schema_def=schema_defs, new_version=new_version, **kwargs)

    @deprecated("save_schema is deprecated; use register_schema instead")
    @typing_deprecated("save_schema is deprecated; use register_schema instead")
    async def save_schema(
        self, schema_def: SchemaDefAdapter, new_version: Optional[bool] = None
    ) -> None:
        """Save a single schema definition"""
        await self.save_schemas([schema_def], new_version=new_version)

    async def register_schema(
        self, schema_def: SchemaDefAdapter, new_version: Optional[bool] = None, **kwargs
    ) -> None:
        """Register a schema definition"""
        await self.register_schemas(schema_defs=[schema_def], new_version=new_version, **kwargs)

    async def get_schema(self, name: str, version: int, **kwargs) -> SchemaDefAdapter:
        """Get a specific schema by name and version"""
        return await self._schema_api.get_schema_by_name_and_version(
            name=name, version=version, **kwargs
        )

    async def get_all_schemas(self, **kwargs) -> List[SchemaDefAdapter]:
        """Get all schema definitions"""
        return await self._schema_api.get_all_schemas(**kwargs)

    async def delete_schema_by_name(self, name: str, **kwargs) -> None:
        """Delete all versions of a schema by name"""
        await self._schema_api.delete_schema_by_name(name=name, **kwargs)

    async def delete_schema_by_name_and_version(self, name: str, version: int, **kwargs) -> None:
        """Delete a specific version of a schema"""
        await self._schema_api.delete_schema_by_name_and_version(
            name=name, version=version, **kwargs
        )

    # Convenience Methods
    async def create_schema(
        self, name: str, version: int, schema_definition: dict, schema_type: str = "JSON", **kwargs
    ) -> None:
        """Create a new schema with simplified parameters"""
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
        """Update an existing schema"""
        schema_def = SchemaDefAdapter(
            name=name,
            version=version,
            data=schema_definition,
            type=schema_type,
        )
        await self.register_schema(schema_def=schema_def, new_version=create_new_version, **kwargs)

    async def schema_exists(self, name: str, version: int, **kwargs) -> bool:
        """Check if a specific schema version exists"""
        try:
            await self.get_schema(name=name, version=version, **kwargs)
            return True
        except Exception:
            return False

    async def get_latest_schema_version(self, name: str, **kwargs) -> Optional[SchemaDefAdapter]:
        """Get the latest version of a schema by name"""
        all_schemas = await self.get_all_schemas(**kwargs)
        matching_schemas = [schema for schema in all_schemas if schema.name == name]

        if not matching_schemas:
            return None

        # Find the schema with the highest version number
        return max(matching_schemas, key=lambda schema: schema.version or 0)

    async def get_schema_versions(self, name: str, **kwargs) -> List[int]:
        """Get all version numbers for a schema"""
        all_schemas = await self.get_all_schemas(**kwargs)
        versions = [
            schema.version
            for schema in all_schemas
            if schema.name == name and schema.version is not None
        ]
        return sorted(versions)

    async def get_schemas_by_name(self, name: str, **kwargs) -> List[SchemaDefAdapter]:
        """Get all versions of a schema by name"""
        all_schemas = await self.get_all_schemas(**kwargs)
        return [schema for schema in all_schemas if schema.name == name]

    async def get_schema_count(self, **kwargs) -> int:
        """Get the total number of schema definitions"""
        schemas = await self.get_all_schemas(**kwargs)
        return len(schemas)

    async def get_unique_schema_names(self, **kwargs) -> List[str]:
        """Get a list of unique schema names"""
        all_schemas = await self.get_all_schemas(**kwargs)
        names = {schema.name for schema in all_schemas if schema.name}
        return sorted(names)

    async def bulk_save_schemas(
        self, schemas: List[dict], new_version: Optional[bool] = None, **kwargs
    ) -> None:
        """Save multiple schemas from dictionary definitions"""
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
        """Clone an existing schema to a new name/version"""
        source_schema = await self.get_schema(name=source_name, version=source_version, **kwargs)

        cloned_schema = SchemaDefAdapter(
            name=target_name,
            version=target_version,
            data=source_schema.data,
            type=source_schema.type,
        )

        await self.register_schema(schema_def=cloned_schema, **kwargs)

    async def delete_all_schema_versions(self, name: str, **kwargs) -> None:
        """Delete all versions of a schema (alias for delete_schema_by_name)"""
        await self.delete_schema_by_name(name=name, **kwargs)

    async def search_schemas_by_name(self, name_pattern: str, **kwargs) -> List[SchemaDefAdapter]:
        """Search schemas by name pattern (case-insensitive)"""
        all_schemas = await self.get_all_schemas(**kwargs)
        return [
            schema for schema in all_schemas if name_pattern.lower() in (schema.name or "").lower()
        ]

    async def get_schemas_with_external_ref(
        self, external_ref_pattern: str, **kwargs
    ) -> List[SchemaDefAdapter]:
        """Find schemas that contain a specific text in their external ref"""
        all_schemas = await self.get_all_schemas(**kwargs)
        return [
            schema
            for schema in all_schemas
            if schema.external_ref and external_ref_pattern.lower() in schema.external_ref.lower()
        ]

    async def validate_schema_structure(self, schema_definition: dict, **kwargs) -> bool:
        """Basic validation to check if schema definition has required structure"""
        # This is a basic validation - you might want to add more sophisticated JSON schema validation
        return isinstance(schema_definition, dict) and len(schema_definition) > 0

    async def get_schema_statistics(self, **kwargs) -> dict:
        """Get comprehensive statistics about schemas"""
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
        """Legacy method: Get all schema definitions"""
        return await self.get_all_schemas(**kwargs)

    async def delete_schema(self, name: str, version: Optional[int] = None, **kwargs) -> None:
        """Legacy method: Delete a schema (by name only or by name and version)"""
        if version is not None:
            await self.delete_schema_by_name_and_version(name=name, version=version, **kwargs)
        else:
            await self.delete_schema_by_name(name=name, **kwargs)

    async def create_schema_version(
        self, name: str, schema_definition: dict, schema_type: str = "JSON", **kwargs
    ) -> None:
        """Create a new version of an existing schema"""
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
