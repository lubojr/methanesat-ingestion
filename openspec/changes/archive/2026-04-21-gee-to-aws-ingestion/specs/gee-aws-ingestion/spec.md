## ADDED Requirements

### Requirement: Data Collection from GEE
The system SHALL collect a subset of Cloud Optimized GeoTIFF (COG) data from a Google Earth Engine bucket.

#### Scenario: Successful data collection
- **WHEN** the script is executed with valid GEE credentials and bucket information
- **THEN** it identifies and retrieves the specified subset of COG files

### Requirement: Data Upload to AWS
The system SHALL upload the collected COG data to a designated AWS S3 bucket.

#### Scenario: Successful data upload
- **WHEN** the collection is complete and AWS credentials are valid
- **THEN** all collected COG files are stored in the target AWS S3 bucket

### Requirement: Ingestion to eoapi
The system SHALL register and ingest the uploaded COG data into the eoapi raster database.

#### Scenario: Successful eoapi ingestion
- **WHEN** data is available in the AWS S3 bucket
- **THEN** the script creates the necessary entries in the eoapi raster database to make the data accessible
