## Context

The ingestion script processes COG files and creates STAC items. Currently, the acquisition datetime is not set or defaults to a generic value. The filename format `MSAT_L4_COG_GEE_interim_c01460640_p5129_v00009003_20240911T220558Z_220620Z.tif` contains the acquisition datetime (`20240911T220558Z`).

## Goals / Non-Goals

**Goals:**
- Extract the first timestamp from the filename suffix.
- Convert the extracted string to a Python `datetime` object.
- Pass this `datetime` object to the STAC item creation logic.

**Non-Goals:**
- Handling files with non-standard naming conventions (we assume the current MSAT L4 pattern).
- Modifying other STAC metadata fields not related to timing.

## Decisions

- **Regex for Extraction**: Use a regular expression to find the timestamp pattern `\d{8}T\d{6}Z`.
- **Datetime Parsing**: Use `datetime.strptime(ts, "%Y%m%dT%H%M%SZ")` for conversion, ensuring it is UTC.
- **Integration Point**: Modify `create_stac_item` to accept an optional `item_datetime` and update the `main` loop to parse it from the filename before calling the creation function.

## Risks / Trade-offs

- **[Risk] Filename format change** → Mitigation: Use a robust regex that targets the specific pattern rather than hardcoded string splits.
