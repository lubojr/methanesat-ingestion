## Why

We need to enrich our STAC items with additional assets (GeoJSON) and styling links to improve the metadata and visualization of the ingested data. This will provide a more comprehensive representation of the MethaneSAT data products.

## What Changes

- Add GeoJSON as an asset to the STAC item.
- Match GeoJSON to the corresponding COG item based on the acquisition date.
- Add a validation step to ensure matching is possible for the whole collection.
- Attach a configurable style JSON link to the STAC item.

## Capabilities

### New Capabilities
- `geojson-asset-matching`: Matching and attaching GeoJSON assets to STAC items based on acquisition date.
- `stac-style-links`: Attaching configurable style JSON links to STAC items to support visualization.

### Modified Capabilities
<!-- No requirement changes to existing capabilities. -->

## Impact

- **STAC Metadata**: STAC items will have additional assets and styling links.
- **Ingestion Script**: `gee_to_aws_ingestion.py` will require new matching and styling logic.
- **Configuration**: New environment variables for style URL.
