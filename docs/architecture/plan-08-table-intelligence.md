# PLAN 08 Table Intelligence

PLAN 08 adds structured scientific table extraction and querying.

## Design

- `ScientificTableExtractor` converts document `TABLE` elements into structured tables.
- Tables preserve caption linkage, page, section, columns, rows, cells, missing values, and numeric values.
- `tables`, `table_columns`, `table_rows`, and `table_cells` store queryable table structure in PostgreSQL.
- `TableQuestionAnswerer` answers simple numeric questions from cell structure instead of prose.

## Current Limits

The initial extractor handles pipe-delimited table text emitted by the deterministic PLAN 07 parser. Multi-row headers and merged cells will get richer parser support in later table/parser iterations, but the storage model is already normalized for those extensions.
