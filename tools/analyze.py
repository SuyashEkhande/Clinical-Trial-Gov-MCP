"""Tools for trial analysis: analyze_trial_details, find_similar_trials, analyze_trial_outcomes."""

from typing import Any

from core.api_client import get_api_client, APIError, APINotFoundError
from core.pagination import PaginationHandler
from core.models import AnalysisDepth, SimilarityDimension
from config import FIELDS_SUMMARY, FIELDS_STANDARD, FIELDS_COMPREHENSIVE
from utils.metrics import (
    extract_trial_summary,
    compute_trial_maturity,
    compute_enrollment_pace,
    compute_completion_likelihood,
    compute_days_since_start,
    compute_days_to_completion,
)
from utils.formatting import format_eligibility


async def analyze_trial_details(
    nct_id: str | None = None,
    trial_ids: list[str] | None = None,
    analysis_depth: str = "STANDARD",
    include_results: bool = True,
    include_references: bool = True,
    compute_metrics: bool = True,
    return_format: str = "STRUCTURED",
) -> dict[str, Any]:
    """
    Deep dive analysis of one or more clinical trials.

    Provides comprehensive trial information with computed metrics for
    trial maturity, enrollment pace, and completion likelihood.

    Args:
        nct_id: Single NCT identifier (e.g., "NCT04123456")
        trial_ids: List of NCT identifiers for multi-trial analysis
        analysis_depth: SUMMARY, STANDARD, or COMPREHENSIVE
        include_results: Fetch results section if available
        include_references: Fetch publication/PubMed links
        compute_metrics: Add computed metrics (maturity, pace, likelihood)
        return_format: STRUCTURED, MARKDOWN, or TABLE

    Returns:
        Detailed trial analysis with enriched data
    """
    client = get_api_client()

    # Determine which trials to analyze
    ids_to_fetch = []
    if nct_id:
        ids_to_fetch.append(nct_id.upper())
    if trial_ids:
        ids_to_fetch.extend([tid.upper() for tid in trial_ids])

    if not ids_to_fetch:
        return {
            "status": "ERROR",
            "message": "Please provide either nct_id or trial_ids",
        }

    # Determine fields based on depth
    try:
        depth = AnalysisDepth(analysis_depth.upper())
    except ValueError:
        depth = AnalysisDepth.STANDARD

    if depth == AnalysisDepth.SUMMARY:
        fields = FIELDS_SUMMARY
    elif depth == AnalysisDepth.COMPREHENSIVE:
        fields = FIELDS_COMPREHENSIVE
    else:
        fields = FIELDS_STANDARD

    # Fetch trials
    trials_data = []
    errors = []

    for tid in ids_to_fetch:
        try:
            study = await client.get_study(tid, fields=fields if depth != AnalysisDepth.COMPREHENSIVE else None)
            trial_analysis = _build_trial_analysis(study, compute_metrics, include_results, include_references)
            trials_data.append(trial_analysis)
        except APINotFoundError:
            errors.append(f"Trial {tid} not found")
        except APIError as e:
            errors.append(f"Error fetching {tid}: {str(e)}")

    result = {
        "status": "SUCCESS" if trials_data else "ERROR",
        "trials": trials_data,
        "total_analyzed": len(trials_data),
        "analysis_depth": depth.value,
    }

    if errors:
        result["errors"] = errors
        if not trials_data:
            result["status"] = "ERROR"

    if len(trials_data) == 1:
        # Flatten for single trial
        result["trial"] = trials_data[0]

    return result


def _build_trial_analysis(
    study: dict[str, Any],
    compute_metrics: bool,
    include_results: bool,
    include_references: bool,
) -> dict[str, Any]:
    """Build detailed analysis for a single trial."""
    protocol = study.get("protocolSection", {})
    results_section = study.get("resultsSection", {})
    derived = study.get("derivedSection", {})

    # Basic summary
    summary = extract_trial_summary(study)

    # Eligibility analysis
    eligibility_module = protocol.get("eligibilityModule", {})
    eligibility_text = eligibility_module.get("eligibilityCriteria", "")
    eligibility_parsed = format_eligibility(eligibility_text)

    eligibility_analysis = {
        "criteria_text": eligibility_text[:2000] if eligibility_text else "",
        "inclusion_criteria": eligibility_parsed["inclusion"][:10],
        "exclusion_criteria": eligibility_parsed["exclusion"][:10],
        "age_range": f"{eligibility_module.get('minimumAge', 'N/A')} - {eligibility_module.get('maximumAge', 'N/A')}",
        "sex": eligibility_module.get("sex", "ALL"),
        "accepts_healthy": eligibility_module.get("healthyVolunteers", "No") == "Yes",
    }

    # Arm/intervention mapping
    arms_module = protocol.get("armsInterventionsModule", {})
    arm_intervention_map = []
    for arm in arms_module.get("armGroups", []):
        arm_intervention_map.append({
            "arm_label": arm.get("label", ""),
            "arm_type": arm.get("type", ""),
            "description": arm.get("description", "")[:500] if arm.get("description") else "",
            "interventions": arm.get("interventionNames", []),
        })

    # Outcome measures
    outcomes_module = protocol.get("outcomesModule", {})
    outcome_measures = []
    for outcome_type in ["primaryOutcomes", "secondaryOutcomes"]:
        for outcome in outcomes_module.get(outcome_type, []):
            outcome_measures.append({
                "type": "PRIMARY" if outcome_type == "primaryOutcomes" else "SECONDARY",
                "measure": outcome.get("measure", ""),
                "description": outcome.get("description", "")[:300] if outcome.get("description") else "",
                "time_frame": outcome.get("timeFrame", ""),
            })

    # Location summary
    contacts_module = protocol.get("contactsLocationsModule", {})
    locations = contacts_module.get("locations", [])
    location_summary = {
        "total_sites": len(locations),
        "countries": list(set(loc.get("country", "") for loc in locations if loc.get("country"))),
        "sample_sites": [
            {
                "facility": loc.get("facility", ""),
                "city": loc.get("city", ""),
                "state": loc.get("state", ""),
                "country": loc.get("country", ""),
                "status": loc.get("status", ""),
            }
            for loc in locations[:5]
        ],
    }

    # Sponsor info
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    sponsor_info = {
        "lead_sponsor": sponsor_module.get("leadSponsor", {}).get("name", ""),
        "sponsor_class": sponsor_module.get("leadSponsor", {}).get("class", ""),
        "collaborators": [
            c.get("name", "") for c in sponsor_module.get("collaborators", [])
        ],
    }

    # Build result
    analysis = {
        **summary,
        "eligibility_analysis": eligibility_analysis,
        "arm_intervention_map": arm_intervention_map,
        "outcome_measures": outcome_measures[:10],
        "location_summary": location_summary,
        "sponsor_info": sponsor_info,
    }

    # Computed metrics
    if compute_metrics:
        analysis["key_metrics"] = {
            "trial_maturity": compute_trial_maturity(study),
            "enrollment_pace": compute_enrollment_pace(study),
            "completion_likelihood": compute_completion_likelihood(study),
            "days_since_start": compute_days_since_start(study),
            "days_to_completion": compute_days_to_completion(study),
        }

    # Results data
    if include_results and results_section:
        analysis["results_status"] = {
            "has_results": study.get("hasResults", False),
            "results_first_posted": protocol.get("statusModule", {}).get("resultsFirstPostDateStruct", {}).get("date"),
        }

    # References
    if include_references:
        refs_module = protocol.get("referencesModule", {})
        references = refs_module.get("references", [])[:5]
        analysis["references"] = [
            {
                "pmid": ref.get("pmid", ""),
                "citation": ref.get("citation", "")[:300] if ref.get("citation") else "",
                "type": ref.get("type", ""),
            }
            for ref in references
        ]

    # MESH terms
    conditions_mesh = derived.get("conditionMeshes", [])
    interventions_mesh = derived.get("interventionMeshes", [])
    analysis["mesh_terms"] = {
        "conditions": [m.get("term", "") for m in conditions_mesh[:10]],
        "interventions": [m.get("term", "") for m in interventions_mesh[:10]],
    }

    return analysis


async def find_similar_trials(
    reference_nct_id: str,
    similarity_dimensions: list[str] | None = None,
    similarity_threshold: float = 60.0,
    exclude_same_sponsor: bool = False,
    exclude_completed: bool = True,
    limit: int = 20,
    include_enrollment_comparison: bool = True,
) -> dict[str, Any]:
    """
    Find trials similar to a reference trial for competitive analysis.

    Args:
        reference_nct_id: NCT ID of the reference trial
        similarity_dimensions: What to match on (CONDITION, INTERVENTION, PHASE, etc.)
        similarity_threshold: Minimum similarity score (0-100)
        exclude_same_sponsor: Filter out trials from same sponsor
        exclude_completed: Only include active/recruiting trials
        limit: Maximum similar trials to return
        include_enrollment_comparison: Compare enrollment numbers

    Returns:
        Similar trials with scoring and competitive landscape analysis
    """
    client = get_api_client()
    pagination = PaginationHandler(client)

    # Get reference trial
    try:
        ref_study = await client.get_study(reference_nct_id.upper())
    except APINotFoundError:
        return {
            "status": "ERROR",
            "message": f"Reference trial {reference_nct_id} not found",
        }
    except APIError as e:
        return {
            "status": "ERROR",
            "message": str(e),
        }

    ref_summary = extract_trial_summary(ref_study)
    ref_protocol = ref_study.get("protocolSection", {})

    # Default dimensions
    if not similarity_dimensions:
        similarity_dimensions = ["CONDITION", "INTERVENTION", "PHASE", "STUDY_TYPE"]

    # Build search query based on reference trial
    query_parts = []

    if "CONDITION" in similarity_dimensions and ref_summary.get("conditions"):
        conditions = ref_summary["conditions"][:3]
        cond_query = " OR ".join(f'AREA[Condition]"{c}"' for c in conditions)
        query_parts.append(f"({cond_query})")

    if "INTERVENTION" in similarity_dimensions and ref_summary.get("interventions"):
        interventions = ref_summary["interventions"][:3]
        intr_query = " OR ".join(f'AREA[InterventionName]"{i}"' for i in interventions)
        query_parts.append(f"({intr_query})")

    if "PHASE" in similarity_dimensions and ref_summary.get("phase"):
        phases = ref_summary["phase"]
        phase_query = " OR ".join(f"AREA[Phase]{p}" for p in phases)
        query_parts.append(f"({phase_query})")

    if not query_parts:
        return {
            "status": "ERROR",
            "message": "Reference trial lacks searchable conditions or interventions",
        }

    # Build search params
    params: dict[str, Any] = {
        "filter.advanced": " OR ".join(query_parts),
        "fields": "|".join(FIELDS_STANDARD),
    }

    # Status filter
    if exclude_completed:
        params["filter.overallStatus"] = "RECRUITING|ACTIVE_NOT_RECRUITING|NOT_YET_RECRUITING|ENROLLING_BY_INVITATION"

    # Execute search
    try:
        response = await pagination.fetch_all_pages(
            query_params=params,
            max_results=limit * 3,  # Fetch extra for filtering
            count_total=True,
        )
    except APIError as e:
        return {
            "status": "ERROR",
            "message": str(e),
        }

    # Score and filter results
    similar_trials = []
    ref_sponsor = ref_summary.get("sponsor", "").lower()

    for study in response.get("studies", []):
        summary = extract_trial_summary(study)

        # Skip reference trial itself
        if summary["nct_id"] == reference_nct_id.upper():
            continue

        # Skip same sponsor if requested
        if exclude_same_sponsor and summary.get("sponsor", "").lower() == ref_sponsor:
            continue

        # Calculate similarity score
        score, matching_dims, differences = _calculate_similarity(
            ref_summary, summary, similarity_dimensions
        )

        if score >= similarity_threshold:
            similar_trial = {
                "trial": summary,
                "similarity_score": round(score, 1),
                "matching_dimensions": matching_dims,
                "key_differences": differences,
            }

            if include_enrollment_comparison:
                ref_enrollment = ref_summary.get("enrollment") or 0
                trial_enrollment = summary.get("enrollment") or 0
                similar_trial["enrollment_comparison"] = {
                    "reference_enrollment": ref_enrollment,
                    "trial_enrollment": trial_enrollment,
                    "difference": trial_enrollment - ref_enrollment,
                }

            similar_trials.append(similar_trial)

    # Sort by similarity score
    similar_trials.sort(key=lambda x: x["similarity_score"], reverse=True)
    similar_trials = similar_trials[:limit]

    # Build competitive landscape
    all_trials = [t["trial"] for t in similar_trials]
    competitive_landscape = {
        "total_similar": len(similar_trials),
        "active_competitors": sum(1 for t in all_trials if t.get("status") == "RECRUITING"),
        "phase_distribution": _count_by_field(all_trials, "phase"),
        "top_sponsors": _count_by_field(all_trials, "sponsor")[:5],
    }

    return {
        "status": "SUCCESS",
        "reference_trial": ref_summary,
        "similar_trials": similar_trials,
        "competitive_landscape": competitive_landscape,
        "dimensions_used": similarity_dimensions,
    }


def _calculate_similarity(
    ref: dict[str, Any],
    trial: dict[str, Any],
    dimensions: list[str],
) -> tuple[float, list[str], list[str]]:
    """Calculate similarity score between two trials."""
    total_weight = 0
    matched_weight = 0
    matching_dims = []
    differences = []

    weights = {
        "CONDITION": 30,
        "INTERVENTION": 30,
        "PHASE": 15,
        "STUDY_TYPE": 10,
        "SPONSOR": 5,
        "LOCATION": 5,
        "ENROLLMENT_TARGET": 5,
    }

    for dim in dimensions:
        weight = weights.get(dim, 10)
        total_weight += weight

        if dim == "CONDITION":
            ref_conds = set(c.lower() for c in (ref.get("conditions") or []))
            trial_conds = set(c.lower() for c in (trial.get("conditions") or []))
            if ref_conds & trial_conds:
                overlap = len(ref_conds & trial_conds) / max(len(ref_conds | trial_conds), 1)
                matched_weight += weight * overlap
                matching_dims.append(f"Conditions: {', '.join(ref_conds & trial_conds)}")
            else:
                differences.append(f"Different conditions: {', '.join(trial_conds)[:50]}")

        elif dim == "INTERVENTION":
            ref_intrs = set(i.lower() for i in (ref.get("interventions") or []))
            trial_intrs = set(i.lower() for i in (trial.get("interventions") or []))
            if ref_intrs & trial_intrs:
                overlap = len(ref_intrs & trial_intrs) / max(len(ref_intrs | trial_intrs), 1)
                matched_weight += weight * overlap
                matching_dims.append(f"Interventions: {', '.join(ref_intrs & trial_intrs)}")
            else:
                differences.append(f"Different interventions: {', '.join(trial_intrs)[:50]}")

        elif dim == "PHASE":
            ref_phases = set(ref.get("phase") or [])
            trial_phases = set(trial.get("phase") or [])
            if ref_phases & trial_phases:
                matched_weight += weight
                matching_dims.append(f"Phase: {', '.join(ref_phases & trial_phases)}")
            else:
                differences.append(f"Different phase: {', '.join(trial_phases)}")

        elif dim == "STUDY_TYPE":
            if ref.get("study_type") == trial.get("study_type"):
                matched_weight += weight
                matching_dims.append(f"Study type: {trial.get('study_type')}")

        elif dim == "SPONSOR":
            if ref.get("sponsor", "").lower() == trial.get("sponsor", "").lower():
                matched_weight += weight
                matching_dims.append("Same sponsor")
            else:
                differences.append(f"Different sponsor: {trial.get('sponsor')}")

    score = (matched_weight / total_weight * 100) if total_weight > 0 else 0
    return score, matching_dims, differences


def _count_by_field(trials: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    """Count trials by a specific field."""
    counts: dict[str, int] = {}
    for trial in trials:
        value = trial.get(field)
        if isinstance(value, list):
            for v in value:
                counts[str(v)] = counts.get(str(v), 0) + 1
        elif value:
            counts[str(value)] = counts.get(str(value), 0) + 1

    return [
        {"value": k, "count": v}
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


async def analyze_trial_outcomes(
    nct_id: str | None = None,
    trial_ids: list[str] | None = None,
    outcome_categories: list[str] | None = None,
    include_results_data: bool = True,
    comparison_mode: str = "SINGLE",
) -> dict[str, Any]:
    """
    Extract and analyze outcome measures from clinical trials.

    Args:
        nct_id: Single NCT identifier
        trial_ids: List of NCT identifiers for comparison
        outcome_categories: Filter by PRIMARY, SECONDARY, OTHER
        include_results_data: Fetch posted results if available
        comparison_mode: SINGLE, COMPARATIVE, or BENCHMARK

    Returns:
        Outcome measures with statistical analyses if available
    """
    client = get_api_client()

    # Determine trials to analyze
    ids_to_fetch = []
    if nct_id:
        ids_to_fetch.append(nct_id.upper())
    if trial_ids:
        ids_to_fetch.extend([tid.upper() for tid in trial_ids])

    if not ids_to_fetch:
        return {
            "status": "ERROR",
            "message": "Please provide nct_id or trial_ids",
        }

    all_outcomes = []

    for tid in ids_to_fetch:
        try:
            study = await client.get_study(tid)
            protocol = study.get("protocolSection", {})
            results = study.get("resultsSection", {})

            outcomes_module = protocol.get("outcomesModule", {})

            trial_outcomes = {
                "nct_id": tid,
                "has_results": study.get("hasResults", False),
                "outcomes": [],
            }

            # Extract primary outcomes
            for outcome in outcomes_module.get("primaryOutcomes", []):
                if not outcome_categories or "PRIMARY" in outcome_categories:
                    trial_outcomes["outcomes"].append({
                        "type": "PRIMARY",
                        "measure": outcome.get("measure", ""),
                        "description": outcome.get("description", ""),
                        "time_frame": outcome.get("timeFrame", ""),
                    })

            # Extract secondary outcomes
            for outcome in outcomes_module.get("secondaryOutcomes", []):
                if not outcome_categories or "SECONDARY" in outcome_categories:
                    trial_outcomes["outcomes"].append({
                        "type": "SECONDARY",
                        "measure": outcome.get("measure", ""),
                        "description": outcome.get("description", ""),
                        "time_frame": outcome.get("timeFrame", ""),
                    })

            # Extract other outcomes
            for outcome in outcomes_module.get("otherOutcomes", []):
                if not outcome_categories or "OTHER" in outcome_categories:
                    trial_outcomes["outcomes"].append({
                        "type": "OTHER",
                        "measure": outcome.get("measure", ""),
                        "description": outcome.get("description", ""),
                        "time_frame": outcome.get("timeFrame", ""),
                    })

            # Results data if available
            if include_results_data and results:
                outcome_measures = results.get("outcomeMeasuresModule", {})
                trial_outcomes["results_data"] = {
                    "outcome_measures": len(outcome_measures.get("outcomeMeasures", [])),
                    "has_statistical_analysis": "moreInfoModule" in results,
                }

                # Adverse events summary
                adverse = results.get("adverseEventsModule", {})
                if adverse:
                    trial_outcomes["adverse_events_summary"] = {
                        "frequency_threshold": adverse.get("frequencyThreshold", ""),
                        "time_frame": adverse.get("timeFrame", ""),
                        "description": adverse.get("description", "")[:500] if adverse.get("description") else "",
                    }

            all_outcomes.append(trial_outcomes)

        except APINotFoundError:
            all_outcomes.append({
                "nct_id": tid,
                "error": "Trial not found",
            })
        except APIError as e:
            all_outcomes.append({
                "nct_id": tid,
                "error": str(e),
            })

    # Build comparison if multiple trials
    result = {
        "status": "SUCCESS",
        "trials_analyzed": len(ids_to_fetch),
        "outcomes_by_trial": all_outcomes,
    }

    if len(all_outcomes) > 1 and comparison_mode == "COMPARATIVE":
        # Find common outcomes
        all_measures = []
        for trial in all_outcomes:
            for outcome in trial.get("outcomes", []):
                all_measures.append(outcome.get("measure", "").lower())

        from collections import Counter
        measure_counts = Counter(all_measures)
        common_outcomes = [m for m, c in measure_counts.items() if c > 1]

        result["comparison_analysis"] = {
            "common_outcome_measures": common_outcomes[:10],
            "total_unique_measures": len(set(all_measures)),
        }

    return result
