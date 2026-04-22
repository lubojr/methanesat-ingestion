## ADDED Requirements

### Requirement: Ingestion-Only Mode
The system SHALL support a mode where it only performs database ingestion by reading existing STAC items from S3.

#### Scenario: Run ingestion-only
- **WHEN** the script is executed with `INGESTION_ONLY=true`
- **THEN** it SHALL bypass GEE collection and GCS-to-S3 transfers, and instead list and read STAC JSON files from the configured S3 prefix.

### Requirement: STAC Item Ingestion from S3
In ingestion-only mode, the system SHALL read STAC item content directly from S3 objects.

#### Scenario: Process STAC items from S3
- **WHEN** scanning the target S3 bucket for `.json` files under the configured prefix
- **THEN** it SHALL parse each JSON as a STAC item and register it in the database using `pypgstac`.
