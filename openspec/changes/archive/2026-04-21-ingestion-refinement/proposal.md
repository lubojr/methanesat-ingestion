## Why

The ingestion script needs more granular control over which files are processed and the ability to run in a "dry run" or local-only mode to verify cloud-to-cloud transfers without triggering database ingestion. This allows for safer testing and specific data targeting from the Google Cloud public datasets.

## What Changes

- Add an optional ingestion toggle to allow running transfers without STAC/database registration.
- Implement folder-specific and string-based filtering for GEE files (focusing on `core/` and `divergence_integral/`).
- Add specific logic for `core` results targeting files containing `COG_GEE`.
- Add specific logic for `divergence_integral` geojson files, ensuring they are only processed if they contain non-empty feature collections.

## Capabilities

### New Capabilities
- `ingestion-control`: Ability to toggle database ingestion and filter files by product type and content.

### Modified Capabilities
<!-- No existing capabilities are being modified as they were archived or haven't been promoted to main specs yet. -->

## Impact

- **Script Logic**: `gee_to_aws_ingestion.py` will require new configuration flags and filtering logic.
- **Workflow**: Local testing becomes possible without database access.
