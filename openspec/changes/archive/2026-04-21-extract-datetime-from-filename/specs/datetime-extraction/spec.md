## ADDED Requirements

### Requirement: Filename Datetime Parsing
The system SHALL extract the acquisition datetime from the GEE COG filename. The datetime is located after the version string and before the end timestamp.

#### Scenario: Parse datetime from valid filename
- **WHEN** provided with a filename like `MSAT_L4_COG_GEE_interim_c01460640_p5129_v00009003_20240911T220558Z_220620Z.tif`
- **THEN** the system SHALL extract `20240911T220558Z` as the acquisition datetime.

### Requirement: STAC Item Datetime Assignment
The system SHALL assign the extracted acquisition datetime to the STAC item's `datetime` property.

#### Scenario: Assign extracted datetime to STAC item
- **WHEN** a STAC item is created for a COG file
- **THEN** the `datetime` field MUST be set to the value extracted from the filename, converted to a valid Python datetime object.
