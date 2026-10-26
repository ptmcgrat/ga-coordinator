"""The common library must run on Python 3.9 (spec section 8). This checks syntax only;
run the suite under 3.9 as well where one is available."""
import ast
import unittest
from pathlib import Path

import support


class Py39Syntax(unittest.TestCase):
    def test_all_python_files_parse_as_3_9(self):
        files = [p for p in support.ROOT.rglob("*.py") if "__pycache__" not in p.parts]
        self.assertGreater(len(files), 10)
        for p in files:
            try:
                ast.parse(p.read_text(), filename=str(p), feature_version=(3, 9))
            except SyntaxError as e:
                self.fail("%s is not Python 3.9 syntax: %s" % (p, e))


if __name__ == "__main__":
    unittest.main()
