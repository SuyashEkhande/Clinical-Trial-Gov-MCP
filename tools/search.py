"""Tool 1: search_clinical_trials - Intelligent trial discovery with natural language support."""

import time
from typing import Any

from core.api_client import get_api_client, APIError
from core.pagination import PaginationHandler
from core.essie_translator import get_translator
from core.models import OverallStatus, Phase, StudyType, InterventionType
from config import FIELDS_SUMMARY, DEFAULT_PAGE_SIZE
from utils.metrics import extract_trial_summary, compute_trial_maturity, compute_enrollment_pace


async def search_clinical_trials(
    query: str | None = None,
    disease_condition: str | None = None,
    intervention_type: str | None = None,
    intervention_name: str | None = None,
    trial_phase: list[str] | None = None,
    enrollment_status: list[str] | None = None,
    study_type: str | None = None,
    location_country: str | None = None,
    location_city: str | None = None,
    location_state: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    min_age: str | None = None,
    max_age: str | None = None,
    sex: str | None = None,
    healthy_volunteers: bool | None = None,
    sponsor: str | None = None,
    has_results: bool | None = None,
    sort_by: str = "RELEVANCE",
    results_limit: int = 50,
    include_metrics: bool = True,
    return_fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Search clinical trials with natural language and structured filtering.

    This is the primary entry point for trial discovery. Supports natural language
    queries that are automatically translated to the API's Essie query syntax.

    Args:
        query: Natural language or Essie query (e.g., "lung cancer AND pembrolizumab in phase 3")
        disease_condition: Specific disease/condition to search
        intervention_type: Type of intervention (DRUG, DEVICE, BIOLOGICAL, etc.)
        intervention_name: Specific intervention name
        trial_phase: List of phases (PHASE1, PHASE2, PHASE3, PHASE4, EARLY_PHASE1)
        enrollment_status: List of statuses (RECRUITING, COMPLETED, etc.)
        study_type: Study type (INTERVENTIONAL, OBSERVATIONAL, EXPANDED_ACCESS)
        location_country: Country name for location filter
        location_city: City name for location filter
        location_state: State/province for location filter
        latitude: Latitude for proximity search
        longitude: Longitude for proximity search
        radius_km: Radius in kilometers for proximity search
        min_age: Minimum eligible age (e.g., "18 years")
        max_age: Maximum eligible age (e.g., "65 years")
        sex: Sex eligibility (MALE, FEMALE, ALL)
        healthy_volunteers: Whether trial accepts healthy volunteers
        sponsor: Sponsor/organization name
        has_results: Filter for trials with posted results
        sort_by: Sort order (RELEVANCE, ENROLLMENT_COUNT, LAST_UPDATE, COMPLETION_DATE)
        results_limit: Maximum results to return (default 50, max 1000)
        include_metrics: Include computed metrics for each trial
        return_fields: Specific fields to retrieve

    Returns:
        Search results with trials, total count, and search metadata
    """
    start_time = time.time()
    client = get_api_client()
    translator = get_translator()
    pagination = PaginationHandler(client)

    # Build query parameters
    params: dict[str, Any] = {}

    # Handle natural language query
    if query:
        translated = translator.translate(query)
        if "AREA[" in translated or "SEARCH[" in translated:
            params["filter.advanced"] = translated
        else:
            params["query.term"] = query

    # Handle specific condition
    if disease_condition:
        params["query.cond"] = disease_condition

    # Handle intervention
    if intervention_name:
        params["query.intr"] = intervention_name
    elif intervention_type:
        try:
            InterventionType(intervention_type.upper())
            # Add to advanced filter if we have intervention type
            filter_part = f"AREA[InterventionType]{intervention_type.upper()}"
            if "filter.advanced" in params:
                params["filter.advanced"] += f" AND {filter_part}"
            else:
                params["filter.advanced"] = filter_part
        except ValueError:
            pass

    # Handle phase filter
    if trial_phase:
        normalized_phases = []
        for p in trial_phase:
            try:
                phase = Phase(p.upper())
                normalized_phases.append(phase.value)
            except ValueError:
                normalized_phases.append(p.upper())
        
        if normalized_phases:
            phase_filter = "(" + " OR ".join(f"AREA[Phase]{p}" for p in normalized_phases) + ")"
            if "filter.advanced" in params:
                params["filter.advanced"] += f" AND {phase_filter}"
            else:
                params["filter.advanced"] = phase_filter

    # Handle enrollment status
    if enrollment_status:
        normalized_status = []
        for s in enrollment_status:
            try:
                status = OverallStatus(s.upper())
                normalized_status.append(status.value)
            except ValueError:
                normalized_status.append(s.upper())
        params["filter.overallStatus"] = "|".join(normalized_status)

    # Handle study type
    if study_type:
        try:
            st = StudyType(study_type.upper())
            filter_part = f"AREA[StudyType]{st.value}"
            if "filter.advanced" in params:
                params["filter.advanced"] += f" AND {filter_part}"
            else:
                params["filter.advanced"] = filter_part
        except ValueError:
            pass

    # Handle location filters
    if latitude is not None and longitude is not None:
        radius = radius_km or 50
        params["filter.geo"] = f"distance({latitude},{longitude},{radius}km)"
    elif location_country or location_city or location_state:
        location_parts = []
        if location_city:
            location_parts.append(f'AREA[LocationCity]"{location_city}"')
        if location_state:
            location_parts.append(f'AREA[LocationState]"{location_state}"')
        if location_country:
            location_parts.append(f'AREA[LocationCountry]"{location_country}"')
        
        if location_parts:
            location_filter = "SEARCH[Location](" + " AND ".join(location_parts) + ")"
            if "filter.advanced" in params:
                params["filter.advanced"] += f" AND {location_filter}"
            else:
                params["filter.advanced"] = location_filter

    # Handle eligibility criteria
    eligibility_parts = []
    if min_age:
        eligibility_parts.append(f'AREA[MinimumAge]"{min_age}"')
    if max_age:
        eligibility_parts.append(f'AREA[MaximumAge]"{max_age}"')
    if sex:
        eligibility_parts.append(f'AREA[Sex]{sex.upper()}')
    if healthy_volunteers is not None:
        eligibility_parts.append(f'AREA[HealthyVolunteers]{"Yes" if healthy_volunteers else "No"}')

    if eligibility_parts:
        elig_filter = " AND ".join(eligibility_parts)
        if "filter.advanced" in params:
            params["filter.advanced"] += f" AND {elig_filter}"
        else:
            params["filter.advanced"] = elig_filter

    # Handle sponsor
    if sponsor:
        params["query.spons"] = sponsor

    # Handle results filter
    if has_results is not None:
        results_filter = f"AREA[HasResults]{'true' if has_results else 'false'}"
        if "filter.advanced" in params:
            params["filter.advanced"] += f" AND {results_filter}"
        else:
            params["filter.advanced"] = results_filter

    # Handle sorting
    sort_mapping = {
        "RELEVANCE": "@relevance",
        "ENROLLMENT_COUNT": "EnrollmentCount:desc",
        "LAST_UPDATE": "LastUpdatePostDate:desc",
        "COMPLETION_DATE": "CompletionDate:desc",
        "START_DATE": "StartDate:desc",
    }
    params["sort"] = sort_mapping.get(sort_by.upper(), "@relevance")

    # Handle fields
    if return_fields:
        params["fields"] = "|".join(return_fields)
    else:
        params["fields"] = "|".join(FIELDS_SUMMARY)

    # Execute search
    try:
        response = await pagination.fetch_all_pages(
            query_params=params,
            max_results=min(results_limit, 1000),
            page_size=min(DEFAULT_PAGE_SIZE, results_limit),
            count_total=True,
        )

        studies = response.get("studies", [])
        
        # Process each study
        processed_studies = []
        for study in studies:
            summary = extract_trial_summary(study)
            
            if include_metrics:
                summary["computed_metrics"] = {
                    "trial_maturity": compute_trial_maturity(study),
                    "enrollment_pace": compute_enrollment_pace(study),
                }
            
            processed_studies.append(summary)

        execution_time = (time.time() - start_time) * 1000

        return {
            "status": "SUCCESS",
            "studies": processed_studies,
            "total_count": response.get("totalCount"),
            "returned_count": len(processed_studies),
            "execution_time_ms": round(execution_time, 2),
            "query_used": params.get("filter.advanced") or params.get("query.term") or params.get("query.cond", ""),
            "message": f"Found {response.get('totalCount', len(processed_studies))} trials matching your criteria",
        }

    except APIError as e:
        execution_time = (time.time() - start_time) * 1000
        return {
            "status": "ERROR",
            "studies": [],
            "total_count": 0,
            "execution_time_ms": round(execution_time, 2),
            "message": str(e),
            "suggestions": [
                "Try simplifying your search query",
                "Check that phase and status values are valid",
                "Ensure location names are spelled correctly",
            ],
        }
