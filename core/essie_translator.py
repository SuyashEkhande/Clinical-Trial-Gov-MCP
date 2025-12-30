"""Natural language to Essie query syntax translator.

Essie is the query language used by ClinicalTrials.gov API v2.
This module provides rules-based translation from natural language queries.
"""

import re
from typing import Any


# Field mappings for AREA[] expressions
FIELD_MAPPINGS = {
    # Conditions
    "condition": "Condition",
    "disease": "Condition",
    "diagnosis": "Condition",
    # Interventions
    "intervention": "InterventionName",
    "drug": "InterventionName",
    "treatment": "InterventionName",
    "therapy": "InterventionName",
    "medication": "InterventionName",
    # Phase
    "phase": "Phase",
    # Status
    "status": "OverallStatus",
    # Sponsor
    "sponsor": "LeadSponsorName",
    "company": "LeadSponsorName",
    "organization": "LeadSponsorName",
    # Location
    "city": "LocationCity",
    "state": "LocationState",
    "country": "LocationCountry",
    # Other
    "title": "BriefTitle",
    "outcome": "PrimaryOutcomeMeasure",
}

# Phase value mappings
PHASE_MAPPINGS = {
    "phase 1": "PHASE1",
    "phase1": "PHASE1",
    "phase i": "PHASE1",
    "phase 2": "PHASE2",
    "phase2": "PHASE2",
    "phase ii": "PHASE2",
    "phase 3": "PHASE3",
    "phase3": "PHASE3",
    "phase iii": "PHASE3",
    "phase 4": "PHASE4",
    "phase4": "PHASE4",
    "phase iv": "PHASE4",
    "early phase 1": "EARLY_PHASE1",
    "early phase1": "EARLY_PHASE1",
}

# Status value mappings
STATUS_MAPPINGS = {
    "recruiting": "RECRUITING",
    "active": "ACTIVE_NOT_RECRUITING",
    "active not recruiting": "ACTIVE_NOT_RECRUITING",
    "not yet recruiting": "NOT_YET_RECRUITING",
    "completed": "COMPLETED",
    "suspended": "SUSPENDED",
    "terminated": "TERMINATED",
    "withdrawn": "WITHDRAWN",
}

# Keywords that indicate logical operators
BOOLEAN_PATTERNS = {
    r"\bAND\b": " AND ",
    r"\bOR\b": " OR ",
    r"\bNOT\b": " NOT ",
    r"\band\b": " AND ",
    r"\bor\b": " OR ",
    r"\bnot\b": " NOT ",
}


class EssieTranslator:
    """Translates natural language queries to Essie expression syntax."""

    def __init__(self):
        self._field_pattern = re.compile(
            r"\b(" + "|".join(FIELD_MAPPINGS.keys()) + r")\s*[:=]?\s*",
            re.IGNORECASE,
        )

    def translate(self, query: str) -> str:
        """
        Translate natural language query to Essie syntax.

        Examples:
            "lung cancer AND pembrolizumab in phase 3"
            → 'AREA[Condition]"lung cancer" AND AREA[InterventionName]pembrolizumab AND AREA[Phase]PHASE3'

            "recruiting trials for diabetes"
            → 'AREA[Condition]diabetes AND AREA[OverallStatus]RECRUITING'

        Args:
            query: Natural language search query

        Returns:
            Essie expression string
        """
        if not query or not query.strip():
            return ""

        # Check if already in Essie format (has AREA[] or SEARCH[])
        if "AREA[" in query or "SEARCH[" in query:
            return query

        # Process the query
        translated = self._translate_query(query)
        return translated.strip()

    def _translate_query(self, query: str) -> str:
        """Internal translation logic."""
        parts = []
        remaining = query.strip()

        # Handle "in phase X" pattern
        phase_match = re.search(r"\bin\s+(phase\s*\d+|phase\s*[ivIV]+)", remaining, re.IGNORECASE)
        if phase_match:
            phase_text = phase_match.group(1).lower()
            phase_value = PHASE_MAPPINGS.get(phase_text.replace(" ", ""), phase_text)
            if phase_value in PHASE_MAPPINGS.values() or phase_value.upper().startswith("PHASE"):
                parts.append(f"AREA[Phase]{phase_value.upper()}")
            remaining = remaining[: phase_match.start()] + remaining[phase_match.end() :]

        # Handle "phase X" pattern without "in"
        phase_match2 = re.search(r"\b(phase\s*\d+|phase\s*[ivIV]+)\b", remaining, re.IGNORECASE)
        if phase_match2:
            phase_text = phase_match2.group(1).lower().replace(" ", "")
            phase_value = PHASE_MAPPINGS.get(phase_text, phase_text)
            if phase_value not in [p for p in parts if "Phase" in p]:
                if phase_value in PHASE_MAPPINGS.values() or phase_value.upper().startswith("PHASE"):
                    parts.append(f"AREA[Phase]{phase_value.upper()}")
            remaining = remaining[: phase_match2.start()] + remaining[phase_match2.end() :]

        # Handle status keywords
        for status_key, status_value in STATUS_MAPPINGS.items():
            if re.search(rf"\b{status_key}\b", remaining, re.IGNORECASE):
                parts.append(f"AREA[OverallStatus]{status_value}")
                remaining = re.sub(rf"\b{status_key}\b\s*(trials?|studies?)?\s*", "", remaining, flags=re.IGNORECASE)

        # Handle location patterns
        location_match = re.search(r"\b(?:in|near|at)\s+([A-Za-z\s]+?)(?:\s+(?:AND|OR|,|$))", remaining, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip()
            # Skip if it's a phase
            if not re.match(r"phase", location, re.IGNORECASE):
                # Check if it looks like a country, state, or city
                if len(location) > 2 and location.lower() not in ["the", "a", "an"]:
                    parts.append(f'AREA[LocationCountry]"{location}"')
                remaining = remaining[: location_match.start()] + remaining[location_match.end() :]

        # Clean up remaining text and extract main search terms
        remaining = self._clean_remaining(remaining)

        # Split by boolean operators and process each term
        main_terms = self._extract_main_terms(remaining)

        if main_terms:
            # Combine main terms with existing parts
            all_parts = main_terms + parts
            return " AND ".join(all_parts)
        elif parts:
            return " AND ".join(parts)
        else:
            # Return as simple condition search if nothing parsed
            return f'AREA[Condition]"{query.strip()}"' if query.strip() else ""

    def _clean_remaining(self, text: str) -> str:
        """Clean up remaining query text."""
        # Remove common filler words
        text = re.sub(r"\b(trials?|studies?|for|with|the|a|an)\b", "", text, flags=re.IGNORECASE)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_main_terms(self, text: str) -> list[str]:
        """Extract main search terms from cleaned text."""
        if not text:
            return []

        parts = []
        # Split by AND/OR but keep the operators
        tokens = re.split(r"\s+(AND|OR)\s+", text, flags=re.IGNORECASE)

        current_operator = "AND"
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if token.upper() in ("AND", "OR"):
                current_operator = token.upper()
                continue

            # Determine appropriate field based on content
            term_parts = self._categorize_term(token)
            if term_parts:
                parts.extend(term_parts)

        return parts

    def _categorize_term(self, term: str) -> list[str]:
        """Categorize a search term and wrap in appropriate AREA[]."""
        term = term.strip()
        if not term:
            return []

        # Check for intervention-like terms (drug names often have specific patterns)
        intervention_patterns = [
            r"mab$",  # monoclonal antibodies
            r"nib$",  # kinase inhibitors
            r"pril$",  # ACE inhibitors
            r"olol$",  # beta blockers
            r"statin$",
            r"cillin$",
        ]
        is_intervention = any(re.search(p, term, re.IGNORECASE) for p in intervention_patterns)

        if is_intervention:
            return [f"AREA[InterventionName]{term}"]

        # Default to condition
        if " " in term:
            return [f'AREA[Condition]"{term}"']
        return [f"AREA[Condition]{term}"]

    def build_query_params(
        self,
        query: str | None = None,
        disease_condition: str | None = None,
        intervention: str | None = None,
        phase: list[str] | None = None,
        status: list[str] | None = None,
        location: dict[str, Any] | None = None,
        sponsor: str | None = None,
    ) -> dict[str, Any]:
        """
        Build API query parameters from structured inputs.

        Args:
            query: Natural language or Essie query
            disease_condition: Specific disease/condition
            intervention: Intervention name/type
            phase: List of phases (PHASE1, PHASE2, etc.)
            status: List of statuses (RECRUITING, etc.)
            location: Location dict with country, city, state, etc.
            sponsor: Sponsor/organization name

        Returns:
            Dictionary of API query parameters
        """
        params: dict[str, Any] = {}

        # Handle main query
        if query:
            translated = self.translate(query)
            if translated:
                # Use filter.advanced for complex queries
                if "AREA[" in translated or "SEARCH[" in translated:
                    params["filter.advanced"] = translated
                else:
                    params["query.term"] = query

        # Handle specific condition
        if disease_condition:
            if "query.cond" not in params:
                params["query.cond"] = disease_condition

        # Handle intervention
        if intervention:
            params["query.intr"] = intervention

        # Handle phase filter
        if phase:
            normalized_phases = [p.upper() if p.upper().startswith("PHASE") else PHASE_MAPPINGS.get(p.lower(), p) for p in phase]
            params["filter.advanced"] = self._append_filter(
                params.get("filter.advanced"),
                "(" + " OR ".join(f"AREA[Phase]{p}" for p in normalized_phases) + ")"
            )

        # Handle status filter
        if status:
            params["filter.overallStatus"] = "|".join(status)

        # Handle location
        if location:
            if location.get("latitude") and location.get("longitude"):
                radius = location.get("radius_km", 50)
                params["filter.geo"] = f"distance({location['latitude']},{location['longitude']},{radius}km)"
            elif location.get("country"):
                params["query.locn"] = location["country"]

        # Handle sponsor
        if sponsor:
            params["query.spons"] = sponsor

        return params

    def _append_filter(self, existing: str | None, new_filter: str) -> str:
        """Append to existing filter with AND."""
        if existing:
            return f"{existing} AND {new_filter}"
        return new_filter


# Singleton instance
_translator: EssieTranslator | None = None


def get_translator() -> EssieTranslator:
    """Get the singleton translator instance."""
    global _translator
    if _translator is None:
        _translator = EssieTranslator()
    return _translator
