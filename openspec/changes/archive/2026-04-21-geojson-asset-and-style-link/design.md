## Context

The current ingestion script processes COG and GeoJSON files independently. We need to match GeoJSON files to their corresponding COG items based on the acquisition date extracted from the filename and add styling information via a configurable link. GeoJSON assets are optional; if no match is found, the COG is still ingested.

## Goals / Non-Goals

**Goals:**
- Match GeoJSON files to COGs by date.
- Treat GeoJSON as an optional asset (ingest COG regardless of GeoJSON presence).
- Add GeoJSON as an asset to the STAC item if a match is found.
- Add a configurable style link to the STAC item.

**Non-Goals:**
- Skipping COGs if GeoJSON is missing.
- Modifying the GEE path structure.

## Decisions

- **Grouping Logic**: List all files and group them by acquisition date.
- **Optional Asset Matching**: For each COG found, check for a matching GeoJSON in the same date group. If found, include it; if not, proceed with COG only.
- **Asset Attachment**: Modify `create_stac_item` to accept an optional GeoJSON S3 URL.
- **Styling Links**: Use an environment variable `STAC_STYLE_URL` to generate the style link, automatically mapping it to the `vector` asset key.

## Risks / Trade-offs

- **[Trade-off] Metadata Consistency** → Ingesting COGs without GeoJSONs might lead to inconsistent item structure across the collection, but fulfills the requirement to not block data availability.
