## Context

The ingestion script currently performs a linear workflow: fetch from GEE -> upload to S3 -> generate STAC -> ingest to DB. This design adds metadata persistence and a decoupled ingestion path.

## Goals / Non-Goals

**Goals:**
- Persist STAC metadata in S3 as JSON.
- Add an "ingestion-only" execution path.
- Avoid redundant GEE interactions and file transfers when metadata exists.

**Non-Goals:**
- Changing the STAC item structure.
- Automating the synchronization between S3 JSONs and the DB (this is a manual/triggered script mode).

## Decisions

- **S3 Upload for JSON**: Use `boto3` to upload the STAC item dictionary as a JSON string to S3. The key will be the same as the COG asset but with a `.json` extension.
- **`INGESTION_ONLY` Flag**: A new environment variable to trigger the decoupled path.
- **S3 Listing for Ingestion**: In ingestion-only mode, the script will use S3's `list_objects_v2` (or similar) under the `AWS_S3_PREFIX` to find all `.json` files.
- **JSON Loading**: Use `boto3`'s `get_object` to read JSON content into memory for `pypgstac` processing.

## Risks / Trade-offs

- **[Risk] Out-of-sync metadata** → If a COG is updated in GEE but the script is only run in ingestion-only mode, the DB might have stale info. Mitigation: Ensure full runs are used for updates.
- **[Trade-off] S3 API Costs** → Listing thousands of JSON files in S3 has a small cost, but it's significantly cheaper and faster than re-downloading/uploading COGs.
