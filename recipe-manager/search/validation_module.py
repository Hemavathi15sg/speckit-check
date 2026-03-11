"""
Validation Module
Validates and normalizes untrusted API inputs before processing.
This module is the FIRST step in the search pipeline.
CRITICAL FIX: Issue #447 - dietary_restrictions=None normalization
When user.dietary_restrictions is None (30% of users), normalize to []
to prevent TypeError in downstream modules.
Constitution Compliance:
- I. Reliability: Null-safe validation prevents crashes
- III. Testability: Pure functions, 90%+ test coverage
- V. Maintainability: Clear helper functions, no magic numbers
- VI. Quality Standards: Full type hints, mypy strict compliance
Performance Target: <5ms P50, <15ms P95
Line Count Target: ≤300 lines (currently: will be checked post-implementation)
"""
import logging
import time
from typing import Optional, List
from models import User
from search.types import SearchRequest, ValidatedSearchInput
from search.exceptions import ValidationError
from search.constants import (
    VALID_CUISINES,
    VALID_DIETARY_RESTRICTIONS,
    VALID_DIFFICULTIES,
    MAX_QUERY_LENGTH,
    MIN_PREP_TIME,
    MAX_PREP_TIME,
    MIN_RATING,
    MAX_RATING,
    MIN_PAGE,
    DEFAULT_PAGE,
    MIN_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DEFAULT_PAGE_SIZE,
)

# Configure module logger
logger = logging.getLogger(__name__)
def validate_search_request(
    request: SearchRequest,
    user: User
) -> ValidatedSearchInput:
    """
    Validate and normalize raw search request.
    This is the entry point for all search validation. It orchestrates
    validation of all fields and returns a fully validated, normalized
    object ready for filtering.
    Args:
        request: Untrusted input from API layer
        user: Authenticated user object (for user_id)
    Returns:
        ValidatedSearchInput with all fields validated and normalized
    Raises:
        ValidationError: If any input is invalid and cannot be normalized
    Performance:
        Target: <5ms P50, <15ms P95
    Side Effects:
        None (pure function)
    Example:
        >>> request = SearchRequest(query="pasta", dietary_restrictions=None)
        >>> user = User(id=uuid4(), name="Test", email="test@example.com",
        ...             dietary_restrictions=None)
        >>> result = validate_search_request(request, user)
        >>> result.dietary_restrictions  # Never None!
        []
    """
    start_time = time.perf_counter()
    try:
        # Validate and normalize all fields
        validated = ValidatedSearchInput(
            query=_validate_query(request.query),
            cuisine=_validate_cuisine(request.cuisine),
            dietary_restrictions=_validate_dietary_restrictions(
                request.dietary_restrictions,
                user.dietary_restrictions
            ),
            prep_time_max=_validate_prep_time(request.prep_time_max),
            difficulty=_validate_difficulty(request.difficulty),
            min_rating=_validate_min_rating(request.min_rating),
            page=_validate_page(request.page),
            page_size=_validate_page_size(request.page_size),
            user_id=str(user.id),
        )
        # Log validation success with timing
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(
            "Validation successful for user_id=%s in %.2fms",
            validated.user_id,
            duration_ms,
            extra={
                "event": "validation_success",
                "user_id": validated.user_id,
                "duration_ms": duration_ms,
            },
        )
        return validated
    except ValidationError:
        # Re-raise ValidationError as-is
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.warning(
            "Validation failed in %.2fms",
            duration_ms,
            extra={
                "event": "validation_failure",
                "duration_ms": duration_ms,
            },
        )
        raise
def _validate_query(query: Optional[str]) -> str:
    """
    Validate and normalize search query.
    Rules:
    - None → "" (empty string for "search all")
    - Trim leading/trailing whitespace
    - Lowercase for consistent filtering
    - Truncate to MAX_QUERY_LENGTH if too long
    Args:
        query: Raw query string from request (may be None)
    Returns:
        Normalized query string (never None, never >MAX_QUERY_LENGTH)
    """
    # None → empty string (search all recipes)
    if query is None:
        return ""
    # Trim and lowercase
    normalized = query.strip().lower()
    # Truncate if too long
    if len(normalized) > MAX_QUERY_LENGTH:
        logger.warning(
            "Query truncated from %d to %d characters",
            len(normalized),
            MAX_QUERY_LENGTH,
            extra={
                "event": "query_truncated",
                "original_length": len(normalized),
                "truncated_length": MAX_QUERY_LENGTH,
            },
        )
        normalized = normalized[:MAX_QUERY_LENGTH]
    return normalized
def _validate_cuisine(cuisine: Optional[str]) -> Optional[str]:
    """
    Validate and normalize cuisine filter.
    Rules:
    - None → None (no cuisine filter)
    - Must be in VALID_CUISINES set
    - Normalized to title case ("italian" → "Italian")
    Args:
        cuisine: Raw cuisine string from request (may be None)
    Returns:
        Normalized cuisine string or None
    Raises:
        ValidationError: If cuisine is not in VALID_CUISINES
    """
    if cuisine is None:
        return None
    # Normalize to title case for comparison
    normalized = cuisine.strip().title()
    # Check if valid
    if normalized not in VALID_CUISINES:
        raise ValidationError(
            field="cuisine",
            value=cuisine,
            message=f"Invalid cuisine. Must be one of: {', '.join(sorted(VALID_CUISINES))}"
        )
    return normalized
def _validate_dietary_restrictions(
    request_restrictions: Optional[List[str]],
    user_restrictions: Optional[List[str]]
) -> List[str]:
    """
    Validate and normalize dietary restrictions.
    CRITICAL: This function fixes Issue #447.
    When both request and user restrictions are None (30% of users),
    this returns [] instead of None, preventing TypeError downstream.
    Rules:
    - None → [] (CRITICAL: Issue #447 fix)
    - Each item must be in VALID_DIETARY_RESTRICTIONS
    - Normalized to lowercase
    - Duplicates removed
    - Empty list preserved as []
    Priority: Use request restrictions if provided, else user restrictions
    Args:
        request_restrictions: Dietary restrictions from API request
        user_restrictions: Dietary restrictions from User object
    Returns:
        List of valid dietary restrictions (NEVER None, may be empty)
    Raises:
        ValidationError: If any restriction is invalid
    """
    # Priority: request > user > []
    restrictions = request_restrictions if request_restrictions is not None else user_restrictions
    # CRITICAL: None → [] (Issue #447 fix)
    if restrictions is None:
        logger.debug("Dietary restrictions normalized from None to []")
        return []
    # Empty list is valid
    if not restrictions:
        return []
    # Normalize to lowercase and remove duplicates
    normalized = []
    seen = set()
    for restriction in restrictions:
        normalized_value = restriction.strip().lower()
        # Validate against allowed set
        if normalized_value not in VALID_DIETARY_RESTRICTIONS:
            raise ValidationError(
                field="dietary_restrictions",
                value=restriction,
                message=f"Invalid dietary restriction '{restriction}'. "
                        f"Must be one of: {', '.join(sorted(VALID_DIETARY_RESTRICTIONS))}"
            )
        # Remove duplicates
        if normalized_value not in seen:
            normalized.append(normalized_value)
            seen.add(normalized_value)
    return normalized
def _validate_prep_time(prep_time_max: Optional[int]) -> Optional[int]:
    """
    Validate prep time maximum filter.
    Rules:
    - None → None (no prep time filter)
    - Must be positive integer (≥1 minute)
    - Must be ≤MAX_PREP_TIME
    Args:
        prep_time_max: Maximum prep time in minutes (may be None)
    Returns:
        Validated prep time or None
    Raises:
        ValidationError: If prep time is invalid
    """
    if prep_time_max is None:
        return None
    if prep_time_max < MIN_PREP_TIME:
        raise ValidationError(
            field="prep_time_max",
            value=prep_time_max,
            message=f"Prep time must be at least {MIN_PREP_TIME} minute"
        )
    if prep_time_max > MAX_PREP_TIME:
        raise ValidationError(
            field="prep_time_max",
            value=prep_time_max,
            message=f"Prep time must be at most {MAX_PREP_TIME} minutes"
        )
    return prep_time_max
def _validate_difficulty(difficulty: Optional[str]) -> Optional[str]:
    """
    Validate difficulty filter.
    Rules:
    - None → None (no difficulty filter)
    - Must be in VALID_DIFFICULTIES: {"easy", "medium", "hard"}
    - Normalized to lowercase
    Args:
        difficulty: Raw difficulty string from request (may be None)
    Returns:
        Normalized difficulty string or None
    Raises:
        ValidationError: If difficulty is invalid
    """
    if difficulty is None:
        return None
    normalized = difficulty.strip().lower()
    if normalized not in VALID_DIFFICULTIES:
        raise ValidationError(
            field="difficulty",
            value=difficulty,
            message=f"Invalid difficulty. Must be one of: {', '.join(sorted(VALID_DIFFICULTIES))}"
        )
    return normalized
def _validate_min_rating(min_rating: Optional[float]) -> float:
    """
    Validate minimum rating filter.
    Rules:
    - None → 0.0 (no rating filter, search all)
    - Must be in range [0.0, 5.0]
    - Rounded to 1 decimal place
    Args:
        min_rating: Minimum rating threshold (may be None)
    Returns:
        Validated rating (never None, default 0.0)
    Raises:
        ValidationError: If rating is out of valid range
    """
    # Default to 0.0 (no filter)
    if min_rating is None:
        return 0.0
    # Round to 1 decimal place
    rounded = round(min_rating, 1)
    if rounded < MIN_RATING or rounded > MAX_RATING:
        raise ValidationError(
            field="min_rating",
            value=min_rating,
            message=f"Rating must be between {MIN_RATING} and {MAX_RATING}"
        )
    return rounded
def _validate_page(page: Optional[int]) -> int:
    """
    Validate page number for pagination.
    Rules:
    - None → DEFAULT_PAGE (1)
    - Must be ≥1
    Args:
        page: Page number (may be None)
    Returns:
        Validated page number (never None, default 1)
    Raises:
        ValidationError: If page < 1
    """
    # Default to first page
    if page is None:
        return DEFAULT_PAGE
    if page < MIN_PAGE:
        raise ValidationError(
            field="page",
            value=page,
            message=f"Page must be at least {MIN_PAGE}"
        )
    return page
def _validate_page_size(page_size: Optional[int]) -> int:
    """
    Validate page size for pagination.
    Rules:
    - None → DEFAULT_PAGE_SIZE (50)
    - Must be in range [1, MAX_PAGE_SIZE]
    - MAX_PAGE_SIZE prevents abuse (e.g., requesting 10000 results)
    Args:
        page_size: Number of results per page (may be None)
    Returns:
        Validated page size (never None, default 50)
    Raises:
        ValidationError: If page size is out of valid range
    """
    # Default to standard page size
    if page_size is None:
        return DEFAULT_PAGE_SIZE
    if page_size < MIN_PAGE_SIZE:
        raise ValidationError(
            field="page_size",
            value=page_size,
            message=f"Page size must be at least {MIN_PAGE_SIZE}"
        )
    if page_size > MAX_PAGE_SIZE:
        raise ValidationError(
            field="page_size",
            value=page_size,
            message=f"Page size must be at most {MAX_PAGE_SIZE}"
        )
    return page_size

