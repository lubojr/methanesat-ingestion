## ADDED Requirements

### Requirement: Configurable Style JSON Link
The system SHALL support adding a configurable style JSON link to the `links` section of each generated STAC item.

#### Scenario: Adding style link
- **WHEN** a style URL is provided in the configuration
- **THEN** the system SHALL add a link with `rel: style` and `type: text/vector-styles` to the STAC item's `links` array
