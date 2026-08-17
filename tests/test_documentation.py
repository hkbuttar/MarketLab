"""Checks for the focused documentation contract."""

from pathlib import Path

DOCUMENTS = (
    "system-architecture.md",
    "repository-architecture.md",
    "data-methodology.md",
    "factor-research.md",
    "backtesting-methodology.md",
    "ml-validation.md",
    "testing.md",
    "user-guide.md",
)


def test_core_documentation_exists_and_is_linked() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    for name in DOCUMENTS:
        path = Path("docs") / name
        assert path.is_file()
        assert path.stat().st_size > 300
        assert f"docs/{name}" in readme


def test_readme_no_longer_claims_domain_modules_are_empty() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Domain modules intentionally contain no implementation" not in readme
