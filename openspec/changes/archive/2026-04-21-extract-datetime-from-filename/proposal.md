## Why

The ingestion script currently does not extract the acquisition time from the filename, which is necessary for accurate STAC metadata. Extracting this information from the filename ensures that the STAC items have the correct temporal information without requiring external lookups.

## What Changes

- Add logic to parse the acquisition datetime from the COG filename.
- Update the STAC item creation process to use this extracted datetime.

## Capabilities

### New Capabilities
- `datetime-extraction`: Extracting acquisition timestamp from GEE filenames to populate STAC item `datetime` field.

### Modified Capabilities
<!-- None -->

## Impact

- **Script Logic**: `gee_to_aws_ingestion.py` will need a new parsing function.
- **STAC Metadata**: STAC items will have more accurate timestamps.
