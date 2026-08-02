# csv-reorder-columns

Rewrite a CSV with its columns in a chosen order. Columns not listed are
appended at the end (or dropped with `--drop-rest`). A `--check` mode turns
the tool into a CI gate verifying the current column order.

## Features

- Desired order as a comma-separated list
- Unlisted columns kept at the end by default, `--drop-rest` to remove them
- `--check` exit 2 when the current order differs
- Custom `--delimiter`, `--json` report
- Zero dependencies, Python >= 3.9

## Install

```bash
pip install .
# or
pip install git+https://github.com/TataneSan/csv-reorder-columns.git
```

## Usage

```bash
csv-reorder-columns id,name,email users.csv
printf 'b,a\n2,1\n' | csv-reorder-columns a,b -
csv-reorder-columns id,name users.csv --drop-rest
csv-reorder-columns id,name users.csv --check
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | ok |
| 1 | I/O or CLI error |
| 2 | unknown column, or check mode detected a different order |

## License

MIT
