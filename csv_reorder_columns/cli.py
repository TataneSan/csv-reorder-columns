#!/usr/bin/env python3
"""Reorder the columns of a CSV file.

Takes an ordered list of column names and rewrites the CSV with the
columns in that order. Unlisted columns are appended at the end unless
--drop-rest is given.

Exit codes:
  0 - ok
  1 - I/O or CLI error
  2 - check failed (unknown column requested)
"""
import argparse
import csv
import json
import sys


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="csv-reorder-columns",
        description="Rewrite a CSV with its columns in a given order.")
    p.add_argument("columns", help="comma-separated column names in the desired order")
    p.add_argument("csvfile", nargs="?", default="-",
                   help="CSV file (default: stdin, '-' for stdin)")
    p.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    p.add_argument("--drop-rest", action="store_true",
                   help="drop columns not listed instead of appending them")
    p.add_argument("--check", action="store_true",
                   help="exit 2 if the current column order already differs; don't rewrite")
    p.add_argument("--json", action="store_true", help="emit JSON report (implies no CSV output)")
    args = p.parse_args(argv)

    wanted = [c.strip() for c in args.columns.split(",") if c.strip()]
    if not wanted:
        print("error: empty column list", file=sys.stderr)
        return 1

    try:
        if args.csvfile == "-":
            rows = list(csv.reader(sys.stdin, delimiter=args.delimiter))
        else:
            with open(args.csvfile, "r", encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh, delimiter=args.delimiter))
    except OSError as exc:
        print("error: cannot read %s: %s" % (args.csvfile, exc), file=sys.stderr)
        return 1

    if not rows:
        print("error: empty CSV", file=sys.stderr)
        return 1

    header = rows[0]
    missing = [c for c in wanted if c not in header]
    if missing:
        print("error: unknown columns: %s (header: %s)" % (", ".join(missing), header),
              file=sys.stderr)
        return 2

    rest = [c for c in header if c not in wanted]
    new_order = wanted if args.drop_rest else wanted + rest
    new_idx = [header.index(c) for c in new_order]

    report = {"input_order": header, "output_order": new_order, "dropped": rest if args.drop_rest else []}

    if args.check:
        differs = new_order != header
        report["differs"] = differs
        if args.json:
            json.dump(report, sys.stdout, indent=2)
            sys.stdout.write("\n")
        elif differs:
            print("current order: %s" % ",".join(header))
            print("desired order: %s" % ",".join(new_order))
        return 2 if differs else 0

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    writer = csv.writer(sys.stdout, delimiter=args.delimiter, lineterminator="\n")
    for row in rows:
        writer.writerow([row[i] if i < len(row) else "" for i in new_idx])
    return 0


if __name__ == "__main__":
    sys.exit(main())
