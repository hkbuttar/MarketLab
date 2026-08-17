"""Reproducible Markdown and HTML research report assembly."""

from collections.abc import Mapping
from dataclasses import dataclass
from html import escape
from pathlib import Path


@dataclass(frozen=True)
class ResearchReport:
    """Structured, evidence-based research report content."""

    title: str
    hypothesis: str
    experiment_id: str
    configuration: Mapping[str, object]
    sections: Mapping[str, str]
    limitations: tuple[str, ...]


def write_research_report(
    report: ResearchReport, output_stem: Path
) -> tuple[Path, Path]:
    """Write equivalent Markdown and standalone HTML reports atomically."""

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(report)
    html = render_html(report)
    markdown_path = output_stem.with_suffix(".md")
    html_path = output_stem.with_suffix(".html")
    _atomic_write(markdown_path, markdown)
    _atomic_write(html_path, html)
    return markdown_path, html_path


def render_markdown(report: ResearchReport) -> str:
    """Render a report without inventing conclusions or recommendations."""

    lines = [
        f"# {report.title}",
        "",
        f"**Experiment:** `{report.experiment_id}`",
        "",
        "## Research hypothesis",
        "",
        report.hypothesis,
        "",
        "## Experiment configuration",
        "",
        "| Parameter | Value |",
        "|---|---|",
    ]
    lines.extend(
        f"| {key.replace('_', ' ').title()} | {value} |"
        for key, value in sorted(report.configuration.items())
    )
    if not report.configuration:
        lines.append("| Configuration | Unavailable for legacy run |")
    for heading, content in report.sections.items():
        lines.extend(("", f"## {heading}", "", content))
    lines.extend(("", "## Limitations", ""))
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(
        (
            "",
            "## Conclusion",
            "",
            "This report documents observed research results and does not constitute "
            "an investment recommendation.",
            "",
        )
    )
    return "\n".join(lines)


def render_html(report: ResearchReport) -> str:
    """Render a compact standalone HTML companion to the Markdown report."""

    configuration = "".join(
        f"<tr><th>{escape(key.replace('_', ' ').title())}</th>"
        f"<td>{escape(str(value))}</td></tr>"
        for key, value in sorted(report.configuration.items())
    )
    if not configuration:
        configuration = (
            "<tr><th>Configuration</th><td>Unavailable for legacy run</td></tr>"
        )
    sections = "".join(
        f"<section><h2>{escape(heading)}</h2><p>{escape(content)}</p></section>"
        for heading, content in report.sections.items()
    )
    limitations = "".join(f"<li>{escape(item)}</li>" for item in report.limitations)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>{escape(report.title)}</title><style>
body{{font:16px/1.6 system-ui,sans-serif;color:#17211d;max-width:900px;
margin:48px auto;padding:0 24px}}h1,h2{{font-family:Georgia,serif}}
h1{{font-size:42px}}h2{{margin-top:36px;border-bottom:1px solid #ddd;
padding-bottom:8px}}table{{border-collapse:collapse;width:100%}}
th,td{{border-bottom:1px solid #ddd;padding:9px;text-align:left}}th{{width:35%}}
.notice{{background:#edf2e8;padding:14px;border-radius:8px}}
code{{font-size:13px}}</style></head><body><h1>{escape(report.title)}</h1>
<p><strong>Experiment:</strong> <code>{escape(report.experiment_id)}</code></p>
<section><h2>Research hypothesis</h2>
<p>{escape(report.hypothesis)}</p></section>
<section><h2>Experiment configuration</h2>
<table>{configuration}</table></section>{sections}
<section><h2>Limitations</h2><ul>{limitations}</ul></section>
<section><h2>Conclusion</h2><p class="notice">This report documents observed
research results and does not constitute an investment recommendation.</p></section>
</body></html>"""


def _atomic_write(path: Path, content: str) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(content, encoding="utf-8")
    partial.replace(path)
