## ADDED Requirements

### Requirement: Alternate S3 Link
The system SHALL add the original S3 URL as an alternate access point for each STAC asset.

#### Scenario: Add alternate S3 link
- **WHEN** a STAC asset is created
- **THEN** it SHALL include an `alternate` field with a `https` sub-field (following the project standard) containing the `s3://` URL, a description, and `alternate:name: "s3"`.

### Requirement: STAC Asset Metadata Standard
The system SHALL include `alternate:name: "https"` at the asset level to identify the primary link type.

#### Scenario: Standardized metadata
- **WHEN** an asset is generated with an HTTPS primary href
- **THEN** it SHALL include the property `alternate:name: "https"`.
