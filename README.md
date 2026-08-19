# GEE to AWS Ingestion Script

This repository contains a Python-based ingestion pipeline designed to migrate Cloud Optimized GeoTIFF (COG) and GeoJSON data from Google Earth Engine (GCS buckets) of MethaneSAT Level 4 data products to AWS S3, generate STAC (SpatioTemporal Asset Catalog) metadata, and ingest it into a `pgSTAC` database.

## Prerequisites

### Google Cloud Authentication
To access the MethaneSAT data in GCS, you need to set up **Application Default Credentials (ADC)**. This script looks for a credentials file (typically `adc.json`) to authenticate with Google Cloud.

1.  **Install the Google Cloud CLI**: Follow the [official instructions](https://cloud.google.com/sdk/docs/install).
2.  **Generate the credentials file**:
    Run the following command in your terminal:
    ```bash
    gcloud auth application-default login
    ```
    This will open a browser for authentication and save a JSON file (usually at `~/.config/gcloud/application_default_credentials.json` on Linux/macOS or `%APPDATA%\gcloud\application_default_credentials.json` on Windows). The script will automatically detect this file.

### Data Access
The MethaneSAT Level 4 data is hosted on Google Cloud Storage at the following location:
- **Bucket**: `msat-prod-data-public-methanesat-level4`
- **Console Link**: [msat-prod-data-public-methanesat-level4](https://console.cloud.google.com/storage/browser/msat-prod-data-public-methanesat-level4)

## Features

- **Automated Data Migration**: Scans GCS buckets for COGs and GeoJSONs and uploads them to AWS S3.
- **Processing Version Management**: Intelligently groups files by location and timestamp, ensuring only the latest processing version (`p-version`) of a scene is ingested.
- **STAC Metadata Generation**: Automatically creates STAC Items using `rio-stac`, including raster and projection extensions.
- **Coordinate Transformation**: Converts COGs to `EPSG:4326` during the pipeline to ensure consistency in the STAC catalog.
- **Data Enrichment**:
    - Merges properties from existing remote STAC APIs.
    - Extracts specific properties (flux, time coverage) from GeoJSON assets into STAC Item properties.
    - Supports custom STAC style links for both raster and vector assets.
- **Titiler Integration**: Automatically generates thumbnail assets using a configured Titiler endpoint.
- **Flexible Ingestion Modes**:
    - Full Pipeline: Download, Transform, Upload, and Ingest.
    - Skip Ingestion: Perform file migration without updating the database (dry run/migration only).
    - Ingestion Only: Re-ingest existing STAC JSON files already stored on S3.
- **Data Validation**: Validates GeoJSON features before processing to avoid ingesting empty datasets.

## Workflow

1. **Scan**: List blobs in the source GCS bucket.
2. **Filter & Group**: Identify the highest `p-version` for each scene (Location ID + Timestamp).
3. **Download**: Pull files from GCS to a local temporary directory.
4. **Transform**: Reproject COG files to `EPSG:4326`.
5. **Upload**: Push reprojected COGs and GeoJSONs to the target AWS S3 bucket.
6. **STAC Creation**: 
    - Generate a STAC Item.
    - Map S3 URLs to public HTTPS URLs.
    - Add thumbnails and style links.
    - Merge metadata from remote STAC providers if configured.
7. **Persist**: Upload the generated STAC Item JSON back to S3.
8. **Ingest**: (Optional) Register the collection and items into a `pgSTAC` database.

## Configuration

The script is configured via environment variables. Create a `.env` file based on the provided `.env.template`.

### Google Cloud Settings
- `GEE_PROJECT`: Google Cloud Project ID.
- `GEE_BUCKET`: Source GCS bucket name.
- `GEE_PREFIX`: Comma-separated list of prefixes to scan in GCS.

### AWS Settings
- `AWS_ACCESS_KEY_ID`: AWS Access Key.
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Key.
- `AWS_REGION`: AWS Region (e.g., `eu-central-1`).
- `AWS_S3_BUCKET`: Target S3 bucket name.
- `AWS_S3_PREFIX`: Prefix for uploaded files on S3.

### STAC & Database Settings
- `STAC_COLLECTION_ID`: ID for the STAC collection.
- `STAC_COLLECTION_TITLE`: Title for the STAC collection.
- `STAC_COLLECTION_DESCRIPTION`: Description for the STAC collection.
- `STAC_PUBLIC_URL_PREFIX`: HTTPS prefix to map S3 URLs to public endpoints.
- `STAC_REMOTE_ENDPOINT`: (Optional) Remote STAC API to fetch additional metadata.
- `TITILER_PUBLIC_URL`: URL to a Titiler instance for thumbnail generation.
- `PGSTAC_CONNECTION`: standard Postgres connection string for `pgSTAC`.

### Operational Toggles
- `SKIP_INGESTION`: Set to `true` to skip database ingestion (STAC JSONs are still created on S3).
- `INGESTION_ONLY`: Set to `true` to only ingest existing STAC JSONs from S3.
- `DO_CLEANUP`: Set to `true` to delete local files after processing.
- `LIMIT`: (Optional) Limit the number of scenes processed in one run.
- `COG_FILTER_ALLOW`: String to filter COG filenames (defaults to `COG_GEE`).
- `COG_FILTER_DENY`: String to exclude COG filenames (defaults to `COG_PORTAL`).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Install dependencies**:
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

## Usage

Run the ingestion script:
```bash
python gee_to_aws_ingestion.py
```

### Logging
Logs are written to `ingest_logs.log` in the current directory, providing detailed information about scanned files, processing steps, and any errors encountered.

## Design Documents
Initial design specifications and change records can be found in the `@openspec/` folder, covering:
- Datetime extraction logic
- GEE to AWS ingestion requirements
- STAC item persistence and ingestion-only mode
- GeoJSON asset matching and styling

## License
MIT
