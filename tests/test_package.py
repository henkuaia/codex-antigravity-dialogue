import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

from scripts.package import RUNTIME_FILES, build


ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_release_has_only_allowlisted_runtime_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = build(Path(directory) / "skill.zip")
            with zipfile.ZipFile(output) as archive:
                prefix = "codex-antigravity-dialogue/"
                self.assertEqual(set(archive.namelist()), {prefix + name for name in RUNTIME_FILES})
                for name in RUNTIME_FILES:
                    with self.subTest(name=name):
                        self.assertEqual(archive.read(prefix + name), (ROOT / name).read_bytes())

    def test_local_markdown_links_resolve(self):
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if "://" not in target and not target.startswith("#"):
                    with self.subTest(file=path.name, target=target):
                        self.assertTrue((path.parent / target.split("#", 1)[0]).is_file())

    def test_evaluation_cases_are_distinct_and_have_observable_expectations(self):
        data = json.loads((ROOT / "evals/scenarios.json").read_text(encoding="utf-8"))
        cases = data["scenarios"]
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["request"])
                self.assertTrue(case["context"])
                self.assertTrue(case["expected"])
                self.assertTrue(case["forbidden"])


if __name__ == "__main__":
    unittest.main()
