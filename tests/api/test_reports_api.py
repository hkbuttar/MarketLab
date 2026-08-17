"""Tests for report catalog and safe previews."""

import pytest

from backend.services.reports import report_catalog, report_content


def test_report_catalog_and_content_are_root_bounded(tmp_path) -> None:
    report = tmp_path / "reports/studies/momentum.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Momentum\n", encoding="utf-8")

    items = report_catalog(tmp_path)
    content = report_content("studies/momentum.md", tmp_path)

    assert items[0].category == "studies"
    assert content.content == "# Momentum\n"
    with pytest.raises(FileNotFoundError):
        report_content("../outside.txt", tmp_path)
