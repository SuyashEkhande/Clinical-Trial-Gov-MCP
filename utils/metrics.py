"""Utility functions for computing trial metrics."""

from datetime import datetime, date
from typing import Any


def compute_trial_maturity(trial: dict[str, Any]) -> str:
    """
    Compute trial maturity stage: EARLY, MID, or LATE.

    Based on:
    - Trial phase
    - Overall status
    - Time since start

    Args:
        trial: Trial data dictionary

    Returns:
        "EARLY", "MID", or "LATE"
    """
    # Extract phase
    phases = []
    protocol = trial.get("protocolSection", {})
    design_module = protocol.get("designModule", {})
    phase_list = design_module.get("phases", [])
    if isinstance(phase_list, list):
        phases = [p.upper() for p in phase_list]
    elif isinstance(phase_list, str):
        phases = [phase_list.upper()]

    # Extract status
    status_module = protocol.get("statusModule", {})
    status = status_module.get("overallStatus", "").upper()

    # Check for late stage indicators
    if "PHASE4" in phases or status == "COMPLETED":
        return "LATE"

    # Check for mid stage
    if "PHASE2" in phases or "PHASE3" in phases:
        return "MID"

    # Check for early stage
    if "PHASE1" in phases or "EARLY_PHASE1" in phases:
        return "EARLY"

    # Default based on status
    if status in ("NOT_YET_RECRUITING", "RECRUITING"):
        return "EARLY"
    elif status in ("ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"):
        return "MID"
    elif status in ("COMPLETED", "TERMINATED", "SUSPENDED", "WITHDRAWN"):
        return "LATE"

    return "EARLY"


def compute_enrollment_pace(trial: dict[str, Any]) -> str:
    """
    Compute enrollment pace assessment.

    Based on:
    - Target enrollment
    - Actual enrollment (if available)
    - Time since start

    Args:
        trial: Trial data dictionary

    Returns:
        Description of enrollment pace ("Fast", "On Track", "Slow", "Unknown")
    """
    protocol = trial.get("protocolSection", {})
    design_module = protocol.get("designModule", {})
    status_module = protocol.get("statusModule", {})

    # Get enrollment info
    enrollment_info = design_module.get("enrollmentInfo", {})
    target = enrollment_info.get("count")
    enrollment_type = enrollment_info.get("type", "").upper()

    if not target:
        return "Unknown"

    # Get start date
    start_struct = status_module.get("startDateStruct", {})
    start_date_str = start_struct.get("date")

    if not start_date_str:
        return "Unknown"

    try:
        # Parse start date (format: "YYYY-MM-DD" or "YYYY-MM" or "YYYY")
        if len(start_date_str) == 10:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        elif len(start_date_str) == 7:
            start_date = datetime.strptime(start_date_str + "-01", "%Y-%m-%d").date()
        else:
            start_date = datetime.strptime(start_date_str + "-01-01", "%Y-%m-%d").date()

        days_since_start = (date.today() - start_date).days

        if days_since_start <= 0:
            return "Not Started"

        # Estimate expected months based on typical trial duration
        # Phase 1: ~1 year, Phase 2: ~2 years, Phase 3: ~3 years
        phases = design_module.get("phases", [])
        if "PHASE3" in phases:
            expected_months = 36
        elif "PHASE2" in phases:
            expected_months = 24
        else:
            expected_months = 12

        expected_per_month = target / expected_months
        months_elapsed = days_since_start / 30

        if enrollment_type == "ACTUAL":
            # If we have actual enrollment data (not common in active trials)
            return "Completed Enrollment"

        # Estimate pace based on time elapsed
        if months_elapsed < 3:
            return "Recently Started"
        elif months_elapsed > expected_months * 0.8:
            return "Approaching Completion"
        else:
            progress_pct = (months_elapsed / expected_months) * 100
            if progress_pct < 30:
                return "Early Stage"
            elif progress_pct < 70:
                return "On Track"
            else:
                return "Nearing Target"

    except (ValueError, TypeError):
        return "Unknown"


def compute_completion_likelihood(trial: dict[str, Any]) -> str:
    """
    Compute likelihood of trial completing as planned.

    Based on:
    - Current status
    - Phase
    - Historical patterns

    Args:
        trial: Trial data dictionary

    Returns:
        Likelihood assessment ("High", "Medium", "Low", "Completed", "N/A")
    """
    protocol = trial.get("protocolSection", {})
    status_module = protocol.get("statusModule", {})
    status = status_module.get("overallStatus", "").upper()

    # Already completed or terminated
    if status == "COMPLETED":
        return "Completed"
    elif status in ("TERMINATED", "WITHDRAWN"):
        return "Did Not Complete"
    elif status == "SUSPENDED":
        return "Low - Suspended"

    # Active trials
    if status in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"):
        # Get phase for historical completion rates
        design_module = protocol.get("designModule", {})
        phases = design_module.get("phases", [])

        # Historical completion rates by phase (approximate)
        # Phase 1: ~60%, Phase 2: ~35%, Phase 3: ~25%
        if "PHASE1" in phases or "EARLY_PHASE1" in phases:
            return "Medium - Phase 1"
        elif "PHASE2" in phases:
            return "Medium-Low - Phase 2"
        elif "PHASE3" in phases:
            return "Medium - Phase 3"
        elif "PHASE4" in phases:
            return "High - Phase 4"
        else:
            return "Medium"

    elif status == "NOT_YET_RECRUITING":
        return "Medium - Not Yet Started"

    return "Unknown"


def compute_days_since_start(trial: dict[str, Any]) -> int | None:
    """
    Compute days since trial started.

    Args:
        trial: Trial data dictionary

    Returns:
        Number of days since start, or None if not available
    """
    protocol = trial.get("protocolSection", {})
    status_module = protocol.get("statusModule", {})
    start_struct = status_module.get("startDateStruct", {})
    start_date_str = start_struct.get("date")

    if not start_date_str:
        return None

    try:
        if len(start_date_str) == 10:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        elif len(start_date_str) == 7:
            start_date = datetime.strptime(start_date_str + "-01", "%Y-%m-%d").date()
        else:
            start_date = datetime.strptime(start_date_str + "-01-01", "%Y-%m-%d").date()

        return (date.today() - start_date).days
    except (ValueError, TypeError):
        return None


def compute_days_to_completion(trial: dict[str, Any]) -> int | None:
    """
    Compute estimated days until completion.

    Args:
        trial: Trial data dictionary

    Returns:
        Number of days to completion, or None if not available/already completed
    """
    protocol = trial.get("protocolSection", {})
    status_module = protocol.get("statusModule", {})

    # Check if already completed
    status = status_module.get("overallStatus", "").upper()
    if status in ("COMPLETED", "TERMINATED", "WITHDRAWN"):
        return 0

    # Get completion date
    comp_struct = status_module.get("completionDateStruct", {})
    comp_date_str = comp_struct.get("date")

    if not comp_date_str:
        # Try primary completion date
        comp_struct = status_module.get("primaryCompletionDateStruct", {})
        comp_date_str = comp_struct.get("date")

    if not comp_date_str:
        return None

    try:
        if len(comp_date_str) == 10:
            comp_date = datetime.strptime(comp_date_str, "%Y-%m-%d").date()
        elif len(comp_date_str) == 7:
            comp_date = datetime.strptime(comp_date_str + "-01", "%Y-%m-%d").date()
        else:
            comp_date = datetime.strptime(comp_date_str + "-01-01", "%Y-%m-%d").date()

        days = (comp_date - date.today()).days
        return max(0, days)  # Return 0 if past due
    except (ValueError, TypeError):
        return None


def extract_trial_summary(trial: dict[str, Any]) -> dict[str, Any]:
    """
    Extract a summary of key trial information.

    Args:
        trial: Full trial data dictionary

    Returns:
        Simplified summary dictionary
    """
    protocol = trial.get("protocolSection", {})
    id_module = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    design_module = protocol.get("designModule", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    arms_module = protocol.get("armsInterventionsModule", {})
    contacts_module = protocol.get("contactsLocationsModule", {})

    # Extract interventions
    interventions = []
    for arm in arms_module.get("interventions", []):
        name = arm.get("name")
        if name:
            interventions.append(name)

    # Extract conditions
    conditions = conditions_module.get("conditions", [])

    # Extract locations
    locations = []
    for loc in contacts_module.get("locations", [])[:5]:  # Limit to 5
        parts = []
        if loc.get("city"):
            parts.append(loc["city"])
        if loc.get("state"):
            parts.append(loc["state"])
        if loc.get("country"):
            parts.append(loc["country"])
        if parts:
            locations.append(", ".join(parts))

    # Get enrollment
    enrollment_info = design_module.get("enrollmentInfo", {})

    return {
        "nct_id": id_module.get("nctId", ""),
        "title": id_module.get("briefTitle", ""),
        "official_title": id_module.get("officialTitle", ""),
        "status": status_module.get("overallStatus", ""),
        "phase": design_module.get("phases", []),
        "study_type": design_module.get("studyType", ""),
        "conditions": conditions,
        "interventions": interventions,
        "sponsor": sponsor_module.get("leadSponsor", {}).get("name", ""),
        "sponsor_class": sponsor_module.get("leadSponsor", {}).get("class", ""),
        "enrollment": enrollment_info.get("count"),
        "enrollment_type": enrollment_info.get("type", ""),
        "start_date": status_module.get("startDateStruct", {}).get("date"),
        "completion_date": status_module.get("completionDateStruct", {}).get("date"),
        "locations": locations,
        "has_results": trial.get("hasResults", False),
    }
