## ADDED Requirements

### Requirement: HTTPS Asset Href
The system SHALL use a public HTTPS URL as the primary `href` for STAC item assets (COG and GeoJSON).

#### Scenario: Generate HTTPS URL for asset
- **WHEN** an asset is uploaded to S3 at a path relative to the `/public/` folder
- **THEN** the system SHALL construct an HTTPS URL by appending the relative path to a configurable base prefix.

### Requirement: Configurable Public URL Prefix
The system SHALL allow the base HTTPS URL prefix to be configured via an environment variable.

#### Scenario: Set public URL prefix
- **WHEN** the `STAC_PUBLIC_URL_PREFIX` environment variable is provided
- **THEN** the system SHALL use its value to construct the primary asset `href`.
