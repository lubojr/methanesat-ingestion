## Why

Collect a specific subset of EO data from a Google Earth Engine bucket and move it to our AWS infrastructure. This data is required for our eoapi raster database to support downstream analysis. A one-off ingestion script is the most efficient way to handle this data transfer.

## What Changes

- Collect COG data from a Google Earth Engine bucket.
- Upload collected data to our AWS bucket.
- Ingest uploaded data to our eoapi raster database.
- Script is a one-off tool and will not be reused.

## Capabilities

### New Capabilities
- `gee-aws-ingestion`: Transfer EO data from GEE to AWS and ingest into eoapi.

### Modified Capabilities
<!-- No existing capabilities are being modified. -->

## Impact

- **Infrastructure**: New data stored in AWS.
- **Database**: New entries in the eoapi raster database.
