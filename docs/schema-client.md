# Schema client

`SchemaClient` manages versioned schema definitions through the Conductor schema
API. Obtain it from `OrkesClients` when the connected server exposes the schema
service, then save, fetch, list, or delete schemas.

**OSS/Orkes:** availability depends on the server deployment and permissions.
Validate schemas in a non-production environment before making them required by
workers. The generated request and model types are listed in [api-map](api-map.md).
