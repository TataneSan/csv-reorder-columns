import json
import subprocess
import sys
import unittest


def run(args, stdin_text=""):
    return subprocess.run(
        [sys.executable, "-m", "csv_reorder_columns", *args],
        input=stdin_text, capture_output=True, text=True,
    )


SAMPLE = "name,age,city\nalice,30,paris\nbob,25,lyon\n"


class TestCli(unittest.TestCase):
    def test_reorder_by_name(self):
        proc = run(["--order", "city,name", "-"], SAMPLE)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "city,name,age\nparis,alice,30\nlyon,bob,25\n")

    def test_reorder_by_index(self):
        proc = run(["--order", "3,1", "-"], SAMPLE)
        self.assertEqual(proc.stdout, "city,name,age\nparis,alice,30\nlyon,bob,25\n")

    def test_rest_prepend(self):
        proc = run(["--order", "name", "--rest", "prepend", "-"], SAMPLE)
        self.assertEqual(proc.stdout, "age,city,name\n30,paris,alice\n25,lyon,bob\n")

    def test_unknown_column(self):
        proc = run(["--order", "nope", "-"], SAMPLE)
        self.assertEqual(proc.returncode, 1)

    def test_duplicate_column(self):
        proc = run(["--order", "name,name", "-"], SAMPLE)
        self.assertEqual(proc.returncode, 1)

    def test_no_header(self):
        proc = run(["--no-header", "--order", "2,1", "-"], "a,b,c\n1,2,3\n")
        self.assertEqual(proc.stdout, "b,a,c\n2,1,3\n")

    def test_check_pass(self):
        proc = run(["--order", "name,age,city", "--check", "-"], SAMPLE)
        self.assertEqual(proc.returncode, 0)

    def test_check_fail(self):
        proc = run(["--order", "city", "--check", "-"], SAMPLE)
        self.assertEqual(proc.returncode, 2)

    def test_json(self):
        proc = run(["--order", "city", "--json", "-"], SAMPLE)
        self.assertEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertEqual(report["new_order"], ["city", "name", "age"])
        self.assertTrue(report["changed"])

    def test_delimiter(self):
        proc = run(["-d", ";", "--order", "b,a", "-"], "a;b\n1;2\n")
        self.assertEqual(proc.stdout, "b;a\n2;1\n")


if __name__ == "__main__":
    unittest.main()
