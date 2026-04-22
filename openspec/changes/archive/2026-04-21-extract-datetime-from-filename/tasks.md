## 1. Datetime Extraction Logic

- [x] 1.1 Implement a helper function to extract the acquisition timestamp from a filename using regex.
- [x] 1.2 Implement a conversion function to turn the timestamp string into a Python `datetime` object.

## 2. Integration with Ingestion Script

- [x] 2.1 Update `create_stac_item` to accept an optional `datetime` parameter.
- [x] 2.2 Update the `main` loop to extract and pass the datetime when processing files.

## 3. Verification

- [x] 3.1 Verify extraction with a sample filename in a test script or dry run.
- [x] 3.2 Run a dry run (`SKIP_INGESTION=true`) to ensure STAC items are correctly generated with the acquisition timestamp.
