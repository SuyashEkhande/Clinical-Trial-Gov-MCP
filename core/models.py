"""Pydantic models for ClinicalTrials.gov API data and tool parameters."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Enumerations
# ============================================================================


class OverallStatus(str, Enum):
    """Study recruitment status."""

    RECRUITING = "RECRUITING"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    COMPLETED = "COMPLETED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    UNKNOWN = "UNKNOWN"


class Phase(str, Enum):
    """Clinical trial phase."""

    EARLY_PHASE1 = "EARLY_PHASE1"
    PHASE1 = "PHASE1"
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"
    NA = "NA"


class StudyType(str, Enum):
    """Type of clinical study."""

    INTERVENTIONAL = "INTERVENTIONAL"
    OBSERVATIONAL = "OBSERVATIONAL"
    EXPANDED_ACCESS = "EXPANDED_ACCESS"


class InterventionType(str, Enum):
    """Type of intervention."""

    DRUG = "DRUG"
    DEVICE = "DEVICE"
    BIOLOGICAL = "BIOLOGICAL"
    PROCEDURE = "PROCEDURE"
    RADIATION = "RADIATION"
    BEHAVIORAL = "BEHAVIORAL"
    GENETIC = "GENETIC"
    DIETARY_SUPPLEMENT = "DIETARY_SUPPLEMENT"
    COMBINATION_PRODUCT = "COMBINATION_PRODUCT"
    DIAGNOSTIC_TEST = "DIAGNOSTIC_TEST"
    OTHER = "OTHER"


class Sex(str, Enum):
    """Sex eligibility."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    ALL = "ALL"


class AnalysisDepth(str, Enum):
    """Depth of trial analysis."""

    SUMMARY = "SUMMARY"
    STANDARD = "STANDARD"
    COMPREHENSIVE = "COMPREHENSIVE"


class ReturnFormat(str, Enum):
    """Output format for results."""

    STRUCTURED = "STRUCTURED"
    MARKDOWN = "MARKDOWN"
    TABLE = "TABLE"


class ExportFormat(str, Enum):
    """Export file format."""

    JSON = "JSON"
    CSV = "CSV"
    MARKDOWN = "MARKDOWN"


class MatchStrictness(str, Enum):
    """Patient matching strictness."""

    STRICT = "STRICT"
    BALANCED = "BALANCED"
    LENIENT = "LENIENT"


class EligibilityStatus(str, Enum):
    """Patient eligibility status."""

    LIKELY_ELIGIBLE = "LIKELY_ELIGIBLE"
    POSSIBLY_ELIGIBLE = "POSSIBLY_ELIGIBLE"
    UNCLEAR = "UNCLEAR"
    LIKELY_INELIGIBLE = "LIKELY_INELIGIBLE"


class TrialMaturity(str, Enum):
    """Trial maturity stage."""

    EARLY = "EARLY"
    MID = "MID"
    LATE = "LATE"


class SimilarityDimension(str, Enum):
    """Dimensions for trial similarity comparison."""

    CONDITION = "CONDITION"
    INTERVENTION = "INTERVENTION"
    PHASE = "PHASE"
    STUDY_TYPE = "STUDY_TYPE"
    SPONSOR = "SPONSOR"
    LOCATION = "LOCATION"
    ENROLLMENT_TARGET = "ENROLLMENT_TARGET"
    PRIMARY_PURPOSE = "PRIMARY_PURPOSE"


class StatisticType(str, Enum):
    """Type of statistics to query."""

    FIELD_VALUES = "FIELD_VALUES"
    FIELD_DISTRIBUTIONS = "FIELD_DISTRIBUTIONS"
    TEMPORAL_TRENDS = "TEMPORAL_TRENDS"
    GEOGRAPHIC_ANALYSIS = "GEOGRAPHIC_ANALYSIS"
    ENROLLMENT_PATTERNS = "ENROLLMENT_PATTERNS"
    DISEASE_LANDSCAPE = "DISEASE_LANDSCAPE"


class MetadataScope(str, Enum):
    """Scope for metadata schema."""

    FIELDS = "FIELDS"
    SEARCH_AREAS = "SEARCH_AREAS"
    ENUMS = "ENUMS"
    STATISTICS = "STATISTICS"
    ALL = "ALL"


class SponsorClass(str, Enum):
    """Sponsor organization class."""

    NIH = "NIH"
    FED = "FED"
    INDUSTRY = "INDUSTRY"
    INDIV = "INDIV"
    NETWORK = "NETWORK"
    OTHER = "OTHER"


class AnalysisScope(str, Enum):
    """Scope for sponsor analysis."""

    ORGANIZATION = "ORGANIZATION"
    NETWORK = "NETWORK"
    ECOSYSTEM = "ECOSYSTEM"


class SortBy(str, Enum):
    """Sort options for search results."""

    RELEVANCE = "RELEVANCE"
    ENROLLMENT_COUNT = "ENROLLMENT_COUNT"
    LAST_UPDATE = "LAST_UPDATE"
    COMPLETION_DATE = "COMPLETION_DATE"
    START_DATE = "START_DATE"


# ============================================================================
# Input Models for Tool Parameters
# ============================================================================


class LocationFilter(BaseModel):
    """Geographic location filter."""

    country: str | None = Field(None, description="Country name")
    city: str | None = Field(None, description="City name")
    state: str | None = Field(None, description="State/province name")
    latitude: float | None = Field(None, description="Latitude for proximity search")
    longitude: float | None = Field(None, description="Longitude for proximity search")
    radius_km: float | None = Field(50.0, description="Search radius in kilometers")


class EligibilityCriteria(BaseModel):
    """Patient eligibility criteria."""

    min_age: str | None = Field(None, description="Minimum age (e.g., '18 years')")
    max_age: str | None = Field(None, description="Maximum age (e.g., '65 years')")
    sex: Sex | None = Field(None, description="Sex requirement")
    healthy_volunteers: bool | None = Field(None, description="Accepts healthy volunteers")


class DateRange(BaseModel):
    """Date range filter."""

    start_date_from: date | None = Field(None, description="Study start date from")
    start_date_to: date | None = Field(None, description="Study start date to")
    completion_date_from: date | None = Field(None, description="Completion date from")
    completion_date_to: date | None = Field(None, description="Completion date to")


class PatientProfile(BaseModel):
    """Patient profile for trial matching."""

    age: int = Field(..., description="Patient's current age")
    gender: Sex = Field(..., description="Patient's gender")
    primary_condition: str = Field(..., description="Primary diagnosed condition")
    secondary_conditions: list[str] | None = Field(None, description="Comorbidities")
    location: LocationFilter | None = Field(None, description="Patient's location")
    excluded_interventions: list[str] | None = Field(
        None, description="Interventions to exclude (allergies, etc.)"
    )
    preferred_phases: list[Phase] | None = Field(None, description="Preferred trial phases")
    must_be_recruiting: bool = Field(True, description="Only include recruiting trials")
    max_travel_distance_km: float | None = Field(100.0, description="Max travel distance")


class TimeWindow(BaseModel):
    """Time window for analysis."""

    from_date: date | None = Field(None, description="Start date")
    to_date: date | None = Field(None, description="End date")


# ============================================================================
# Output Models
# ============================================================================


class TrialSummary(BaseModel):
    """Summary of a clinical trial."""

    nct_id: str = Field(..., description="NCT identifier")
    title: str = Field(..., description="Brief title")
    status: str = Field(..., description="Overall status")
    phase: list[str] | None = Field(None, description="Trial phase(s)")
    conditions: list[str] | None = Field(None, description="Conditions studied")
    interventions: list[str] | None = Field(None, description="Interventions")
    sponsor: str | None = Field(None, description="Lead sponsor")
    enrollment: int | None = Field(None, description="Enrollment count")
    start_date: str | None = Field(None, description="Study start date")
    completion_date: str | None = Field(None, description="Expected completion date")
    locations: list[str] | None = Field(None, description="Study locations")


class TrialMetrics(BaseModel):
    """Computed metrics for a trial."""

    trial_maturity: TrialMaturity | None = Field(None, description="EARLY/MID/LATE stage")
    enrollment_pace: str | None = Field(None, description="Enrollment velocity assessment")
    completion_likelihood: str | None = Field(None, description="Likelihood to complete")
    outcome_coverage: float | None = Field(None, description="% of outcomes with results")
    days_since_start: int | None = Field(None, description="Days since study start")
    days_to_completion: int | None = Field(None, description="Estimated days to completion")


class EligibilityAnalysis(BaseModel):
    """Parsed eligibility criteria."""

    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    age_range: str | None = Field(None, description="Age eligibility range")
    sex: str | None = Field(None, description="Sex requirement")
    accepts_healthy: bool | None = Field(None, description="Accepts healthy volunteers")


class MatchedTrial(BaseModel):
    """A trial matched to a patient profile."""

    trial: TrialSummary
    match_score: float = Field(..., description="Match score 0-100")
    eligibility_status: EligibilityStatus
    eligibility_explanation: str = Field(..., description="Why patient matches/doesn't match")
    distance_km: float | None = Field(None, description="Distance to nearest site")
    next_steps: list[str] | None = Field(None, description="How to apply")


class SimilarTrial(BaseModel):
    """A similar trial for comparison."""

    trial: TrialSummary
    similarity_score: float = Field(..., description="Similarity score 0-100")
    matching_dimensions: list[str] = Field(default_factory=list)
    key_differences: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Result from trial search."""

    studies: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int | None = Field(None, description="Total matching studies")
    next_page_token: str | None = Field(None, description="Token for next page")
    execution_time_ms: float | None = Field(None, description="Query execution time")
    status: str = Field("SUCCESS", description="Result status")
    message: str | None = Field(None, description="Status message")


class FieldSchema(BaseModel):
    """Schema for a data field."""

    field_name: str
    piece_name: str | None = None
    data_type: str | None = None
    searchable: bool = False
    retrievable: bool = True
    description: str | None = None
    example_values: list[str] | None = None


class EnumDefinition(BaseModel):
    """Definition of an enumeration type."""

    enum_name: str
    possible_values: list[str]
    description: str | None = None


class MetadataResult(BaseModel):
    """Result from metadata schema tool."""

    fields_schema: list[FieldSchema] | None = None
    search_areas: list[dict[str, Any]] | None = None
    enum_definitions: list[EnumDefinition] | None = None
    api_version: str | None = None
    total_studies: int | None = None
