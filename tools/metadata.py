"""Tool 4: get_trial_metadata_schema - API data structure introspection."""

from typing import Any

from core.api_client import get_api_client
from core.models import MetadataScope


async def get_trial_metadata_schema(
    scope: str = "FIELDS",
    include_descriptions: bool = True,
    filter_by_area: str | None = None,
    searchable_only: bool = False,
    include_examples: bool = True,
) -> dict[str, Any]:
    """
    Get the data structure and available search fields for ClinicalTrials.gov API.

    This is a self-documenting tool that enables discovery of queryable fields.

    Args:
        scope: What to return - FIELDS, SEARCH_AREAS, ENUMS, STATISTICS, or ALL
        include_descriptions: Add field definitions
        filter_by_area: Filter to specific module (e.g., "ConditionsModule")
        searchable_only: Only return fields that can be queried
        include_examples: Add example values where available

    Returns:
        Schema information based on requested scope
    """
    client = get_api_client()
    result: dict[str, Any] = {
        "status": "SUCCESS",
        "scope": scope,
    }

    try:
        scope_enum = MetadataScope(scope.upper())
    except ValueError:
        scope_enum = MetadataScope.FIELDS

    # Get metadata fields
    if scope_enum in (MetadataScope.FIELDS, MetadataScope.ALL):
        metadata = await client.get_metadata()
        fields_schema = []

        for field in metadata.get("fields", []):
            field_info = {
                "field_name": field.get("name", ""),
                "piece_name": field.get("piece", ""),
                "data_type": field.get("type", ""),
                "searchable": field.get("searchable", False),
                "retrievable": True,
            }

            if include_descriptions:
                field_info["description"] = field.get("description", "")

            # Apply filters
            if filter_by_area and filter_by_area.lower() not in field_info["piece_name"].lower():
                continue
            if searchable_only and not field_info["searchable"]:
                continue

            fields_schema.append(field_info)

        result["fields_schema"] = fields_schema
        result["total_fields"] = len(fields_schema)

    # Get search areas
    if scope_enum in (MetadataScope.SEARCH_AREAS, MetadataScope.ALL):
        search_areas = await client.get_search_areas()
        areas = []

        for area in search_areas.get("searchAreas", []):
            area_info = {
                "area_name": area.get("name", ""),
                "ui_label": area.get("uiLabel", ""),
                "param_name": area.get("param", ""),
                "parts": [p.get("name", "") for p in area.get("parts", [])],
            }
            areas.append(area_info)

        result["search_areas"] = areas

    # Get enumerations
    if scope_enum in (MetadataScope.ENUMS, MetadataScope.ALL):
        enums = await client.get_enums()
        enum_definitions = []

        for enum in enums.get("enums", []):
            enum_info = {
                "enum_name": enum.get("name", ""),
                "possible_values": enum.get("values", []),
            }
            if include_descriptions:
                enum_info["description"] = enum.get("description", "")
            enum_definitions.append(enum_info)

        result["enum_definitions"] = enum_definitions

    # Get statistics info
    if scope_enum in (MetadataScope.STATISTICS, MetadataScope.ALL):
        try:
            stats = await client.get_overall_stats()
            result["statistics"] = {
                "total_studies": stats.get("totalCount", 0),
                "last_updated": stats.get("lastUpdated", ""),
            }
        except Exception:
            result["statistics"] = {"error": "Could not fetch statistics"}

    # Get API version
    try:
        version = await client.get_version()
        result["api_version"] = version.get("version", "")
    except Exception:
        pass

    # Add usage examples
    if include_examples:
        result["query_examples"] = [
            {
                "description": "Search for lung cancer trials in Phase 3",
                "query": 'AREA[Condition]"lung cancer" AND AREA[Phase]PHASE3',
            },
            {
                "description": "Find recruiting trials by sponsor",
                "query": "AREA[LeadSponsorName]Pfizer AND AREA[OverallStatus]RECRUITING",
            },
            {
                "description": "Search trials near a location",
                "query": "filter.geo=distance(42.3601,-71.0589,50mi)",
            },
            {
                "description": "Find trials with posted results",
                "query": "AREA[HasResults]true",
            },
        ]

    return result
