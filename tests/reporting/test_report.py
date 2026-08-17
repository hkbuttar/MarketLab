"""Tests for deterministic research report rendering."""

from marketlab.reporting.report import ResearchReport, render_html, render_markdown


def test_research_report_contains_configuration_limitations_and_disclaimer() -> None:
    report = ResearchReport(
        title="Momentum Study",
        hypothesis="Test momentum after costs.",
        experiment_id="run-1",
        configuration={"cost_bps": 10},
        sections={"Performance": "CAGR was 8%."},
        limitations=("Historical evidence only.",),
    )

    markdown = render_markdown(report)
    html = render_html(report)

    assert "| Cost Bps | 10 |" in markdown
    assert "Historical evidence only" in markdown
    assert "does not constitute an investment recommendation" in markdown
    assert "Momentum Study" in html
    assert "<script" not in html


def test_legacy_report_discloses_missing_configuration() -> None:
    report = ResearchReport(
        title="Legacy Study",
        hypothesis="Reproduce a legacy run.",
        experiment_id="legacy",
        configuration={},
        sections={},
        limitations=(),
    )

    assert "Unavailable for legacy run" in render_markdown(report)
