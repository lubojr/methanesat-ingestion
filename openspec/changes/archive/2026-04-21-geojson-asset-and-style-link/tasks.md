## 1. Setup and Configuration

- [x] 1.1 Add `STAC_STYLE_URL` and `STAC_STYLE_ASSET_KEYS` to `.env.template`.

## 2. File Grouping and Matching

- [x] 2.1 Implement logic to list all files and group them by acquisition date.
- [x] 2.2 Implement optional matching logic: link GeoJSON to COG if present, otherwise proceed with COG only.

## 3. STAC Item Enhancement

- [x] 3.1 Update `create_stac_item` to accept an optional GeoJSON S3 URL and attach it as an asset if provided.
- [x] 3.2 Update `create_stac_item` to add style links based on configuration.

## 4. Main Loop Integration

- [x] 4.1 Update the `main` loop to iterate over grouped items, ensuring COGs are processed even without GeoJSON.
- [x] 4.2 Handle the conditional processing (download, upload) for the optional GeoJSON asset.

## 5. Verification

- [x] 5.1 Run a dry run (`SKIP_INGESTION=true`) with a mix of COG+GeoJSON and COG-only data to verify correct behavior.
