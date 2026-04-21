## 1. Configuration and Setup

- [x] 1.1 Add `SKIP_INGESTION` environment variable support to `gee_to_aws_ingestion.py`.
- [x] 1.2 Update `.env.template` to include the `SKIP_INGESTION` toggle and clarify product folder structures.

## 2. Granular Filtering

- [x] 2.1 Refactor `list_gee_files` to support multiple product folders (`core/`, `divergence_integral/`).
- [x] 2.2 Implement `core` filtering logic to only keep files containing `COG_GEE`.
- [x] 2.3 Implement `divergence_integral` GeoJSON filtering to check for non-empty feature collections.

## 3. Ingestion Toggle

- [x] 3.1 Wrap `ingest_collection` and `ingest_items` calls in a conditional check for `SKIP_INGESTION`.
- [x] 3.2 Add comprehensive logging for skipped phases when in "dry run" mode.
- [x] 3.3 Add `AWS_S3_PREFIX` support for uploaded files.

## 4. Verification

- [x] 4.1 Run a local test with `SKIP_INGESTION=true` and a `LIMIT=1` for both `core` and `divergence_integral`.
- [x] 4.2 Verify that cloud transfer works correctly while database calls are bypassed.
