"""Output formatting utilities for trial data."""

from typing import Any


def format_trial_summary(trial: dict[str, Any]) -> str:
    """
    Format a trial summary as readable text.

    Args:
        trial: Trial summary dictionary

    Returns:
        Formatted string
    """
    lines = [
        f"**{trial.get('nct_id', 'Unknown')}**: {trial.get('title', 'No Title')}",
        f"- Status: {trial.get('status', 'Unknown')}",
        f"- Phase: {', '.join(trial.get('phase', [])) or 'N/A'}",
        f"- Sponsor: {trial.get('sponsor', 'Unknown')}",
    ]

    if trial.get("conditions"):
        lines.append(f"- Conditions: {', '.join(trial['conditions'][:3])}")

    if trial.get("interventions"):
        lines.append(f"- Interventions: {', '.join(trial['interventions'][:3])}")

    if trial.get("enrollment"):
        lines.append(f"- Enrollment: {trial['enrollment']}")

    if trial.get("locations"):
        lines.append(f"- Locations: {trial['locations'][0]}" + (
            f" (+{len(trial['locations'])-1} more)" if len(trial["locations"]) > 1 else ""
        ))

    return "\n".join(lines)


def format_markdown(trials: list[dict[str, Any]], title: str = "Clinical Trials") -> str:
    """
    Format a list of trials as Markdown document.

    Args:
        trials: List of trial summary dictionaries
        title: Document title

    Returns:
        Markdown formatted string
    """
    lines = [f"# {title}", "", f"Found {len(trials)} trial(s).", ""]

    for i, trial in enumerate(trials, 1):
        lines.append(f"## {i}. {trial.get('title', 'Unknown Trial')}")
        lines.append("")
        lines.append(f"**NCT ID:** {trial.get('nct_id', 'Unknown')}")
        lines.append(f"**Status:** {trial.get('status', 'Unknown')}")
        lines.append(f"**Phase:** {', '.join(trial.get('phase', [])) or 'N/A'}")
        lines.append(f"**Sponsor:** {trial.get('sponsor', 'Unknown')}")

        if trial.get("conditions"):
            lines.append(f"**Conditions:** {', '.join(trial['conditions'])}")

        if trial.get("interventions"):
            lines.append(f"**Interventions:** {', '.join(trial['interventions'])}")

        if trial.get("enrollment"):
            lines.append(f"**Enrollment:** {trial['enrollment']}")

        if trial.get("start_date"):
            lines.append(f"**Start Date:** {trial['start_date']}")

        if trial.get("completion_date"):
            lines.append(f"**Expected Completion:** {trial['completion_date']}")

        if trial.get("locations"):
            lines.append(f"**Locations:** {'; '.join(trial['locations'][:3])}")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_csv_row(trial: dict[str, Any], fields: list[str] | None = None) -> str:
    """
    Format a trial as CSV row.

    Args:
        trial: Trial data dictionary
        fields: List of fields to include

    Returns:
        CSV formatted row
    """
    if fields is None:
        fields = ["nct_id", "title", "status", "phase", "sponsor", "enrollment"]

    values = []
    for field in fields:
        value = trial.get(field, "")
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        # Escape quotes and wrap in quotes if contains comma
        value = str(value).replace('"', '""')
        if "," in value or '"' in value or "\n" in value:
            value = f'"{value}"'
        values.append(value)

    return ",".join(values)


def format_csv(
    trials: list[dict[str, Any]],
    fields: list[str] | None = None,
) -> str:
    """
    Format trials as CSV document.

    Args:
        trials: List of trial data dictionaries
        fields: List of fields to include

    Returns:
        CSV formatted string
    """
    if fields is None:
        fields = ["nct_id", "title", "status", "phase", "sponsor", "enrollment", "conditions"]

    lines = [",".join(fields)]  # Header

    for trial in trials:
        lines.append(format_csv_row(trial, fields))

    return "\n".join(lines)


def format_eligibility(eligibility_text: str) -> dict[str, list[str]]:
    """
    Parse and format eligibility criteria text.

    Args:
        eligibility_text: Raw eligibility criteria string

    Returns:
        Dictionary with 'inclusion' and 'exclusion' criteria lists
    """
    inclusion = []
    exclusion = []

    if not eligibility_text:
        return {"inclusion": inclusion, "exclusion": exclusion}

    # Split into lines
    lines = eligibility_text.split("\n")
    current_section = "inclusion"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for section headers
        lower_line = line.lower()
        if "inclusion" in lower_line and ("criteria" in lower_line or ":" in line):
            current_section = "inclusion"
            continue
        elif "exclusion" in lower_line and ("criteria" in lower_line or ":" in line):
            current_section = "exclusion"
            continue

        # Add criterion to appropriate list
        # Clean up bullet points and numbering
        line = line.lstrip("•-*·").strip()
        line = line.lstrip("0123456789.").strip()

        if line:
            if current_section == "inclusion":
                inclusion.append(line)
            else:
                exclusion.append(line)

    return {"inclusion": inclusion, "exclusion": exclusion}


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
