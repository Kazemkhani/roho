import ast
import json
import unittest
from pathlib import Path


class NotebookTests(unittest.TestCase):
    def test_structure_and_code_cells(self):
        path = Path(__file__).resolve().parents[1] / "notebooks/roho_kaggle.ipynb"
        notebook = json.loads(path.read_text())
        self.assertEqual(notebook["nbformat"], 4)
        self.assertEqual(notebook["nbformat_minor"], 5)
        ids = []
        for cell in notebook["cells"]:
            ids.append(cell["id"])
            self.assertIn(cell["cell_type"], ("code", "markdown"))
            self.assertIsInstance(cell["metadata"], dict)
            if cell["cell_type"] == "code":
                ast.parse("".join(cell["source"]))
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
