"""Tool 8: analyze_sponsor_network - Organization intelligence and pipeline analysis."""

from typing import Any

from core.api_client import get_api_client, APIError
from core.pagination import PaginationHandler
from core.models import AnalysisScope
from config import FIELDS_STANDARD
from utils.metrics import extract_trial_summary


async def analyze_sponsor_network(
    sponsor_name: str,
    analysis_scope: str = "ORGANIZATION",
    include_trial_portfolio: bool = True,
    analyze_therapeutic_areas: bool = True,
    analyze_stage_distribution: bool = True,
    analyze_collaboration_patterns: bool = False,
    time_window_years: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Analyze a sponsor's clinical trial portfolio and network.

    Provides organization intelligence including pipeline strength,
    therapeutic focus, and collaboration patterns.

    Args:
        sponsor_name: Organization name to analyze
        analysis_scope: ORGANIZATION, NETWORK (includes collaborators), or ECOSYSTEM
        include_trial_portfolio: Get their trial list
        analyze_therapeutic_areas: Group trials by disease area
        analyze_stage_distribution: Analyze phase distribution
        analyze_collaboration_patterns: Map partnership networks
        time_window_years: Limit to trials started within N years
        limit: Maximum trials to analyze

    Returns:
        Sponsor analysis with portfolio, therapeutic focus, and network data
    """
    client = get_api_client()
    pagination = PaginationHandler(client)

    # Determine scope
    try:
        scope = AnalysisScope(analysis_scope.upper())
    except ValueError:
        scope = AnalysisScope.ORGANIZATION

    # Build search parameters
    params: dict[str, Any] = {
        "query.spons": sponsor_name,
        "fields": "|".join(FIELDS_STANDARD + ["Collaborator", "LeadSponsorClass"]),
    }

    # Time window filter
    if time_window_years:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=time_window_years * 365)
        params["filter.advanced"] = f'AREA[StartDate]RANGE[{cutoff.strftime("%Y-%m-%d")},MAX]'

    # Execute search
    try:
        response = await pagination.fetch_all_pages(
            query_params=params,
            max_results=limit,
            count_total=True,
        )
    except APIError as e:
        return {
            "status": "ERROR",
            "message": str(e),
        }

    studies = response.get("studies", [])

    if not studies:
        return {
            "status": "SUCCESS",
            "message": f"No trials found for sponsor: {sponsor_name}",
            "sponsor_summary": {
                "name": sponsor_name,
                "trial_count": 0,
            },
        }

    # Process trials
    trial_summaries = []
    by_condition: dict[str, list[dict]] = {}
    by_phase: dict[str, int] = {}
    by_status: dict[str, int] = {}
    collaborators: dict[str, int] = {}
    sponsor_class = None
    total_enrollment = 0

    for study in studies:
        summary = extract_trial_summary(study)
        trial_summaries.append(summary)

        # Get sponsor class
        if not sponsor_class:
            sponsor_class = summary.get("sponsor_class")

        # Enrollment
        enrollment = summary.get("enrollment") or 0
        total_enrollment += enrollment

        # By condition
        conditions = summary.get("conditions") or []
        for cond in conditions:
            if cond not in by_condition:
                by_condition[cond] = []
            by_condition[cond].append(summary)

        # By phase
        phases = summary.get("phase") or ["N/A"]
        for phase in phases:
            by_phase[phase] = by_phase.get(phase, 0) + 1

        # By status
        status = summary.get("status", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1

        # Collaborators (from full study data)
        protocol = study.get("protocolSection", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        for collab in sponsor_module.get("collaborators", []):
            collab_name = collab.get("name", "")
            if collab_name:
                collaborators[collab_name] = collaborators.get(collab_name, 0) + 1

    # Build sponsor summary
    active_count = sum(1 for s in trial_summaries if s.get("status") in ["RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING"])
    completed_count = by_status.get("COMPLETED", 0)

    sponsor_summary = {
        "name": sponsor_name,
        "class": sponsor_class or "Unknown",
        "trial_count": len(studies),
        "total_enrollment_target": total_enrollment,
        "active_trials_count": active_count,
        "completed_trials_count": completed_count,
    }

    result: dict[str, Any] = {
        "status": "SUCCESS",
        "sponsor_summary": sponsor_summary,
    }

    # Trial portfolio
    if include_trial_portfolio:
        result["trial_portfolio"] = [
            {
                "nct_id": t["nct_id"],
                "title": t["title"][:100],
                "status": t["status"],
                "phase": t.get("phase", []),
                "conditions": t.get("conditions", [])[:2],
                "enrollment": t.get("enrollment"),
                "start_date": t.get("start_date"),
            }
            for t in trial_summaries[:50]  # Limit to 50 for response size
        ]

    # Therapeutic area breakdown
    if analyze_therapeutic_areas:
        therapeutic_areas = []
        for cond, trials in sorted(by_condition.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
            phases_in_area = {}
            total_area_enrollment = 0
            for t in trials:
                for p in t.get("phase") or ["N/A"]:
                    phases_in_area[p] = phases_in_area.get(p, 0) + 1
                total_area_enrollment += t.get("enrollment") or 0

            therapeutic_areas.append({
                "disease_area": cond,
                "trial_count": len(trials),
                "enrollment_focus": total_area_enrollment,
                "phase_distribution": phases_in_area,
                "active_count": sum(1 for t in trials if t.get("status") in ["RECRUITING", "ACTIVE_NOT_RECRUITING"]),
            })

        result["therapeutic_area_breakdown"] = therapeutic_areas

    # Pipeline stage distribution
    if analyze_stage_distribution:
        early_phase = by_phase.get("PHASE1", 0) + by_phase.get("EARLY_PHASE1", 0)
        mid_phase = by_phase.get("PHASE2", 0)
        late_phase = by_phase.get("PHASE3", 0) + by_phase.get("PHASE4", 0)

        total_phases = early_phase + mid_phase + late_phase
        if total_phases > 0:
            early_pct = early_phase / total_phases * 100
            late_pct = late_phase / total_phases * 100

            if early_pct > 50:
                portfolio_strength = "Early-Heavy - Focus on discovery"
            elif late_pct > 50:
                portfolio_strength = "Late-Heavy - Near-term commercial potential"
            elif mid_phase / total_phases > 0.4:
                portfolio_strength = "Mid-Heavy - Proof of concept focus"
            else:
                portfolio_strength = "Balanced - Diversified pipeline"
        else:
            portfolio_strength = "Unknown"

        result["pipeline_stage_distribution"] = {
            "early_phase": {
                "phases": ["EARLY_PHASE1", "PHASE1"],
                "count": early_phase,
            },
            "mid_phase": {
                "phases": ["PHASE2"],
                "count": mid_phase,
            },
            "late_phase": {
                "phases": ["PHASE3", "PHASE4"],
                "count": late_phase,
            },
            "phase_breakdown": by_phase,
            "portfolio_strength": portfolio_strength,
        }

    # Collaboration patterns
    if analyze_collaboration_patterns and collaborators:
        result["collaboration_network"] = {
            "total_collaborators": len(collaborators),
            "top_collaborators": [
                {"organization": k, "collaboration_count": v}
                for k, v in sorted(collaborators.items(), key=lambda x: x[1], reverse=True)[:10]
            ],
            "collaboration_intensity": "High" if len(collaborators) > 20 else "Moderate" if len(collaborators) > 5 else "Low",
        }

    # Add status distribution
    result["status_distribution"] = [
        {"status": k, "count": v}
        for k, v in sorted(by_status.items(), key=lambda x: x[1], reverse=True)
    ]

    return result
