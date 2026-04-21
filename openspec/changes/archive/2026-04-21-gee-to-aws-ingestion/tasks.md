## 1. Setup and Preparation

- [x] 1.1 Create the Python script file `gee_to_aws_ingestion.py`.
- [x] 1.2 Initialize a virtual environment and install dependencies (`google-cloud-storage`, `boto3`, `python-dotenv`).
- [x] 1.3 Create a `.env` template file for credentials (GEE_PROJECT, GEE_BUCKET, AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_S3_BUCKET).

## 2. GEE Data Collection

- [x] 2.1 Implement GCS client initialization and authentication.
- [x] 2.2 Add logic to list and filter the specific subset of COG files in the GEE bucket.
- [x] 2.3 Implement the download function to retrieve files from GCS to local storage.

## 3. AWS Data Upload

- [x] 3.1 Implement S3 client initialization and authentication.
- [x] 3.2 Add logic to upload the downloaded COG files to the target S3 bucket.
- [x] 3.3 Ensure uploaded objects have correct permissions/metadata (if required).

## 4. STAC API Ingestion

- [x] 4.1 Install and configure `pypgstac` and `rio-stac`.
- [x] 4.2 Implement STAC Collection creation.
- [x] 4.3 Implement STAC Item generation using `rio-stac`.
- [x] 4.4 Implement Item ingestion using `pypgstac`.

## 5. Cleanup and Polishing

- [x] 5.1 Add error handling and logging throughout the script.
- [x] 5.2 Test the script with a small subset of data.
- [x] 5.3 Verify all files are in S3.
