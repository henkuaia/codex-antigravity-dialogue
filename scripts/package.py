"""Build a skill-only ZIP from an explicit public-file allowlist."""

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
RUNTIME_FILES = (
    "SKILL.md",
    "LICENSE",
    "agents/openai.yaml",
    "references/installation.md",
    "references/diagnostics.md",
    "references/handoffs.md",
    "references/compatibility.md",
    "scripts/doctor.py",
)


def build(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in RUNTIME_FILES:
            archive.write(ROOT / relative, "codex-antigravity-dialogue/" + relative)
    return output


if __name__ == "__main__":
    print(build(ROOT / "dist" / f"codex-antigravity-dialogue-v{VERSION}.zip"))
