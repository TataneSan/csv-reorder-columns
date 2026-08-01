# csv-reorder-columns

Reorder the columns of a CSV document by header name or 1-based index. Columns
not listed are kept (appended or prepended) or dropped. Works on files or
stdin, and doubles as a CI gate with `--check`.

## Features

- Select columns by header **name** or **1-based index**, in any mix
- Control unlisted columns: `--rest append|prepend|drop`
- Custom delimiter and quote character
- `--no-header` mode for headerless files (index selectors)
- `--check` mode for CI: exit code 2 if the input order would change
- `--json` report with the resolved order and dropped columns
- Pure Python standard library, no dependencies

## Install

```bash
pip install .
```

Or run directly from the source tree:

```bash
python -m csv_reorder_columns.cli --help
```

## Usage

```
csv-reorder-columns [FILE] --order col2,col1 [--rest append|prepend|drop]
                    [-d DELIM] [-q QUOTE] [--no-header]
                    [--check] [--json] [--quiet]
```

`FILE` defaults to stdin (`-` also means stdin).

## Examples

Move `email` and `name` to the front, keep the rest:

```bash
csv-reorder-columns users.csv --order email,name
# email,name,id,age,country
```

Same with indices (1-based):

```bash
csv-reorder-columns users.csv --order 3,1
```

Select only some columns, drop the others:

```bash
csv-reorder-columns users.csv --order name,email --rest drop
```

Put listed columns at the end:

```bash
csv-reorder-columns users.csv --order updated_at --rest prepend
```

Semicolon-delimited input, from stdin:

```bash
cat data.csv | csv-reorder-columns - -d ';' --order total,qty
```

Headerless CSV (selectors are indices):

```bash
csv-reorder-columns raw.csv --no-header --order 2,1
```

CI gate — fail if `schema.csv` is not in the expected order:

```bash
csv-reorder-columns schema.csv --order id,name,email --check
echo $?   # 0 = already ordered, 2 = would change
```

JSON report:

```bash
csv-reorder-columns users.csv --order email,name --rest drop --json
```

```json
{
  "file": "users.csv",
  "rows": 101,
  "columns_in": 5,
  "columns_out": 2,
  "new_order": ["email", "name"],
  "dropped": ["id", "age", "country"],
  "changed": true
}
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | success (or `--check`: input already in the requested order) |
| 1    | I/O or argument error (unknown/ambiguous/duplicate column, ...) |
| 2    | `--check`: the input column order would change |

## Development

```bash
python -m pytest tests/
```

## License

MIT — see [LICENSE](LICENSE).
