## Why

Currently, STAC item assets use S3 URLs as their primary `href`. To improve compatibility with web-based clients and follow project standards, we need to switch the primary `href` to a public HTTPS URL while retaining the S3 URL as an `alternate` access point. This ensures that assets are easily accessible via browser while still allowing direct S3 access for optimized workflows.

## What Changes

- Update STAC asset `href` to use a configurable HTTPS URL prefix.
- The HTTPS URL mapping must be relative to the `/public/` folder on the bucket.
- Add an `alternate` field to each asset containing the original S3 URL.
- Implement the specific STAC asset metadata structure required (e.g., `alternate:name`).

## Capabilities

### New Capabilities
- `stac-asset-https-mapping`: Logic to transform S3 paths into public HTTPS URLs based on configuration.
- `stac-alternate-assets`: Support for adding multiple access points (S3 and HTTPS) to a single STAC asset.

### Modified Capabilities
<!-- No requirement changes to existing capabilities. -->

## Impact

- **STAC Items**: Assets will have different primary `href` values and a more complex `alternate` structure.
- **Ingestion Script**: `gee_to_aws_ingestion.py` will require updates to the asset generation logic.
- **Configuration**: New environment variable for the HTTPS public URL prefix.
