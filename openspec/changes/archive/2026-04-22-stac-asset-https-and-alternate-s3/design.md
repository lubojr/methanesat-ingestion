## Context

The current ingestion script uses S3 URLs (e.g., `s3://bucket/prefix/path.tif`) as the primary `href` for assets. We need to map these to public HTTPS URLs (e.g., `https://domain.at/api/public/share/id/path.tif`) while keeping the S3 URL as an alternate.

## Goals / Non-Goals

**Goals:**
- Implement a configurable mapping logic for HTTPS URLs.
- Construct the `alternate` STAC field for each asset.
- Update both COG and GeoJSON asset generation.

**Non-Goals:**
- Changing the S3 upload destination.
- Automating the generation of the public share ID (this is assumed to be part of the configurable prefix).

## Decisions

- **URL Construction**: The script will take the path relative to the bucket's root (or a specific prefix like `public/`) and append it to the `STAC_PUBLIC_URL_PREFIX`.
- **`alternate` Field Structure**: Follow the provided example exactly:
  ```json
  "alternate": {
    "https": {
      "href": "s3://...",
      "description": "Access through s3.",
      "alternate:name": "s3"
    }
  },
  "alternate:name": "https"
  ```
- **Helper Function**: Create a `map_s3_to_public_url` function to handle the string manipulation and ensure consistent URL formation.

## Risks / Trade-offs

- **[Risk] Path Mismatch** → If the `STAC_PUBLIC_URL_PREFIX` or the relative path logic is incorrect, the generated HTTPS links will be broken. Mitigation: Log example URLs during the first few items of a run.
