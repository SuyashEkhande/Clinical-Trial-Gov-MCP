"""Tool 7: get_enrollment_intelligence - Enrollment analytics and market capacity."""

from typing import Any

from core.api_client import get_api_client, APIError
from core.pagination import PaginationHandler
from config import FIELDS_SUMMARY
from utils.metrics import extract_trial_summary


async def get_enrollment_intelligence(
    condition: str | None = None,
    intervention_type: str | None = None,
    location_country: str | None = None,
    location_state: str | None = None,
    enrollment_status: list[str] | None = None,
    include_capacity_analysis: bool = True,
    include_velocity_analysis: bool = True,
    include_competitor_summary: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Analyze enrollment patterns and market capacity for clinical trials.

    Provides aggregate statistics, velocity metrics, and competitive intelligence
    for clinical operations and market analysis.

    Args:
        condition: Disease/condition to analyze
        intervention_type: Filter by intervention type
        location_country: Geographic focus - country
        location_state: Geographic focus - state
        enrollment_status: Trial statuses to include
        include_capacity_analysis: Calculate open enrollment slots
        include_velocity_analysis: Estimate enrollment speed
        include_competitor_summary: Rank trials by enrollment
        limit: Maximum trials to analyze

    Returns:
        Enrollment intelligence with aggregate stats and insights
    """
    client = get_api_client()
    pagination = PaginationHandler(client)

    # Build search parameters
    params: dict[str, Any] = {
        "fields": "|".join(FIELDS_SUMMARY + ["EnrollmentCount", "StartDate", "CompletionDate"]),
    }

    # Condition filter
    if condition:
        params["query.cond"] = condition

    # Intervention type
    if intervention_type:
        params["filter.advanced"] = f"AREA[InterventionType]{intervention_type.upper()}"

    # Status filter
    if enrollment_status:
        params["filter.overallStatus"] = "|".join(enrollment_status)
    else:
        # Default to active/recruiting
        params["filter.overallStatus"] = "RECRUITING|ACTIVE_NOT_RECRUITING|NOT_YET_RECRUITING"

    # Location filter
    if location_country or location_state:
        location_parts = []
        if location_state:
            location_parts.append(f'AREA[LocationState]"{location_state}"')
        if location_country:
            location_parts.append(f'AREA[LocationCountry]"{location_country}"')

        location_filter = "SEARCH[Location](" + " AND ".join(location_parts) + ")"
        if "filter.advanced" in params:
            params["filter.advanced"] += f" AND {location_filter}"
        else:
            params["filter.advanced"] = location_filter

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
    total_count = response.get("totalCount", len(studies))

    if not studies:
        return {
            "status": "SUCCESS",
            "message": "No trials found matching criteria",
            "aggregate_stats": {
                "total_trials_analyzed": 0,
            },
        }

    # Calculate aggregate statistics
    enrollments = []
    by_phase: dict[str, list[int]] = {}
    by_status: dict[str, int] = {}
    by_sponsor: dict[str, int] = {}
    by_country: dict[str, int] = {}

    trial_summaries = []

    for study in studies:
        summary = extract_trial_summary(study)
        trial_summaries.append(summary)

        enrollment = summary.get("enrollment") or 0
        if enrollment > 0:
            enrollments.append(enrollment)

        # By phase
        phases = summary.get("phase") or ["N/A"]
        for phase in phases:
            if phase not in by_phase:
                by_phase[phase] = []
            by_phase[phase].append(enrollment)

        # By status
        status = summary.get("status", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1

        # By sponsor
        sponsor = summary.get("sponsor", "Unknown")
        by_sponsor[sponsor] = by_sponsor.get(sponsor, 0) + 1

        # By country (from first location)
        locations = summary.get("locations", [])
        if locations:
            country = locations[0].split(",")[-1].strip() if "," in locations[0] else locations[0]
            by_country[country] = by_country.get(country, 0) + 1

    # Aggregate stats
    total_enrollment = sum(enrollments)
    avg_enrollment = sum(enrollments) / len(enrollments) if enrollments else 0

    aggregate_stats = {
        "total_trials_analyzed": len(studies),
        "total_in_database": total_count,
        "total_enrollment_target": total_enrollment,
        "average_enrollment_per_trial": round(avg_enrollment, 1),
        "median_enrollment": sorted(enrollments)[len(enrollments)//2] if enrollments else 0,
        "enrollment_range": {
            "min": min(enrollments) if enrollments else 0,
            "max": max(enrollments) if enrollments else 0,
        },
    }

    # Enrollment by phase
    enrollment_by_phase = []
    for phase, enroll_list in sorted(by_phase.items()):
        phase_total = sum(enroll_list)
        enrollment_by_phase.append({
            "phase": phase,
            "trial_count": len(enroll_list),
            "total_enrollment": phase_total,
            "average_enrollment": round(phase_total / len(enroll_list), 1) if enroll_list else 0,
        })

    # Status distribution
    status_distribution = [
        {"status": k, "count": v, "percentage": round(v / len(studies) * 100, 1)}
        for k, v in sorted(by_status.items(), key=lambda x: x[1], reverse=True)
    ]

    result: dict[str, Any] = {
        "status": "SUCCESS",
        "query_summary": {
            "condition": condition,
            "intervention_type": intervention_type,
            "location": location_country or location_state or "Global",
        },
        "aggregate_stats": aggregate_stats,
        "enrollment_by_phase": enrollment_by_phase,
        "status_distribution": status_distribution,
    }

    # Geographic distribution
    if by_country:
        result["geographic_distribution"] = [
            {"country": k, "trial_count": v}
            for k, v in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

    # Capacity analysis
    if include_capacity_analysis:
        recruiting_count = by_status.get("RECRUITING", 0)
        recruiting_enrollment = sum(
            s.get("enrollment") or 0
            for s in trial_summaries
            if s.get("status") == "RECRUITING"
        )

        result["capacity_analysis"] = {
            "recruiting_trials": recruiting_count,
            "estimated_open_slots": recruiting_enrollment,  # Simplified estimate
            "market_saturation": _estimate_saturation(recruiting_count, total_enrollment),
        }

    # Velocity analysis
    if include_velocity_analysis:
        result["velocity_insights"] = {
            "average_trial_size": round(avg_enrollment, 0),
            "enrollment_distribution": _categorize_enrollments(enrollments),
            "recommendation": _generate_velocity_recommendation(enrollments, recruiting_count=by_status.get("RECRUITING", 0)),
        }

    # Competitor summary
    if include_competitor_summary:
        top_sponsors = [
            {"sponsor": k, "trial_count": v}
            for k, v in sorted(by_sponsor.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # Top trials by enrollment
        top_trials = sorted(trial_summaries, key=lambda x: x.get("enrollment") or 0, reverse=True)[:10]

        result["competitive_insights"] = {
            "dominant_sponsors": top_sponsors,
            "largest_trials": [
                {
                    "nct_id": t["nct_id"],
                    "title": t["title"][:80],
                    "enrollment": t.get("enrollment"),
                    "sponsor": t.get("sponsor"),
                }
                for t in top_trials
            ],
            "market_concentration": _estimate_concentration(by_sponsor),
        }

    return result


def _estimate_saturation(recruiting_count: int, total_enrollment: int) -> str:
    """Estimate market saturation level."""
    if recruiting_count < 5:
        return "Low - Few active trials"
    elif recruiting_count < 20:
        return "Moderate - Some competition"
    elif recruiting_count < 50:
        return "High - Significant competition"
    else:
        return "Very High - Crowded market"


def _categorize_enrollments(enrollments: list[int]) -> dict[str, int]:
    """Categorize trials by enrollment size."""
    categories = {
        "small (<50)": 0,
        "medium (50-200)": 0,
        "large (200-500)": 0,
        "very_large (>500)": 0,
    }

    for e in enrollments:
        if e < 50:
            categories["small (<50)"] += 1
        elif e < 200:
            categories["medium (50-200)"] += 1
        elif e < 500:
            categories["large (200-500)"] += 1
        else:
            categories["very_large (>500)"] += 1

    return categories


def _generate_velocity_recommendation(enrollments: list[int], recruiting_count: int) -> str:
    """Generate enrollment velocity recommendation."""
    if not enrollments:
        return "Insufficient data for recommendation"

    avg = sum(enrollments) / len(enrollments)

    if avg < 50 and recruiting_count > 20:
        return "High competition for small trials - consider larger enrollment targets"
    elif avg > 200 and recruiting_count < 10:
        return "Large trials with low competition - favorable enrollment environment"
    elif recruiting_count > 30:
        return "Crowded market - differentiate on eligibility criteria or site selection"
    else:
        return "Moderate market conditions - standard enrollment timelines expected"


def _estimate_concentration(by_sponsor: dict[str, int]) -> str:
    """Estimate market concentration."""
    if not by_sponsor:
        return "Unknown"

    total = sum(by_sponsor.values())
    top_3 = sum(sorted(by_sponsor.values(), reverse=True)[:3])
    concentration = top_3 / total if total > 0 else 0

    if concentration > 0.6:
        return "High - Top 3 sponsors dominate"
    elif concentration > 0.4:
        return "Moderate - Some concentration"
    else:
        return "Low - Fragmented market"
