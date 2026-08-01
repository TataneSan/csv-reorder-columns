"""csv-reorder-columns: reorder the columns of a CSV file.

The --order list (comma-separated) takes column names (with a header) or
1-based indices. Columns not listed stay in their original relative order,
appended after the listed ones (or prepended with --rest first).

Exit codes:
  0  success
  1  I/O or argument error (unknown column, duplicate, ...)
  2  check mode: the current column order differs from the requested order
"""

import argparse
import csv
import io
import json
import sys

from . import __version__


def resolve_indices(order_specs, header):
    """Map --order specs to 0-based indices into `header`.

    A spec is a column name or a 1-based index. Returns (indices, rest) where
    rest is the list of unlisted indices in original order.
    """
    picked = []
    seen = set()
    for spec in order_specs:
        spec = spec.strip()
        if not spec:
            continue
        idx = None
        if spec.isdigit():
            n = int(spec)
            if 1 <= n <= len(header):
                idx = n - 1
        else:
            if spec in header:
                idx = header.index(spec)
        if idx is None:
            raise ValueError(f"unknown column: {spec!r}")
        if idx in seen:
            raise ValueError(f"column listed twice: {spec!r}")
        seen.add(idx)
        picked.append(idx)
    rest = [i for i in range(len(header)) if i not in seen]
    return picked, rest


def build_parser():
    p = argparse.ArgumentParser(
        prog="csv-reorder-columns",
        description="Reorder the columns of a CSV file.",
    )
    p.add_argument("file", nargs="?", default="-",
                   help="CSV file to read (default: stdin; '-' also means stdin)")
    p.add_argument("--order", required=True, metavar="COL,...",
                   help="comma-separated list of column names or 1-based indices, in the desired leading order")
    p.add_argument("--rest", choices=("append", "prepend"), default="append",
                   help="where to put unlisted columns (default: append)")
    p.add_argument("-d", "--delimiter", default=",",
                   help="field delimiter for input and output (default: ',')")
    p.add_argument("--no-header", action="store_true",
                   help="input has no header row; --order then accepts only 1-based indices")
    p.add_argument("--check", action="store_true",
                   help="exit 2 if the file column order differs from the requested order; print nothing on success")
    p.add_argument("--json", action="store_true",
                   help="print a JSON report instead of the CSV")
    p.add_argument("--quiet", action="store_true",
                   help="with --check, suppress the human-readable diagnosis")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    parse = getattr(parser, "parse_intermixed_args", parser.parse_args)
    args = parse(argv)

    delimiter = args.delimiter
    if len(delimiter) != 1:
        print("csv-reorder-columns: error: delimiter must be a single character", file=sys.stderr)
        return 1

    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, "r", encoding="utf-8", newline=None) as fh:
                text = fh.read()
    except OSError as exc:
        print(f"csv-reorder-columns: error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 1

    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    except csv.Error as exc:
        print(f"csv-reorder-columns: error: malformed CSV: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("csv-reorder-columns: error: empty input", file=sys.stderr)
        return 1

    header = rows[0]
    if args.no_header:
        header = [str(i + 1) for i in range(len(header))]

    order_specs = [s for s in args.order.split(",") if s.strip()]
    try:
        picked, rest = resolve_indices(order_specs, header)
    except ValueError as exc:
        print(f"csv-reorder-columns: error: {exc}", file=sys.stderr)
        return 1

    final = picked + rest if args.rest == "append" else rest + picked
    current = list(range(len(header)))
    changed = final != current

    if args.check:
        if changed:
            if not args.quiet:
                print("csv-reorder-columns: check failed: column order differs", file=sys.stderr)
            return 2
        if not args.quiet and not args.json:
            print("csv-reorder-columns: OK (column order matches)")
        return 0

    if args.json:
        report = {
            "file": None if args.file == "-" else args.file,
            "columns": len(header),
            "listed": len(picked),
            "new_order": [header[i] for i in final],
            "changed": changed,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    out = io.StringIO()
    writer = csv.writer(out, delimiter=delimiter, lineterminator="\n")
    for row in rows:
        writer.writerow([row[i] if i < len(row) else "" for i in final])
    sys.stdout.write(out.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())
