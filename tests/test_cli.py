import json
import subprocess
import sys
from pathlib import Path

CLI = [sys.executable, "-m", "csv_reorder_columns.cli"]

SAMPLE = "id,name,email,age\n1,Alice,alice@example.com,34\n2,Bob,bob@example.com,28\n"


def run(args, stdin=""):
    return subprocess.run(
        CLI + args, input=stdin, capture_output=True, text=True, cwd=Path(__file__).parent.parent
    )


def test_reorder_by_name():
    r = run(["--order", "email,name"], SAMPLE)
    assert r.returncode == 0
    assert r.stdout.splitlines()[0] == "email,name,id,age"
    assert r.stdout.splitlines()[1].startswith("alice@example.com,Alice")


def test_reorder_by_index():
    r = run(["--order", "3,1"], SAMPLE)
    assert r.returncode == 0
    assert r.stdout.splitlines()[0] == "email,id,name,age"


def test_rest_drop():
    r = run(["--order", "name", "--rest", "drop"], SAMPLE)
    assert r.returncode == 0
    assert r.stdout.splitlines()[0] == "name"
    assert len(r.stdout.strip().splitlines()) == 3


def test_rest_prepend():
    r = run(["--order", "age", "--rest", "prepend"], SAMPLE)
    assert r.returncode == 0
    assert r.stdout.splitlines()[0] == "id,name,email,age"


def test_unknown_column():
    r = run(["--order", "nope"], SAMPLE)
    assert r.returncode == 1
    assert "unknown column" in r.stderr


def test_duplicate_selector():
    r = run(["--order", "name,name"], SAMPLE)
    assert r.returncode == 1
    assert "duplicate" in r.stderr


def test_out_of_range_index():
    r = run(["--order", "99"], SAMPLE)
    assert r.returncode == 1
    assert "out of range" in r.stderr


def test_check_fail_and_pass():
    r = run(["--order", "email,name", "--check"], SAMPLE)
    assert r.returncode == 2
    r2 = run(["--order", "id,name", "--check"], SAMPLE)
    assert r2.returncode == 0


def test_check_json():
    r = run(["--order", "email,name", "--check", "--json"], SAMPLE)
    assert r.returncode == 2
    report = json.loads(r.stdout)
    assert report["changed"] is True
    assert report["requested_order"] == ["email", "name", "id", "age"]


def test_json_report():
    r = run(["--order", "name", "--rest", "drop", "--json"], SAMPLE)
    assert r.returncode == 0
    report = json.loads(r.stdout)
    assert report["columns_out"] == 1
    assert set(report["dropped"]) == {"id", "email", "age"}


def test_no_header():
    data = "1,Alice,34\n2,Bob,28\n"
    r = run(["--no-header", "--order", "2,1"], data)
    assert r.returncode == 0
    assert r.stdout.splitlines()[0] == "Alice,1,34"


def test_quoted_fields_preserved():
    data = 'id,note\n1,"hello, world"\n'
    r = run(["--order", "note,id"], data)
    assert r.returncode == 0
    assert '"hello, world",1' in r.stdout


def test_empty_input():
    r = run(["--order", "a"], "")
    assert r.returncode == 1
