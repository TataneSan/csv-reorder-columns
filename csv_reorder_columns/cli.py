"""csv-reorder-columns: reorder the columns of a CSV document.

Reads a CSV document (file or stdin), rewrites the columns in the requested
order and prints the result. Column selectors are header names or 1-based
indices. Columns not listed are kept, appended or prepended according to
--rest. Also usable as a CI gate with --check.

Exit codes:
  0  success
  1  I/O or argument error (unknown column, duplicate selector, ...)
  2  check mode: the input column order differs from the requested one
"""

import argparse
import csv
import io
import json
import sys

from . import __version__

REST_MODES = ("append", "prepend", "drop")


def parse_delimiter(value):
    aliases = {"\\t": "\t", "tab": "\t", "comma": ",", "semicolon": ";", "pipe": "|"}
    if value in aliases:
        return aliases[value]
    if len(value) != 1:
        raise ValueError(
            "delimiter must be a single character (aliases: tab, comma, semicolon, pipe)"
        )
    return value


def split_selectors(order_arg):
    parts = [p.strip() for p in order_arg.split(",")]
    return [p for p in parts if p != ""]


def resolve_selectors(header, selectors):
    """Return (selected_indices, rest_indices) or raise ValueError."""
    n = len(header)
    selected = []
    for sel in selectors:
        if sel.lstrip("-").isdigit():
            idx = int(sel)
            if idx < 1 or idx > n:
                raise ValueError(f"column index out of range: {sel} (header has {n} columns)")
            pos = idx - 1
        else:
            matches = [i for i, name in enumerate(header) if name == sel]
            if not matches:
                raise ValueError(f"unknown column name: {sel!r}")
            if len(matches) > 1:
                raise ValueError(f"ambiguous column name {sel!r}: matches {len(matches)} header cells")
            pos = matches[0]
        if pos in selected:
            raise ValueError(f"duplicate selector: {sel!r}")
        selected.append(pos)
    rest = [i for i in range(n) if i not in selected]
    return selected, rest


def final_order(selected, rest, mode):
    if mode == "append":
        return selected + rest
    if mode == "prepend":
        return rest + selected
    return list(selected)  # drop


def reorder_rows(rows, order):
    out = []
    for row in rows:
        # tolerate ragged rows: missing cells become empty strings
        out.append([row[i] if i < len(row) else "" for i in order])
    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog="csv-reorder-columns",
        description="Reorder the columns of a CSV document by name or index.",
    )
    p.add_argument("file", nargs="?", default="-",
                   help="CSV file to read (default: stdin; '-' also means stdin)")
    p.add_argument("-o", "--order", required=True,
                   help="comma-separated column selectors (header names or 1-based indices)")
    p.add_argument("--rest", choices=REST_MODES, default="append",
                   help="what to do with unlisted columns: append, prepend, drop (default: append)")
    p.add_argument("-d", "--delimiter", default=",",
                   help="field delimiter (default: ','; aliases: tab, comma, semicolon, pipe)")
    p.add_argument("-q", "--quotechar", default='"',
                   help="quote character (default: double quote)")
    p.add_argument("--no-header", action="store_true",
                   help="treat the first row as data; selectors must be indices")
    p.add_argument("--check", action="store_true",
                   help="do not print the CSV; exit 2 if the input order would change")
    p.add_argument("--json", action="store_true",
                   help="print a JSON report instead of the CSV")
    p.add_argument("--quiet", action="store_true",
                   help="with --check, suppress the human-readable diagnosis")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        delimiter = parse_delimiter(args.delimiter)
    except ValueError as exc:
        print(f"csv-reorder-columns: error: {exc}", file=sys.stderr)
        return 1
    if len(args.quotechar) != 1:
        print("csv-reorder-columns: error: quotechar must be a single character", file=sys.stderr)
        return 1

    selectors = split_selectors(args.order)
    if not selectors:
        print("csv-reorder-columns: error: --order is empty", file=sys.stderr)
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

    reader = csv.reader(io.StringIO(text), delimiter=delimiter, quotechar=args.quotechar)
    rows = list(reader)
    if not rows:
        print("csv-reorder-columns: error: empty input", file=sys.stderr)
        return 1

    if args.no_header:
        header = [str(i + 1) for i in range(len(rows[0]))]
        data_rows = rows
    else:
        header = rows[0]
        data_rows = rows[1:]

    try:
        selected, rest = resolve_selectors(header, selectors)
    except ValueError as exc:
        print(f"csv-reorder-columns: error: {exc}", file=sys.stderr)
        return 1

    order = final_order(selected, rest, args.rest)
    new_header = [header[i] for i in order]

    changed = order != list(range(len(header)))

    if args.check:
        report = {
            "file": args.file,
            "columns": len(header),
            "requested_order": new_header,
            "rest_mode": args.rest,
            "changed": changed,
            "ok": not changed,
        }
        if args.json:
            print(json.dumps(report, indent=2))
        elif not args.quiet:
            if changed:
                print(
                    f"csv-reorder-columns: {args.file}: column order would change "
                    f"from [{', '.join(header)}] to [{', '.join(new_header)}]",
                    file=sys.stderr,
                )
            else:
                print(f"csv-reorder-columns: {args.file}: column order OK", file=sys.stderr)
        return 2 if changed else 0

    out_rows = ([new_header] if not args.no_header else []) + reorder_rows(data_rows, order)

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, quotechar=args.quotechar,
                        lineterminator="\n")
    writer.writerows(out_rows)
    output = buf.getvalue()

    if args.json:
        report = {
            "file": args.file,
            "rows": len(out_rows),
            "columns_in": len(header),
            "columns_out": len(new_header),
            "new_order": new_header,
            "dropped": [header[i] for i in rest] if args.rest == "drop" else [],
            "changed": changed,
        }
        print(json.dumps(report, indent=2))
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
