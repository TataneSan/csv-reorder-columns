# csv-reorder-columns

Reorder the columns of a CSV file by name or index. Unlisted columns stay in
their original relative order, appended after (or prepended before) the
listed ones.

## Features

- `--order COL,...` accepts column names (with header) or 1-based indices
- `--rest append|prepend` controls where unlisted columns go (default: append)
- `--no-header` mode with index-only ordering
- Custom delimiter for input and output
- `--check` CI gate (exit 2 when the actual order differs), `--json` report
- No dependencies, Python >= 3.9

## Install

```bash
pip install git+https://github.com/TataneSan/csv-reorder-columns.git
```

Or from a local checkout:

```bash
git clone https://github.com/TataneSan/csv-reorder-columns.git
cd csv-reorder-columns
pip install .
```

## Usage

```
csv-reorder-columns [FILE] --order COL,...
                    [--rest append|prepend] [-d DELIM]
                    [--no-header] [--check] [--json] [--quiet]
```

### Examples

Bring `city` and `name` first by name:

```bash
printf 'name,age,city\nalice,30,paris\n' | csv-reorder-columns --order city,name
# city,name,age
# paris,alice,30
```

Same with 1-based indices:

```bash
csv-reorder-columns data.csv --order 3,1
```

Push unlisted columns to the front:

```bash
csv-reorder-columns data.csv --order name --rest prepend
```

Headerless file (indices only):

```bash
csv-reorder-columns --no-header --order 2,1 flat.csv
```

### CI check

```bash
csv-reorder-columns --order id,name,email --check users.csv
# exit 0: columns are already in that leading order
# exit 2: order differs
```

### JSON report

```bash
csv-reorder-columns --order city --json data.csv
# {
#   "changed": true,
#   "columns": 3,
#   "file": "data.csv",
#   "listed": 1,
#   "new_order": [
#     "city",
#     "name",
#     "age"
#   ]
# }
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | I/O or argument error (unknown/duplicate column, empty input, ...) |
| 2 | `--check` failed: column order differs |

## License

MIT
