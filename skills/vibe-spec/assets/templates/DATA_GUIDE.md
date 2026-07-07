# Data Guide

Use this file to keep data storage, privacy, fixtures, and experiment inputs reproducible.

## Data Locations

| Path | Kind | Source | Used By | Commit? | Notes |
|---|---|---|---|---|---|
| TBD | raw / derived / fixture / export | TBD | TBD | yes/no | TBD |

## Data Rules

- Keep raw data separate from derived data.
- Do not commit secrets, credentials, private user data, or large generated artifacts unless explicitly approved.
- Record source, generation command, timestamp, and schema for derived datasets.
- Prefer small deterministic fixtures for tests.
- Document cleanup and retention rules for generated data.

## Schemas

| Dataset/File | Schema/Fields | Validation | Notes |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

## Privacy And Sensitivity

- Sensitive data classes: TBD
- Redaction/anonymization rules: TBD
- Storage restrictions: TBD

## Reproducibility

For any dataset used in experiments or tests, record:

- Source path or URL.
- Version, hash, or timestamp.
- Transformation script or command.
- Expected output location.
