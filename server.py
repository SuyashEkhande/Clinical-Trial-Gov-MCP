"""ClinicalTrials.gov MCP Server - Main entry point.

A semantic intelligence layer for clinical trial data, providing 10 advanced
tools for AI agents to discover, analyze, and export clinical trial information.
"""

from fastmcp import FastMCP

from tools.metadata import get_trial_metadata_schema
from tools.search import search_clinical_trials
from tools.analyze import analyze_trial_details, find_similar_trials, analyze_trial_outcomes
from tools.patient_match import match_patient_to_trials
from tools.enrollment import get_enrollment_intelligence
from tools.sponsor import analyze_sponsor_network
from tools.export import export_and_format_trials
from tools.statistics import query_trial_statistics

# Create the MCP server
mcp = FastMCP(
    name="clinicaltrials-mcp",
    instructions="""
    ClinicalTrials.gov MCP Server - A semantic intelligence layer for clinical trial data.
    
    This server provides 10 advanced tools for discovering, analyzing, and exporting
    clinical trial information from ClinicalTrials.gov.
    
    CORE TOOLS:
    - search_clinical_trials: Natural language trial discovery with smart filtering
    - analyze_trial_details: Deep-dive study analysis with computed metrics
    - match_patient_to_trials: Patient-centric trial matching with eligibility scoring
    - get_trial_metadata_schema: Self-documenting API schema discovery
    
    ANALYSIS TOOLS:
    - find_similar_trials: Competitive landscape analysis
    - analyze_trial_outcomes: Outcome measure extraction and comparison
    - get_enrollment_intelligence: Enrollment analytics and market capacity
    
    INTELLIGENCE TOOLS:
    - analyze_sponsor_network: Organization and pipeline analysis
    - export_and_format_trials: Multi-format batch export
    - query_trial_statistics: Aggregate analytics and trends
    
    TIPS:
    - Start with search_clinical_trials for discovery
    - Use get_trial_metadata_schema to learn available fields
    - Natural language queries are automatically translated to API syntax
    - All tools return structured JSON for easy processing
    """,
)


# Register all 10 tools
@mcp.tool()
async def tool_search_clinical_trials(
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
) -> dict:
    """
    Search clinical trials with natural language and structured filtering.
    
    Supports natural language queries like "lung cancer AND pembrolizumab in phase 3"
    that are automatically translated to the API's query syntax.
    
    Args:
        query: Natural language or Essie query
        disease_condition: Specific disease/condition
        intervention_type: DRUG, DEVICE, BIOLOGICAL, etc.
        intervention_name: Specific intervention name
        trial_phase: List of phases (PHASE1, PHASE2, PHASE3, PHASE4)
        enrollment_status: RECRUITING, COMPLETED, etc.
        study_type: INTERVENTIONAL, OBSERVATIONAL
        location_country: Country filter
        location_city: City filter
        location_state: State filter
        latitude/longitude/radius_km: Proximity search
        min_age/max_age: Age eligibility
        sex: MALE, FEMALE, ALL
        healthy_volunteers: Accept healthy volunteers
        sponsor: Sponsor name
        has_results: Filter for trials with posted results
        sort_by: RELEVANCE, ENROLLMENT_COUNT, LAST_UPDATE
        results_limit: Max results (default 50)
        include_metrics: Add computed metrics
        return_fields: Specific fields to retrieve
    """
    return await search_clinical_trials(
        query=query,
        disease_condition=disease_condition,
        intervention_type=intervention_type,
        intervention_name=intervention_name,
        trial_phase=trial_phase,
        enrollment_status=enrollment_status,
        study_type=study_type,
        location_country=location_country,
        location_city=location_city,
        location_state=location_state,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        min_age=min_age,
        max_age=max_age,
        sex=sex,
        healthy_volunteers=healthy_volunteers,
        sponsor=sponsor,
        has_results=has_results,
        sort_by=sort_by,
        results_limit=results_limit,
        include_metrics=include_metrics,
        return_fields=return_fields,
    )


@mcp.tool()
async def tool_analyze_trial_details(
    nct_id: str | None = None,
    trial_ids: list[str] | None = None,
    analysis_depth: str = "STANDARD",
    include_results: bool = True,
    include_references: bool = True,
    compute_metrics: bool = True,
    return_format: str = "STRUCTURED",
) -> dict:
    """
    Deep dive analysis of clinical trials with computed metrics.
    
    Provides comprehensive trial information including eligibility parsing,
    arm/intervention mapping, outcome measures, and computed assessments.
    
    Args:
        nct_id: Single NCT identifier (e.g., "NCT04123456")
        trial_ids: List of NCT identifiers
        analysis_depth: SUMMARY, STANDARD, or COMPREHENSIVE
        include_results: Fetch posted results
        include_references: Fetch publications
        compute_metrics: Add maturity, pace, likelihood metrics
        return_format: STRUCTURED, MARKDOWN, TABLE
    """
    return await analyze_trial_details(
        nct_id=nct_id,
        trial_ids=trial_ids,
        analysis_depth=analysis_depth,
        include_results=include_results,
        include_references=include_references,
        compute_metrics=compute_metrics,
        return_format=return_format,
    )


@mcp.tool()
async def tool_match_patient_to_trials(
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
) -> dict:
    """
    Match a patient profile to eligible clinical trials.
    
    Provides patient-centric matching with eligibility scoring and explanations.
    
    Args:
        age: Patient's current age
        gender: MALE, FEMALE
        primary_condition: Main diagnosed condition
        secondary_conditions: Comorbidities
        location_country/city/state: Patient location
        latitude/longitude: For proximity search
        max_travel_distance_km: Max travel distance
        excluded_interventions: Allergies, exclusions
        preferred_phases: Preferred trial phases
        must_be_recruiting: Only recruiting trials
        match_strictness: STRICT, BALANCED, LENIENT
        explain_matches: Provide explanations
        limit: Max matching trials
    """
    return await match_patient_to_trials(
        age=age,
        gender=gender,
        primary_condition=primary_condition,
        secondary_conditions=secondary_conditions,
        location_country=location_country,
        location_city=location_city,
        location_state=location_state,
        latitude=latitude,
        longitude=longitude,
        max_travel_distance_km=max_travel_distance_km,
        excluded_interventions=excluded_interventions,
        preferred_phases=preferred_phases,
        must_be_recruiting=must_be_recruiting,
        match_strictness=match_strictness,
        explain_matches=explain_matches,
        limit=limit,
    )


@mcp.tool()
async def tool_get_trial_metadata_schema(
    scope: str = "FIELDS",
    include_descriptions: bool = True,
    filter_by_area: str | None = None,
    searchable_only: bool = False,
    include_examples: bool = True,
) -> dict:
    """
    Get the data structure and available search fields.
    
    Self-documenting tool for discovering queryable fields and valid values.
    
    Args:
        scope: FIELDS, SEARCH_AREAS, ENUMS, STATISTICS, or ALL
        include_descriptions: Add field definitions
        filter_by_area: Filter to specific module
        searchable_only: Only searchable fields
        include_examples: Add example queries
    """
    return await get_trial_metadata_schema(
        scope=scope,
        include_descriptions=include_descriptions,
        filter_by_area=filter_by_area,
        searchable_only=searchable_only,
        include_examples=include_examples,
    )


@mcp.tool()
async def tool_find_similar_trials(
    reference_nct_id: str,
    similarity_dimensions: list[str] | None = None,
    similarity_threshold: float = 60.0,
    exclude_same_sponsor: bool = False,
    exclude_completed: bool = True,
    limit: int = 20,
    include_enrollment_comparison: bool = True,
) -> dict:
    """
    Find trials similar to a reference trial for competitive analysis.
    
    Args:
        reference_nct_id: NCT ID of reference trial
        similarity_dimensions: CONDITION, INTERVENTION, PHASE, SPONSOR, etc.
        similarity_threshold: Minimum score 0-100
        exclude_same_sponsor: Filter out same sponsor
        exclude_completed: Only active trials
        limit: Max similar trials
        include_enrollment_comparison: Compare enrollment
    """
    return await find_similar_trials(
        reference_nct_id=reference_nct_id,
        similarity_dimensions=similarity_dimensions,
        similarity_threshold=similarity_threshold,
        exclude_same_sponsor=exclude_same_sponsor,
        exclude_completed=exclude_completed,
        limit=limit,
        include_enrollment_comparison=include_enrollment_comparison,
    )


@mcp.tool()
async def tool_analyze_trial_outcomes(
    nct_id: str | None = None,
    trial_ids: list[str] | None = None,
    outcome_categories: list[str] | None = None,
    include_results_data: bool = True,
    comparison_mode: str = "SINGLE",
) -> dict:
    """
    Extract and analyze outcome measures from trials.
    
    Args:
        nct_id: Single NCT identifier
        trial_ids: List of NCT identifiers
        outcome_categories: PRIMARY, SECONDARY, OTHER
        include_results_data: Fetch posted results
        comparison_mode: SINGLE, COMPARATIVE, BENCHMARK
    """
    return await analyze_trial_outcomes(
        nct_id=nct_id,
        trial_ids=trial_ids,
        outcome_categories=outcome_categories,
        include_results_data=include_results_data,
        comparison_mode=comparison_mode,
    )


@mcp.tool()
async def tool_get_enrollment_intelligence(
    condition: str | None = None,
    intervention_type: str | None = None,
    location_country: str | None = None,
    location_state: str | None = None,
    enrollment_status: list[str] | None = None,
    include_capacity_analysis: bool = True,
    include_velocity_analysis: bool = True,
    include_competitor_summary: bool = False,
    limit: int = 100,
) -> dict:
    """
    Analyze enrollment patterns and market capacity.
    
    Args:
        condition: Disease/condition to analyze
        intervention_type: Filter by intervention
        location_country/state: Geographic focus
        enrollment_status: Trial statuses
        include_capacity_analysis: Estimate open slots
        include_velocity_analysis: Estimate speed
        include_competitor_summary: Rank competitors
        limit: Max trials to analyze
    """
    return await get_enrollment_intelligence(
        condition=condition,
        intervention_type=intervention_type,
        location_country=location_country,
        location_state=location_state,
        enrollment_status=enrollment_status,
        include_capacity_analysis=include_capacity_analysis,
        include_velocity_analysis=include_velocity_analysis,
        include_competitor_summary=include_competitor_summary,
        limit=limit,
    )


@mcp.tool()
async def tool_analyze_sponsor_network(
    sponsor_name: str,
    analysis_scope: str = "ORGANIZATION",
    include_trial_portfolio: bool = True,
    analyze_therapeutic_areas: bool = True,
    analyze_stage_distribution: bool = True,
    analyze_collaboration_patterns: bool = False,
    time_window_years: int | None = None,
    limit: int = 100,
) -> dict:
    """
    Analyze a sponsor's clinical trial portfolio and network.
    
    Args:
        sponsor_name: Organization name
        analysis_scope: ORGANIZATION, NETWORK, ECOSYSTEM
        include_trial_portfolio: Get trial list
        analyze_therapeutic_areas: Group by disease
        analyze_stage_distribution: Phase distribution
        analyze_collaboration_patterns: Map partnerships
        time_window_years: Limit time range
        limit: Max trials
    """
    return await analyze_sponsor_network(
        sponsor_name=sponsor_name,
        analysis_scope=analysis_scope,
        include_trial_portfolio=include_trial_portfolio,
        analyze_therapeutic_areas=analyze_therapeutic_areas,
        analyze_stage_distribution=analyze_stage_distribution,
        analyze_collaboration_patterns=analyze_collaboration_patterns,
        time_window_years=time_window_years,
        limit=limit,
    )


@mcp.tool()
async def tool_export_and_format_trials(
    trial_ids: list[str],
    export_format: str = "JSON",
    fields_to_include: list[str] | None = None,
    include_summary_stats: bool = True,
    grouping_strategy: str | None = None,
    sort_by: str = "AS_PROVIDED",
) -> dict:
    """
    Export clinical trials in multiple formats.
    
    Args:
        trial_ids: List of NCT IDs to export
        export_format: JSON, CSV, MARKDOWN
        fields_to_include: Specific fields
        include_summary_stats: Add statistics
        grouping_strategy: CONDITION, PHASE, SPONSOR, LOCATION
        sort_by: AS_PROVIDED, ENROLLMENT_DESC, START_DATE_DESC
    """
    return await export_and_format_trials(
        trial_ids=trial_ids,
        export_format=export_format,
        fields_to_include=fields_to_include,
        include_summary_stats=include_summary_stats,
        grouping_strategy=grouping_strategy,
        sort_by=sort_by,
    )


@mcp.tool()
async def tool_query_trial_statistics(
    statistic_type: str,
    field_name: str | None = None,
    condition: str | None = None,
    phase: list[str] | None = None,
    enrollment_status: list[str] | None = None,
    countries: list[str] | None = None,
    limit: int = 20,
    include_trend_analysis: bool = True,
) -> dict:
    """
    Query aggregate statistics and trends.
    
    Args:
        statistic_type: FIELD_VALUES, GEOGRAPHIC_ANALYSIS, 
                       DISEASE_LANDSCAPE, ENROLLMENT_PATTERNS
        field_name: Field to analyze
        condition: Filter condition
        phase: Filter phases
        enrollment_status: Filter statuses
        countries: Filter countries
        limit: Max results
        include_trend_analysis: Add insights
    """
    return await query_trial_statistics(
        statistic_type=statistic_type,
        field_name=field_name,
        condition=condition,
        phase=phase,
        enrollment_status=enrollment_status,
        countries=countries,
        limit=limit,
        include_trend_analysis=include_trend_analysis,
    )


def main():
    """Run the MCP server with streamable HTTP transport."""
    mcp.run(transport="http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

