## ADDED Requirements

### Requirement: STAC Item Persistence
The system SHALL save each generated STAC item as a JSON file to the target S3 bucket.

#### Scenario: Save STAC item JSON
- **WHEN** a STAC item is successfully generated and its assets (COG/GeoJSON) are uploaded to S3
- **THEN** the system SHALL upload the STAC item's JSON representation to the same S3 prefix with a `.json` extension.

### Requirement: Persistent Pathing
The STAC JSON file SHALL be stored using the same path logic as the COG asset it represents.

#### Scenario: Consistent storage path
- **WHEN** a COG is stored at `s3://bucket/prefix/path/to/file.tif`
- **THEN** the corresponding STAC JSON MUST be stored at `s3://bucket/prefix/path/to/file.json`.
