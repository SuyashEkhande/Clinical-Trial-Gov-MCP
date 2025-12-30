"""Configuration and constants for ClinicalTrials.gov MCP Server."""

from typing import Final

# API Configuration
API_BASE_URL: Final[str] = "https://clinicaltrials.gov/api/v2"
API_TIMEOUT_SECONDS: Final[int] = 30
MAX_RETRIES: Final[int] = 3
RETRY_BACKOFF_FACTOR: Final[float] = 1.5

# Pagination
DEFAULT_PAGE_SIZE: Final[int] = 50
MAX_PAGE_SIZE: Final[int] = 1000

# Cache TTLs (in seconds)
CACHE_TTL_METADATA: Final[int] = 86400  # 24 hours for schema/enums
CACHE_TTL_STATISTICS: Final[int] = 86400  # 24 hours for field stats
CACHE_TTL_STUDY: Final[int] = 21600  # 6 hours for individual studies
CACHE_TTL_SEARCH: Final[int] = 3600  # 1 hour for search results
CACHE_MAX_SIZE: Final[int] = 1000  # Max cached items

# Default fields for different analysis depths
FIELDS_SUMMARY: Final[list[str]] = [
    "NCTId",
    "BriefTitle",
    "OverallStatus",
    "Phase",
    "Condition",
    "InterventionName",
    "LeadSponsorName",
    "EnrollmentCount",
]

FIELDS_STANDARD: Final[list[str]] = FIELDS_SUMMARY + [
    "OfficialTitle",
    "BriefSummary",
    "DetailedDescription",
    "StudyType",
    "DesignPrimaryPurpose",
    "EligibilityCriteria",
    "MinimumAge",
    "MaximumAge",
    "Sex",
    "HealthyVolunteers",
    "PrimaryOutcomeMeasure",
    "SecondaryOutcomeMeasure",
    "StartDate",
    "CompletionDate",
    "LocationCity",
    "LocationState",
    "LocationCountry",
    "LocationFacility",
    "CentralContactName",
    "CentralContactPhone",
    "CentralContactEMail",
]

FIELDS_COMPREHENSIVE: Final[list[str]] = FIELDS_STANDARD + [
    "OrgStudyId",
    "SecondaryId",
    "NCTIdAlias",
    "DesignAllocation",
    "DesignInterventionModel",
    "DesignMasking",
    "DesignWhoMasked",
    "ArmGroupLabel",
    "ArmGroupType",
    "ArmGroupDescription",
    "InterventionType",
    "InterventionDescription",
    "InterventionArmGroupLabel",
    "OtherOutcomeMeasure",
    "LeadSponsorClass",
    "Collaborator",
    "ResponsiblePartyType",
    "ResponsiblePartyInvestigatorFullName",
    "ReferencePMID",
    "ReferenceCitation",
    "ConditionMesh",
    "InterventionMesh",
    "HasResults",
    "ResultsFirstPostDate",
    "LastUpdatePostDate",
    "StudyFirstPostDate",
]
