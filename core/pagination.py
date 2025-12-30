"""Token-based pagination handler for ClinicalTrials.gov API."""

from typing import Any, AsyncIterator

from .api_client import ClinicalTrialsAPIClient, get_api_client
from config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class PaginationHandler:
    """Handles token-based pagination for API results."""

    def __init__(self, client: ClinicalTrialsAPIClient | None = None):
        self._client = client or get_api_client()

    async def fetch_all_pages(
        self,
        query_params: dict[str, Any],
        max_results: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        count_total: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch all paginated results and return unified response.

        Args:
            query_params: Query parameters for the search
            max_results: Maximum total results to fetch (None = all)
            page_size: Results per page (max 1000)
            count_total: Whether to count total matching studies

        Returns:
            Unified result with all studies and metadata
        """
        page_size = min(page_size, MAX_PAGE_SIZE)
        all_studies: list[dict[str, Any]] = []
        page_token: str | None = None
        total_count: int | None = None

        while True:
            response = await self._client.search_studies(
                query_params=query_params,
                page_size=page_size,
                page_token=page_token,
                count_total=count_total and total_count is None,  # Only count on first page
            )

            studies = response.get("studies", [])
            all_studies.extend(studies)

            # Get total count from first page
            if total_count is None:
                total_count = response.get("totalCount")

            # Check if we've reached max_results
            if max_results and len(all_studies) >= max_results:
                all_studies = all_studies[:max_results]
                break

            # Check for next page
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return {
            "studies": all_studies,
            "totalCount": total_count,
            "fetchedCount": len(all_studies),
        }

    async def stream_pages(
        self,
        query_params: dict[str, Any],
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Stream paginated results as async iterator.

        Yields pages of studies one at a time for memory-efficient processing.

        Args:
            query_params: Query parameters for the search
            page_size: Results per page (max 1000)

        Yields:
            Lists of study dictionaries, one page at a time
        """
        page_size = min(page_size, MAX_PAGE_SIZE)
        page_token: str | None = None

        while True:
            response = await self._client.search_studies(
                query_params=query_params,
                page_size=page_size,
                page_token=page_token,
            )

            studies = response.get("studies", [])
            if studies:
                yield studies

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    async def fetch_page(
        self,
        query_params: dict[str, Any],
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
        count_total: bool = False,
    ) -> dict[str, Any]:
        """
        Fetch a single page of results.

        Args:
            query_params: Query parameters for the search
            page_size: Results per page
            page_token: Token for specific page
            count_total: Whether to count total

        Returns:
            Single page response
        """
        return await self._client.search_studies(
            query_params=query_params,
            page_size=page_size,
            page_token=page_token,
            count_total=count_total,
        )
