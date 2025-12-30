"""Tool 3: match_patient_to_trials - Patient-centric trial matching."""

import re
from typing import Any

from core.api_client import get_api_client, APIError
from core.pagination import PaginationHandler
from core.models import MatchStrictness, EligibilityStatus, PatientProfile
from config import FIELDS_STANDARD
from utils.metrics import extract_trial_summary
from utils.formatting import format_eligibility


async def match_patient_to_trials(
    age: int,
    gender: str,
    primary_condition: str,
    secondary_conditions: list[str] | None = None,
    location_country: str | None = None,
    location_city: str | None = None,
    location_state: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    max_travel_distance_km: float = 100.0,
    excluded_interventions: list[str] | None = None,
    preferred_phases: list[str] | None = None,
    must_be_recruiting: bool = True,
    match_strictness: str = "BALANCED",
    explain_matches: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Match a patient profile to eligible clinical trials.

    Provides patient-centric trial matching with eligibility scoring
    and explanations for why a patient may or may not qualify.

    Args:
        age: Patient's current age
        gender: Patient's gender (MALE, FEMALE, ALL)
        primary_condition: Primary diagnosed condition
        secondary_conditions: Comorbidities
        location_country: Patient's country
        location_city: Patient's city
        location_state: Patient's state/province
        latitude: Latitude for proximity search
        longitude: Longitude for proximity search
        max_travel_distance_km: Maximum travel distance
        excluded_interventions: Interventions to exclude (allergies, etc.)
        preferred_phases: Preferred trial phases
        must_be_recruiting: Only include recruiting trials
        match_strictness: STRICT, BALANCED, or LENIENT
        explain_matches: Provide eligibility explanations
        limit: Maximum matching trials to return

    Returns:
        Matched trials with eligibility scores and explanations
    """
    client = get_api_client()
    pagination = PaginationHandler(client)

    # Build search query
    params: dict[str, Any] = {
        "query.cond": primary_condition,
        "fields": "|".join(FIELDS_STANDARD),
    }

    # Status filter
    if must_be_recruiting:
        params["filter.overallStatus"] = "RECRUITING|ENROLLING_BY_INVITATION"

    # Location filter
    if latitude is not None and longitude is not None:
        params["filter.geo"] = f"distance({latitude},{longitude},{max_travel_distance_km}km)"
    elif location_country:
        location_parts = []
        if location_city:
            location_parts.append(f'AREA[LocationCity]"{location_city}"')
        if location_state:
            location_parts.append(f'AREA[LocationState]"{location_state}"')
        if location_country:
            location_parts.append(f'AREA[LocationCountry]"{location_country}"')
        
        if location_parts:
            params["filter.advanced"] = "SEARCH[Location](" + " AND ".join(location_parts) + ")"

    # Phase filter
    if preferred_phases:
        phase_filter = "(" + " OR ".join(f"AREA[Phase]{p.upper()}" for p in preferred_phases) + ")"
        if "filter.advanced" in params:
            params["filter.advanced"] += f" AND {phase_filter}"
        else:
            params["filter.advanced"] = phase_filter

    # Determine match strictness
    try:
        strictness = MatchStrictness(match_strictness.upper())
    except ValueError:
        strictness = MatchStrictness.BALANCED

    # Execute search
    try:
        response = await pagination.fetch_all_pages(
            query_params=params,
            max_results=limit * 3,  # Fetch extra for filtering/scoring
            count_total=True,
        )
    except APIError as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "matched_trials": [],
        }

    # Score each trial
    matched_trials = []
    patient_age_years = age
    patient_gender = gender.upper()

    for study in response.get("studies", []):
        summary = extract_trial_summary(study)
        protocol = study.get("protocolSection", {})
        eligibility_module = protocol.get("eligibilityModule", {})

        # Calculate eligibility score
        score, status, explanation, issues = _calculate_eligibility(
            patient_age_years=patient_age_years,
            patient_gender=patient_gender,
            eligibility_module=eligibility_module,
            excluded_interventions=excluded_interventions or [],
            interventions=summary.get("interventions", []),
            strictness=strictness,
        )

        # Apply strictness filter
        if strictness == MatchStrictness.STRICT and status != EligibilityStatus.LIKELY_ELIGIBLE:
            continue
        elif strictness == MatchStrictness.BALANCED and status == EligibilityStatus.LIKELY_INELIGIBLE:
            continue

        # Calculate distance if location available
        distance_km = None
        locations = protocol.get("contactsLocationsModule", {}).get("locations", [])
        if locations and (location_city or location_country):
            # Simple distance estimation based on matching location
            for loc in locations:
                if location_city and loc.get("city", "").lower() == location_city.lower():
                    distance_km = 0
                    break
                elif location_state and loc.get("state", "").lower() == location_state.lower():
                    distance_km = 50  # Approximate
                    break
                elif location_country and loc.get("country", "").lower() == location_country.lower():
                    distance_km = 100  # Approximate
                    break

        # Build match result
        match_result = {
            "trial": summary,
            "match_score": round(score, 1),
            "eligibility_status": status.value,
        }

        if explain_matches:
            match_result["eligibility_explanation"] = explanation
            if issues:
                match_result["potential_issues"] = issues

        if distance_km is not None:
            match_result["distance_km"] = distance_km

        # Add next steps
        match_result["next_steps"] = _generate_next_steps(study, status)

        matched_trials.append(match_result)

    # Sort by match score
    matched_trials.sort(key=lambda x: x["match_score"], reverse=True)
    matched_trials = matched_trials[:limit]

    # Alternative suggestions if few matches
    alternative_conditions = []
    if len(matched_trials) < 5 and secondary_conditions:
        alternative_conditions = secondary_conditions[:3]

    result = {
        "status": "SUCCESS",
        "patient_summary": {
            "age": age,
            "gender": gender,
            "primary_condition": primary_condition,
            "location": location_country or location_city or "Not specified",
        },
        "matched_trials": matched_trials,
        "total_matches": len(matched_trials),
        "search_criteria": {
            "strictness": strictness.value,
            "recruiting_only": must_be_recruiting,
            "max_distance_km": max_travel_distance_km if latitude else None,
        },
    }

    if alternative_conditions:
        result["alternative_conditions"] = alternative_conditions
        result["suggestion"] = (
            "Few matches found. Consider searching for trials related to: "
            + ", ".join(alternative_conditions)
        )

    # Add disclaimer
    result["disclaimer"] = (
        "This tool provides informational matching only. Always consult with a healthcare "
        "provider before enrolling in any clinical trial. Eligibility determination is "
        "made by the study team, not this tool."
    )

    return result


def _calculate_eligibility(
    patient_age_years: int,
    patient_gender: str,
    eligibility_module: dict[str, Any],
    excluded_interventions: list[str],
    interventions: list[str],
    strictness: MatchStrictness,
) -> tuple[float, EligibilityStatus, str, list[str]]:
    """Calculate eligibility score and status for a patient."""
    score = 100.0
    issues = []
    explanation_parts = []

    # Check age eligibility
    min_age_str = eligibility_module.get("minimumAge", "")
    max_age_str = eligibility_module.get("maximumAge", "")

    min_age_years = _parse_age(min_age_str)
    max_age_years = _parse_age(max_age_str)

    if min_age_years is not None and patient_age_years < min_age_years:
        score -= 40
        issues.append(f"Below minimum age ({min_age_str})")
    elif max_age_years is not None and patient_age_years > max_age_years:
        score -= 40
        issues.append(f"Above maximum age ({max_age_str})")
    else:
        explanation_parts.append("Age requirement met")

    # Check sex eligibility
    trial_sex = eligibility_module.get("sex", "ALL").upper()
    if trial_sex != "ALL" and trial_sex != patient_gender:
        score -= 50
        issues.append(f"Trial requires {trial_sex} participants")
    else:
        explanation_parts.append("Gender requirement met")

    # Check excluded interventions
    if excluded_interventions and interventions:
        excluded_lower = [e.lower() for e in excluded_interventions]
        for intervention in interventions:
            if intervention.lower() in excluded_lower:
                score -= 30
                issues.append(f"Contains excluded intervention: {intervention}")
                break

    # Check healthy volunteers
    healthy_vol = eligibility_module.get("healthyVolunteers", "No")
    if healthy_vol == "Yes":
        explanation_parts.append("Accepts volunteers (may require specific condition)")

    # Determine status
    if score >= 80:
        status = EligibilityStatus.LIKELY_ELIGIBLE
    elif score >= 60:
        status = EligibilityStatus.POSSIBLY_ELIGIBLE
    elif score >= 40:
        status = EligibilityStatus.UNCLEAR
    else:
        status = EligibilityStatus.LIKELY_INELIGIBLE

    # Build explanation
    if issues:
        explanation = "Issues found: " + "; ".join(issues)
        if explanation_parts:
            explanation += ". Meets: " + ", ".join(explanation_parts)
    elif explanation_parts:
        explanation = "Eligibility criteria appear satisfied: " + ", ".join(explanation_parts)
    else:
        explanation = "Unable to determine eligibility from available data"

    return score, status, explanation, issues


def _parse_age(age_str: str) -> int | None:
    """Parse age string to years."""
    if not age_str:
        return None

    age_str = age_str.lower().strip()

    # Match patterns like "18 years", "18 Years", "18years", etc.
    match = re.match(r"(\d+)\s*(years?|yrs?|y)?", age_str)
    if match:
        return int(match.group(1))

    # Handle months
    match = re.match(r"(\d+)\s*months?", age_str)
    if match:
        return int(match.group(1)) // 12

    # Handle "N/A" or similar
    if "n/a" in age_str or "no limit" in age_str:
        return None

    return None


def _generate_next_steps(study: dict[str, Any], status: EligibilityStatus) -> list[str]:
    """Generate next steps for a patient."""
    steps = []
    protocol = study.get("protocolSection", {})
    contacts = protocol.get("contactsLocationsModule", {})

    if status in (EligibilityStatus.LIKELY_ELIGIBLE, EligibilityStatus.POSSIBLY_ELIGIBLE):
        steps.append("Review the full eligibility criteria with your doctor")

        # Add contact info if available
        central_contacts = contacts.get("centralContacts", [])
        if central_contacts:
            contact = central_contacts[0]
            if contact.get("phone"):
                steps.append(f"Contact study team: {contact.get('phone')}")
            if contact.get("email"):
                steps.append(f"Email: {contact.get('email')}")

        locations = contacts.get("locations", [])
        if locations:
            steps.append(f"Visit one of {len(locations)} study site(s) for screening")

        steps.append("Bring your medical records to the screening appointment")

    elif status == EligibilityStatus.UNCLEAR:
        steps.append("Discuss eligibility with your healthcare provider")
        steps.append("Contact the study team for clarification")

    else:
        steps.append("You may not qualify, but discuss with your doctor")
        steps.append("Consider asking about similar trials")

    return steps
