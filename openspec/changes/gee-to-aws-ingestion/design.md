## Context

We have been granted access to a Google Earth Engine (GEE) bucket containing Earth Observation (EO) data. We need to transfer a specific subset of this data to our AWS infrastructure and ingest it into our existing eoapi raster database. The process is a one-off task.

## Goals / Non-Goals

**Goals:**
- Provide a reliable one-off Python script for data transfer.
- Ensure data is correctly stored in AWS S3 as Cloud Optimized GeoTIFFs (COGs).
- Successfully register the data in the eoapi raster database.

**Non-Goals:**
- Creating a reusable or automated pipeline.
- Handling real-time data updates.
- Implementing a full-scale ingestion service.

## Decisions

- **Python Language**: Use Python for the script due to its excellent library support for GCS (`google-cloud-storage`), AWS (`boto3`), and database interaction.
- **Direct Transfer**: Download data from GCS to local/ephemeral storage and then upload to S3, as this is the simplest approach for a one-off script.
- **eoapi Ingestion**: Use standard eoapi ingestion methods (e.g., `pystac` for STAC item generation if needed, or direct database inserts depending on the eoapi setup) to register the S3 objects.
- **Environment Variables**: Use environment variables for all credentials and bucket names to keep the script secure and configurable without hardcoding.

## Risks / Trade-offs

- **[Risk] Data Volume** → Mitigation: Implement basic error handling and logging to track progress and allow for manual resume if the script fails midway.
- **[Risk] Network Latency** → Mitigation: Transfer data in small batches or use multi-threading if necessary to speed up the process.
- **[Trade-off] One-off vs. Reusable** → We chose a simple one-off script to minimize development time, accepting that it may need modification if a similar task arises in the future.
