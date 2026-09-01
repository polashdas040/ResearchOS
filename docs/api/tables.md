# Table Intelligence

Scientific tables are stored as reusable structured artifacts derived from parsed document elements.

## Stored Data

- `tables`: document linkage, source element, page, section, caption, and semantic summary.
- `table_columns`: ordered column labels.
- `table_rows`: ordered data rows.
- `table_cells`: raw value, normalized value, numeric value, and cell kind.

Applications should answer numeric table questions from this structure, not from generated prose.
