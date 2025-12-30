"""Tool 9: export_and_format_trials - Multi-format batch export."""

from typing import Any

from core.api_client import get_api_client, APIError
from core.models import ExportFormat
from config import FIELDS_STANDARD
from utils.metrics import extract_trial_summary
from utils.formatting import format_markdown, format_csv


async def export_and_format_trials(
    trial_ids: list[str],
    export_format: str = "JSON",
    fields_to_include: list[str] | None = None,
    include_summary_stats: bool = True,
    grouping_strategy: str | None = None,
    sort_by: str = "AS_PROVIDED",
) -> dict[str, Any]:
    """
    Export clinical trials in multiple formats for reports and sharing.

    Args:
        trial_ids: List of NCT IDs to export
        export_format: JSON, CSV, or MARKDOWN
        fields_to_include: Specific fields to include
        include_summary_stats: Add aggregate statistics
        grouping_strategy: Group by CONDITION, PHASE, SPONSOR, or LOCATION
        sort_by: AS_PROVIDED, ENROLLMENT_DESC, START_DATE_DESC

    Returns:
        Formatted export with metadata
    """
    client = get_api_client()

    if not trial_ids:
        return {
            "status": "ERROR",
            "message": "Please provide trial_ids to export",
        }

    # Validate format
    try:
        fmt = ExportFormat(export_format.upper())
    except ValueError:
        fmt = ExportFormat.JSON

    # Determine fields
    fields = fields_to_include if fields_to_include else FIELDS_STANDARD

    # Fetch trials
    trials_data = []
    errors = []

    for tid in trial_ids:
        try:
            study = await client.get_study(tid.upper(), fields=fields)
            summary = extract_trial_summary(study)
            trials_data.append(summary)
        except APIError as e:
            errors.append(f"{tid}: {str(e)}")

    if not trials_data:
        return {
            "status": "ERROR",
            "message": "No trials could be fetched",
            "errors": errors,
        }

    # Sort if requested
    if sort_by == "ENROLLMENT_DESC":
        trials_data.sort(key=lambda x: x.get("enrollment") or 0, reverse=True)
    elif sort_by == "START_DATE_DESC":
        trials_data.sort(key=lambda x: x.get("start_date") or "", reverse=True)

    # Group if requested
    grouped_data = None
    if grouping_strategy:
        grouped_data = _group_trials(trials_data, grouping_strategy)

    # Calculate summary stats
    summary_stats = None
    if include_summary_stats:
        enrollments = [t.get("enrollment") or 0 for t in trials_data]
        phases = {}
        statuses = {}

        for t in trials_data:
            for p in t.get("phase") or ["N/A"]:
                phases[p] = phases.get(p, 0) + 1
            status = t.get("status", "Unknown")
            statuses[status] = statuses.get(status, 0) + 1

        summary_stats = {
            "total_trials": len(trials_data),
            "total_enrollment": sum(enrollments),
            "average_enrollment": round(sum(enrollments) / len(enrollments), 1) if enrollments else 0,
            "phase_distribution": phases,
            "status_distribution": statuses,
        }

    # Format output
    if fmt == ExportFormat.MARKDOWN:
        content = format_markdown(trials_data, title="Clinical Trials Export")
    elif fmt == ExportFormat.CSV:
        csv_fields = ["nct_id", "title", "status", "phase", "sponsor", "enrollment", "conditions"]
        content = format_csv(trials_data, fields=csv_fields)
    else:
        content = trials_data if not grouped_data else grouped_data

    result = {
        "status": "SUCCESS",
        "export_format": fmt.value,
        "record_count": len(trials_data),
    }

    if fmt == ExportFormat.JSON:
        result["data"] = content
    else:
        result["content"] = content

    if grouped_data and fmt == ExportFormat.JSON:
        result["grouped_data"] = grouped_data

    if summary_stats:
        result["summary_stats"] = summary_stats

    if errors:
        result["errors"] = errors

    result["metadata"] = {
        "fields_included": fields[:10] if len(fields) > 10 else fields,
        "grouping": grouping_strategy,
        "sort_order": sort_by,
    }

    return result


def _group_trials(trials: list[dict[str, Any]], strategy: str) -> dict[str, list[dict]]:
    """Group trials by specified strategy."""
    grouped: dict[str, list[dict]] = {}

    for trial in trials:
        if strategy == "CONDITION":
            keys = trial.get("conditions", ["Unknown"])
        elif strategy == "PHASE":
            keys = trial.get("phase", ["N/A"])
        elif strategy == "SPONSOR":
            keys = [trial.get("sponsor", "Unknown")]
        elif strategy == "LOCATION":
            locations = trial.get("locations", [])
            if locations:
                # Extract country from first location
                first_loc = locations[0]
                keys = [first_loc.split(",")[-1].strip() if "," in first_loc else first_loc]
            else:
                keys = ["Unknown"]
        else:
            keys = ["All"]

        for key in keys:
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(trial)

    return grouped
