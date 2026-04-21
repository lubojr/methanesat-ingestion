## ADDED Requirements

### Requirement: Skip Database Ingestion Toggle
The system SHALL provide an option to skip the database ingestion phase while still performing the file transfer from GCS to S3.

#### Scenario: Running in skip-ingestion mode
- **WHEN** the script is executed with `SKIP_INGESTION=true`
- **THEN** it SHOULD download files from GCS and upload to S3, but MUST NOT call the STAC/pypgstac ingestion functions.

### Requirement: Core Product Filtering
The system SHALL support filtering for the `core` product by identifying files in the `core/` folder that contain the string `COG_GEE`.

#### Scenario: Identifying valid Core files
- **WHEN** scanning the `core/` GCS directory structure
- **THEN** it SHALL only process files where the filename contains the string `COG_GEE`.

### Requirement: Divergence Integral Filtering
The system SHALL support filtering for the `divergence_integral` product by ensuring GeoJSON files contain a non-empty `features` array.

#### Scenario: Identifying valid Divergence Integral files
- **WHEN** scanning the `divergence_integral/` GCS directory structure for GeoJSON files
- **THEN** it SHALL only process files where the `features` collection is not empty.
