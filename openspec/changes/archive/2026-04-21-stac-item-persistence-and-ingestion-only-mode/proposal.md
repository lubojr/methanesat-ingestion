## Why

Currently, the ingestion script processes files from GEE, uploads them to AWS, and ingests them into STAC in a single coupled workflow. If we need to re-run ingestion or run it in a different environment (like a server with DB access but without GEE access), we have to repeat the entire transfer process. Saving STAC items to the target bucket allows for persistent metadata and decoupled ingestion, enabling a faster and more flexible "ingestion-only" mode.

## What Changes

- Save generated STAC item JSON files to the target S3 bucket alongside the COG and GeoJSON files.
- Implement an "ingestion-only" mode that reads existing STAC items from S3 and registers them in the database.
- Add configuration to toggle between "full transfer + ingestion" and "ingestion-only" modes.

## Capabilities

### New Capabilities
- `stac-persistence`: Saving STAC items as JSON files in the target S3 bucket.
- `ingestion-only-mode`: Capability to run ingestion by reading persistent STAC items from S3, bypassing GEE collection and transfer.

### Modified Capabilities
<!-- No existing capabilities modified. -->

## Impact

- **Storage**: Additional small JSON files stored in S3.
- **Workflow**: Ability to run ingestion on servers without GEE credentials or internet access to GEE buckets.
- **Performance**: Faster ingestion for already transferred data.
