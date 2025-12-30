"""Async HTTP client for ClinicalTrials.gov API with caching and retry logic."""

import asyncio
import hashlib
import json
from typing import Any

import aiohttp
from cachetools import TTLCache

from config import (
    API_BASE_URL,
    API_TIMEOUT_SECONDS,
    CACHE_MAX_SIZE,
    CACHE_TTL_METADATA,
    CACHE_TTL_SEARCH,
    CACHE_TTL_STATISTICS,
    CACHE_TTL_STUDY,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class APIValidationError(APIError):
    """Invalid query syntax or parameters."""

    pass


class APIRateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class APINotFoundError(APIError):
    """Resource not found (e.g., invalid NCT ID)."""

    pass


class ClinicalTrialsAPIClient:
    """Async HTTP client for ClinicalTrials.gov API v2."""

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        # Separate caches for different data types with appropriate TTLs
        self._cache_metadata = TTLCache(maxsize=100, ttl=CACHE_TTL_METADATA)
        self._cache_statistics = TTLCache(maxsize=200, ttl=CACHE_TTL_STATISTICS)
        self._cache_studies = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_STUDY)
        self._cache_search = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_SEARCH)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=API_TIMEOUT_SECONDS)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Accept": "application/json",
                },
            )
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_cache_key(self, endpoint: str, params: dict[str, Any] | None) -> str:
        """Generate a cache key from endpoint and parameters."""
        key_data = {"endpoint": endpoint, "params": params or {}}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_for_endpoint(self, endpoint: str) -> TTLCache:
        """Get the appropriate cache based on endpoint type."""
        if "metadata" in endpoint or "search-areas" in endpoint or "enums" in endpoint:
            return self._cache_metadata
        elif "stats" in endpoint:
            return self._cache_statistics
        elif "/studies/NCT" in endpoint:
            return self._cache_studies
        else:
            return self._cache_search

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Make a GET request to the API with caching and retry logic.

        Args:
            endpoint: API endpoint (e.g., "/studies", "/studies/NCT00000001")
            params: Query parameters
            use_cache: Whether to use cached results

        Returns:
            JSON response as dictionary

        Raises:
            APIError: On API errors
            APIValidationError: On invalid query syntax
            APIRateLimitError: On rate limiting
            APINotFoundError: On 404 responses
        """
        cache = self._get_cache_for_endpoint(endpoint)
        cache_key = self._get_cache_key(endpoint, params)

        # Check cache first
        if use_cache and cache_key in cache:
            return cache[cache_key]

        session = await self._get_session()
        url = f"{API_BASE_URL}{endpoint}"
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(url, params=params) as response:
                    # Handle specific error codes
                    if response.status == 400:
                        text = await response.text()
                        raise APIValidationError(
                            f"Invalid query: {text}",
                            status_code=400,
                        )
                    elif response.status == 404:
                        raise APINotFoundError(
                            f"Resource not found: {endpoint}",
                            status_code=404,
                        )
                    elif response.status == 429:
                        raise APIRateLimitError(
                            "Rate limit exceeded",
                            status_code=429,
                        )
                    elif response.status == 403:
                        raise APIError(
                            "Access forbidden - API may be blocking requests",
                            status_code=403,
                        )

                    response.raise_for_status()
                    data = await response.json()

                    # Cache successful responses
                    if use_cache:
                        cache[cache_key] = data

                    return data

            except (APIValidationError, APINotFoundError):
                raise  # Don't retry these
            except APIRateLimitError:
                # Wait longer for rate limits
                wait_time = RETRY_BACKOFF_FACTOR ** (attempt + 2)
                await asyncio.sleep(wait_time)
                last_error = APIRateLimitError("Rate limit exceeded", 429)
            except aiohttp.ClientResponseError as e:
                last_error = APIError(
                    f"HTTP error: {e.status}", e.status
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF_FACTOR**attempt)
            except aiohttp.ClientError as e:
                last_error = APIError(f"Request failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF_FACTOR**attempt)

        raise last_error or APIError("Unknown error after retries")

    async def get_study(self, nct_id: str, fields: list[str] | None = None) -> dict[str, Any]:
        """
        Fetch a single study by NCT ID.

        Args:
            nct_id: NCT identifier (e.g., "NCT00000001")
            fields: Optional list of fields to retrieve

        Returns:
            Study data dictionary
        """
        params = {}
        if fields:
            params["fields"] = "|".join(fields)

        return await self.get(f"/studies/{nct_id}", params=params if params else None)

    async def search_studies(
        self,
        query_params: dict[str, Any],
        page_size: int = 50,
        page_token: str | None = None,
        count_total: bool = False,
    ) -> dict[str, Any]:
        """
        Search for studies with the given query parameters.

        Args:
            query_params: Query parameters (query.cond, filter.overallStatus, etc.)
            page_size: Number of results per page (max 1000)
            page_token: Pagination token for subsequent pages
            count_total: Whether to count total matching studies

        Returns:
            Search results with studies array and optional pagination token
        """
        params = {**query_params, "pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
        if count_total:
            params["countTotal"] = "true"

        return await self.get("/studies", params=params)

    async def get_metadata(self) -> list[dict[str, Any]]:
        """Get the API data model metadata."""
        result = await self.get("/studies/metadata")
        # API returns array directly
        return {"fields": result} if isinstance(result, list) else result

    async def get_search_areas(self) -> dict[str, Any]:
        """Get available search areas and fields."""
        result = await self.get("/studies/search-areas")
        return {"searchAreas": result} if isinstance(result, list) else result

    async def get_enums(self) -> dict[str, Any]:
        """Get enumeration type definitions."""
        result = await self.get("/studies/enums")
        return {"enums": result} if isinstance(result, list) else result

    async def get_field_values(self, field: str) -> dict[str, Any]:
        """Get statistics on field values."""
        return await self.get("/stats/field/values", params={"types": field})

    async def get_field_sizes(self, field: str) -> dict[str, Any]:
        """Get statistics on list field sizes."""
        return await self.get("/stats/field/sizes", params={"fields": field})

    async def get_overall_stats(self) -> dict[str, Any]:
        """Get overall size statistics."""
        return await self.get("/stats/size")

    async def get_version(self) -> dict[str, Any]:
        """Get API version information."""
        return await self.get("/version")

    def clear_cache(self):
        """Clear all caches."""
        self._cache_metadata.clear()
        self._cache_statistics.clear()
        self._cache_studies.clear()
        self._cache_search.clear()


# Singleton instance
_client: ClinicalTrialsAPIClient | None = None


def get_api_client() -> ClinicalTrialsAPIClient:
    """Get the singleton API client instance."""
    global _client
    if _client is None:
        _client = ClinicalTrialsAPIClient()
    return _client
