## Context

The existing ingestion script transfers COG data from Google Cloud Storage (GCS) to AWS S3 and registers it in a STAC API via `pypgstac`. We need to refine the filtering logic to target specific MethaneSAT products (`core` and `divergence_integral`) and add a mechanism for local-only testing without database access.

## Goals / Non-Goals

**Goals:**
- Implement granular filtering for `core/` (dispersed emissions) and `divergence_integral/` (point sources).
- Add a `SKIP_INGESTION` toggle for local transfer verification.
- Support GeoJSON content-based filtering for `divergence_integral`.

**Non-Goals:**
- Changing the underlying transfer mechanism (GCS to S3).
- Modifying the STAC API schema.

## Decisions

- **GCS Path Filtering**: Use folder-based prefixes (`core/`, `divergence_integral/`) to narrow GCS listing operations.
- **In-Memory Filtering**: Filter file lists by string (e.g., `COG_GEE` for `core`) after listing but before downloading.
- **GeoJSON Peek**: Download GeoJSON files, parse them locally, and check the `features` length. If empty, discard and skip upload. This is necessary because GCS metadata doesn't reflect the content's "emptiness."
- **Configuration Toggle**: Add a `SKIP_INGESTION` environment variable (default: `False`). If `True`, the `ingest_collection` and `ingest_items` calls are bypassed.

## Risks / Trade-offs

- **[Risk] GeoJSON Download Cost** → Mitigation: GeoJSON files are typically small compared to COGs. We still download them to verify content, but we only upload to S3 if they have data.
- **[Trade-off] String Filtering** → Using `COG_GEE` as a filter for `core` results is specific to current GCS naming conventions but is sufficient for a one-off/specialized ingestion script.
