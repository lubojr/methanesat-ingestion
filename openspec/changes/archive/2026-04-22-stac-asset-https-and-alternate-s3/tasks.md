## 1. Configuration and Setup

- [x] 1.1 Add `STAC_PUBLIC_URL_PREFIX` to `.env.template`.
- [x] 1.2 Read the public URL prefix in the script.

## 2. Asset Mapping Logic

- [x] 2.1 Implement `map_s3_to_public_url` helper function to construct HTTPS `href` from S3 path.
- [x] 2.2 Implement a helper function to construct the `alternate` dictionary for STAC assets.

## 3. STAC Item Update

- [x] 3.1 Update `create_stac_item` to use HTTPS URLs as the primary `href` for both COG and GeoJSON assets.
- [x] 3.2 Add the `alternate` access dictionary and `alternate:name: "https"` metadata to all generated assets.

## 4. Verification

- [ ] 4.1 Run a dry run (`SKIP_INGESTION=true`) and verify the generated STAC item JSON matches the required structure.
