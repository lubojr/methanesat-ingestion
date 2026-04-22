## ADDED Requirements

### Requirement: GeoJSON to COG Matching
The system SHALL match GeoJSON files to the corresponding COG items based on their acquisition date extracted from the filename.

#### Scenario: Successful matching
- **WHEN** a COG file and its corresponding GeoJSON file share the same acquisition date
- **THEN** the system SHALL link them within the same STAC item

### Requirement: Optional GeoJSON Asset
The system SHALL treat the GeoJSON as an optional asset. If a corresponding GeoJSON is not found for a COG, the COG SHALL still be ingested.

#### Scenario: Missing GeoJSON
- **WHEN** a COG file is missing its corresponding GeoJSON file
- **THEN** the system SHALL log a warning and proceed with the ingestion of the COG item without the GeoJSON asset
