from __future__ import annotations

from typing import Any


def _line(item: dict[str, Any]) -> str:
    label = str(item.get("label") or item.get("source") or "Finding").strip()
    detail = str(item.get("detail") or item.get("summary") or item.get("status") or "").strip()
    return f"- **{label}:** {detail}"


def format_incident_report(
    findings: list[dict[str, Any]] | None = None,
    template: str = "brief",
    incident_title: str = "IT incident",
) -> dict[str, Any]:
    findings = findings or []
    lines = [_line(item) for item in findings]
    if template == "technical":
        markdown = "\n".join([f"# {incident_title}", "", "## Diagnostic findings", *lines, "", "## Next step", "- Validate the evidence and assign an owner."])
    elif template == "handoff":
        markdown = "\n".join([f"# Handoff: {incident_title}", "", *lines, "", "- Owner: unassigned", "- Status: needs review"])
    else:
        markdown = "\n".join([f"**{incident_title}**", *lines])
    return {
        "tool": "format_incident_report",
        "template": template,
        "markdown": markdown,
        "finding_count": len(findings),
    }
