## 1. Setup and Configuration

- [x] 1.1 Add `INGESTION_ONLY` environment variable to `.env.template`.
- [x] 1.2 Update the script to read the `INGESTION_ONLY` flag.

## 2. STAC Persistence (Full Mode)

- [x] 2.1 Implement logic to upload the STAC item JSON to S3 after generation.
- [x] 2.2 Ensure the JSON key matches the COG key with a `.json` extension.

## 3. Ingestion-Only Mode

- [x] 3.1 Implement S3 listing logic to find all STAC JSON files under the `AWS_S3_PREFIX`.
- [x] 3.2 Implement logic to read and parse STAC JSON files directly from S3.
- [x] 3.3 Update the `main` loop to branch into the ingestion-only path if the flag is set.
- [x] 3.4 Ensure the ingestion-only path bypasses GEE collection, downloading, and uploading.

## 4. Verification

- [x] 4.1 Run a full transfer with STAC persistence and verify JSON files are in S3.
- [x] 4.2 Run in ingestion-only mode and verify items are correctly registered in the STAC API/DB.
