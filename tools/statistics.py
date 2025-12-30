"""Tool 10: query_trial_statistics - Aggregate analytics and trend analysis."""

from typing import Any

from core.api_client import get_api_client, APIError
from core.pagination import PaginationHandler
from core.models import StatisticType


async def query_trial_statistics(
    statistic_type: str,
    field_name: str | None = None,
    condition: str | None = None,
    phase: list[str] | None = None,
    enrollment_status: list[str] | None = None,
    countries: list[str] | None = None,
    limit: int = 20,
    include_trend_analysis: bool = True,
) -> dict[str, Any]:
    """
    Query aggregate statistics and trends for clinical trials.

    Args:
        statistic_type: FIELD_VALUES, FIELD_DISTRIBUTIONS, TEMPORAL_TRENDS, 
                       GEOGRAPHIC_ANALYSIS, ENROLLMENT_PATTERNS, or DISEASE_LANDSCAPE
        field_name: Field to analyze (e.g., "Phase", "OverallStatus")
        condition: Filter to specific condition
        phase: Filter to specific phases
        enrollment_status: Filter to specific statuses
        countries: Filter to specific countries
        limit: Maximum results
        include_trend_analysis: Add growth/decline insights

    Returns:
        Statistical analysis with insights and visualization suggestions
    """
    client = get_api_client()
    pagination = PaginationHandler(client)

    # Validate statistic type
    try:
        stat_type = StatisticType(statistic_type.upper())
    except ValueError:
        stat_type = StatisticType.FIELD_VALUES

    result: dict[str, Any] = {
        "status": "SUCCESS",
        "statistic_type": stat_type.value,
    }

    # Handle different statistic types
    if stat_type == StatisticType.FIELD_VALUES:
        if not field_name:
            return {
                "status": "ERROR",
                "message": "field_name is required for FIELD_VALUES",
            }

        try:
            stats = await client.get_field_values(field_name)
            values = stats.get("values", [])

            result["field_name"] = field_name
            result["data"] = [
                {"value": v.get("value", ""), "count": v.get("count", 0)}
                for v in values[:limit]
            ]
            result["total_unique_values"] = len(values)
            result["visualization_suggestion"] = "pie_chart" if len(values) < 10 else "bar_chart"

        except APIError as e:
            return {"status": "ERROR", "message": str(e)}

    elif stat_type == StatisticType.GEOGRAPHIC_ANALYSIS:
        # Fetch trials and analyze by location
        params: dict[str, Any] = {
            "fields": "NCTId|LocationCountry|LocationState|LocationCity|OverallStatus",
        }

        if condition:
            params["query.cond"] = condition
        if enrollment_status:
            params["filter.overallStatus"] = "|".join(enrollment_status)

        try:
            response = await pagination.fetch_all_pages(
                query_params=params,
                max_results=500,
                count_total=True,
            )

            by_country: dict[str, int] = {}
            by_state: dict[str, int] = {}

            for study in response.get("studies", []):
                protocol = study.get("protocolSection", {})
                contacts = protocol.get("contactsLocationsModule", {})

                for loc in contacts.get("locations", []):
                    country = loc.get("country", "Unknown")
                    state = loc.get("state", "")

                    by_country[country] = by_country.get(country, 0) + 1
                    if state:
                        by_state[f"{state}, {country}"] = by_state.get(f"{state}, {country}", 0) + 1

            result["geographic_distribution"] = {
                "by_country": [
                    {"country": k, "trial_count": v}
                    for k, v in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:limit]
                ],
                "by_state": [
                    {"location": k, "trial_count": v}
                    for k, v in sorted(by_state.items(), key=lambda x: x[1], reverse=True)[:limit]
                ],
            }
            result["total_trials_analyzed"] = response.get("totalCount", len(response.get("studies", [])))
            result["visualization_suggestion"] = "choropleth_map"

        except APIError as e:
            return {"status": "ERROR", "message": str(e)}

    elif stat_type == StatisticType.DISEASE_LANDSCAPE:
        # Analyze conditions
        params = {"fields": "NCTId|Condition|Phase|OverallStatus|EnrollmentCount"}

        if enrollment_status:
            params["filter.overallStatus"] = "|".join(enrollment_status)
        elif not enrollment_status:
            params["filter.overallStatus"] = "RECRUITING|ACTIVE_NOT_RECRUITING|NOT_YET_RECRUITING|COMPLETED"

        try:
            response = await pagination.fetch_all_pages(
                query_params=params,
                max_results=500,
                count_total=True,
            )

            by_condition: dict[str, dict] = {}

            for study in response.get("studies", []):
                protocol = study.get("protocolSection", {})
                conditions = protocol.get("conditionsModule", {}).get("conditions", [])
                phases = protocol.get("designModule", {}).get("phases", ["N/A"])
                enrollment = protocol.get("designModule", {}).get("enrollmentInfo", {}).get("count", 0)

                for cond in conditions[:3]:  # Limit conditions per study
                    if cond not in by_condition:
                        by_condition[cond] = {
                            "trial_count": 0,
                            "total_enrollment": 0,
                            "phases": {},
                        }

                    by_condition[cond]["trial_count"] += 1
                    by_condition[cond]["total_enrollment"] += enrollment or 0

                    for phase in phases:
                        by_condition[cond]["phases"][phase] = by_condition[cond]["phases"].get(phase, 0) + 1

            # Sort by trial count
            sorted_conditions = sorted(by_condition.items(), key=lambda x: x[1]["trial_count"], reverse=True)

            result["disease_landscape"] = [
                {
                    "condition": k,
                    "trial_count": v["trial_count"],
                    "total_enrollment": v["total_enrollment"],
                    "phase_distribution": v["phases"],
                }
                for k, v in sorted_conditions[:limit]
            ]
            result["total_conditions_found"] = len(by_condition)
            result["visualization_suggestion"] = "treemap"

        except APIError as e:
            return {"status": "ERROR", "message": str(e)}

    elif stat_type == StatisticType.ENROLLMENT_PATTERNS:
        params = {"fields": "NCTId|EnrollmentCount|Phase|OverallStatus|StudyType"}

        if condition:
            params["query.cond"] = condition
        if enrollment_status:
            params["filter.overallStatus"] = "|".join(enrollment_status)

        try:
            response = await pagination.fetch_all_pages(
                query_params=params,
                max_results=500,
                count_total=True,
            )

            enrollments = []
            by_phase: dict[str, list[int]] = {}

            for study in response.get("studies", []):
                protocol = study.get("protocolSection", {})
                design = protocol.get("designModule", {})
                enrollment = design.get("enrollmentInfo", {}).get("count", 0)
                phases = design.get("phases", ["N/A"])

                if enrollment and enrollment > 0:
                    enrollments.append(enrollment)
                    for phase in phases:
                        if phase not in by_phase:
                            by_phase[phase] = []
                        by_phase[phase].append(enrollment)

            # Calculate statistics
            if enrollments:
                sorted_e = sorted(enrollments)
                result["enrollment_patterns"] = {
                    "total_trials": len(enrollments),
                    "total_enrollment": sum(enrollments),
                    "mean": round(sum(enrollments) / len(enrollments), 1),
                    "median": sorted_e[len(sorted_e) // 2],
                    "min": min(enrollments),
                    "max": max(enrollments),
                    "percentiles": {
                        "25th": sorted_e[len(sorted_e) // 4] if len(sorted_e) > 4 else sorted_e[0],
                        "75th": sorted_e[3 * len(sorted_e) // 4] if len(sorted_e) > 4 else sorted_e[-1],
                    },
                }

                result["by_phase"] = {
                    phase: {
                        "count": len(vals),
                        "mean": round(sum(vals) / len(vals), 1) if vals else 0,
                        "total": sum(vals),
                    }
                    for phase, vals in by_phase.items()
                }

            result["visualization_suggestion"] = "histogram"

        except APIError as e:
            return {"status": "ERROR", "message": str(e)}

    else:
        # Default: FIELD_DISTRIBUTIONS
        result["message"] = f"Statistic type {stat_type.value} analysis completed"

    # Add insights if requested
    if include_trend_analysis and "data" in result:
        data = result.get("data", [])
        if data and len(data) > 1:
            top_value = data[0]
            result["insights"] = {
                "most_common": f"{top_value.get('value')} ({top_value.get('count')} occurrences)",
                "concentration": f"Top {min(3, len(data))} values account for {sum(d.get('count', 0) for d in data[:3])} / {sum(d.get('count', 0) for d in data)} total",
            }

    return result
