import json
from pathlib import Path
import re
import tempfile
import unicodedata
import unittest
import zipfile

from scripts.package import RUNTIME_FILES, build


ROOT = Path(__file__).resolve().parents[1]


def _slugify(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\- ]", "", text)
    return text.replace(" ", "-")


def _is_punct(ch: str) -> bool:
    if not ch:
        return False
    cat = unicodedata.category(ch)
    return cat.startswith("P") or cat.startswith("S")


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

    def test_local_markdown_links_and_anchors_resolve(self):
        md_files = list(ROOT.rglob("*.md"))
        anchors = {}
        for path in md_files:
            text = path.read_text(encoding="utf-8")
            file_anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
            for match in re.finditer(r"^#{1,6}\s+(.+)$", text, re.M):
                file_anchors.add(_slugify(match.group(1)))
            anchors[path.resolve()] = file_anchors

        link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)|(?:href|src)=\"([^\"]+)\"")
        for path in md_files:
            text = path.read_text(encoding="utf-8")
            for match in link_re.finditer(text):
                target = match.group(1) or match.group(2)
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                path_part, _, frag = target.partition("#")
                resolved = (path.parent / path_part).resolve() if path_part else path.resolve()
                with self.subTest(file=path.name, target=target):
                    self.assertTrue(resolved.is_file(), f"Missing target file: {resolved}")
                    if frag and resolved in anchors:
                        self.assertIn(frag, anchors[resolved], f"Missing anchor #{frag} in {resolved.name}")

    def test_markdown_commonmark_formatting_and_code_blocks_are_clean(self):
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            in_code = False
            for idx, line in enumerate(text.splitlines(), 1):
                if line.strip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    continue
                clean = re.sub(r"`[^`]+`", lambda m: " " * len(m.group(0)), line)
                for match in re.finditer(r"\*\*(.+?)\*\*", clean):
                    start, end = match.start(), match.end()
                    prev_ch = clean[start - 1] if start > 0 else ""
                    first_in = match.group(1)[0]
                    last_in = match.group(1)[-1]
                    next_ch = clean[end] if end < len(clean) else ""
                    left_bad = _is_punct(first_in) and prev_ch and not (prev_ch.isspace() or _is_punct(prev_ch))
                    right_bad = _is_punct(last_in) and next_ch and not (next_ch.isspace() or _is_punct(next_ch))
                    with self.subTest(file=path.name, line=idx):
                        self.assertFalse(left_bad or right_bad, f"CommonMark bold flanking issue at {path.name}:{idx}: {line}")

    def test_evaluation_cases_are_distinct_and_have_observable_expectations(self):
        data = json.loads((ROOT / "evals/scenarios.json").read_text(encoding="utf-8"))
        cases = data["scenarios"]
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        self.assertGreaterEqual(len(cases), 11)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["request"])
                self.assertTrue(case["context"])
                self.assertTrue(case["expected"])
                self.assertTrue(case["forbidden"])

    def test_no_private_user_paths_or_live_conversation_ids_in_repo_files(self):
        forbidden_patterns = (
            r"(?i)[a-z]:\\users\\",
            r"(?i)[a-z]:/users/",
            r"(?i)/Users/[a-z0-9_.-]+/",
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b",
        )
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts or path.suffix == ".zip":
                continue
            text = path.read_text(encoding="utf-8")
            for pat in forbidden_patterns:
                with self.subTest(file=path.name, pattern=pat):
                    self.assertIsNone(re.search(pat, text), f"Private path/UUID pattern {pat} found in {path}")


if __name__ == "__main__":
    unittest.main()
