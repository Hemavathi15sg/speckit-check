"""
Unit Tests for Validation Module

Tests for search/validation_module.py following TDD approach.
These tests MUST FAIL initially (module not implemented yet).

Test Coverage Target: ≥90% (exceeds 80% requirement)
Constitution Principle III: Testability

Focus: Issue #447 fix - dietary_restrictions=None normalization
"""

import pytest
from uuid import uuid4
from models import User
from search.types import SearchRequest, ValidatedSearchInput
from search.exceptions import ValidationError
from search.constants import (
    VALID_CUISINES,
    VALID_DIETARY_RESTRICTIONS,
    MAX_QUERY_LENGTH,
    MAX_PAGE_SIZE,
    MAX_RATING,
    MIN_RATING,
)


# ============================================================================
# CRITICAL: Issue #447 Fix Tests (dietary_restrictions=None)
# ============================================================================

@pytest.mark.unit
@pytest.mark.bug
def test_none_dietary_restrictions_normalized_to_empty_list():
    """
    CRITICAL: Test Issue #447 fix.
    
    When user.dietary_restrictions is None, validate_search_request()
    MUST normalize it to [] (empty list) to prevent TypeError.
    
    This is the root cause fix for Issue #447 affecting 30% of users.
    """
    # GIVEN: User with None dietary_restrictions (30% of users)
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=None,  # ← Issue #447: This causes TypeError
    )
    request = SearchRequest(query="pasta")
    
    # WHEN: Validating search request
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    # THEN: dietary_restrictions is NEVER None (always list)
    assert isinstance(result.dietary_restrictions, list)
    assert result.dietary_restrictions == []
    assert result.dietary_restrictions is not None  # Explicit None check


@pytest.mark.unit
def test_empty_dietary_restrictions_preserved():
    """Empty list should be preserved as-is."""
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=[],  # Explicitly empty
    )
    request = SearchRequest(query="pasta", dietary_restrictions=[])
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    assert result.dietary_restrictions == []


@pytest.mark.unit
def test_valid_dietary_restrictions_normalized():
    """
    Valid dietary restrictions should be normalized to lowercase.
    Supports case-insensitive user input.
    """
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=None,
    )
    request = SearchRequest(
        query="pasta",
        dietary_restrictions=["Vegan", "GLUTEN-FREE"],  # Mixed case
    )
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    assert result.dietary_restrictions == ["vegan", "gluten-free"]


@pytest.mark.unit
def test_invalid_dietary_restriction_raises_error():
    """Invalid dietary restriction should raise ValidationError."""
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=None,
    )
    request = SearchRequest(
        query="pasta",
        dietary_restrictions=["invalid", "not-a-real-restriction"],
    )
    
    from search.validation_module import validate_search_request
    
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert exc_info.value.field == "dietary_restrictions"
    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.unit
def test_duplicate_dietary_restrictions_removed():
    """Duplicate dietary restrictions should be removed."""
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=None,
    )
    request = SearchRequest(
        query="pasta",
        dietary_restrictions=["vegan", "vegan", "gluten-free"],  # Duplicate "vegan"
    )
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    # Should have only unique values
    assert len(result.dietary_restrictions) == 2
    assert "vegan" in result.dietary_restrictions
    assert "gluten-free" in result.dietary_restrictions


# ============================================================================
# Query Validation Tests
# ============================================================================

@pytest.mark.unit
def test_none_query_normalized_to_empty_string():
    """None query should be normalized to empty string."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query=None)
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    assert result.query == ""
    assert result.query is not None


@pytest.mark.unit
def test_query_trimmed_and_lowercased():
    """Query should be trimmed and lowercased for consistent filtering."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="  PASTA CARBONARA  ")
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    assert result.query == "pasta carbonara"


@pytest.mark.unit
def test_query_truncated_if_too_long():
    """Query exceeding MAX_QUERY_LENGTH should be truncated."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    long_query = "x" * (MAX_QUERY_LENGTH + 100)
    request = SearchRequest(query=long_query)
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    assert len(result.query) == MAX_QUERY_LENGTH


# ============================================================================
# Cuisine Validation Tests
# ============================================================================

@pytest.mark.unit
def test_invalid_cuisine_raises_error():
    """Invalid cuisine should raise ValidationError."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="pasta", cuisine="Martian")
    
    from search.validation_module import validate_search_request
    
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert exc_info.value.field == "cuisine"


@pytest.mark.unit
def test_valid_cuisine_normalized():
    """Valid cuisine should be normalized to title case."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="pasta", cuisine="italian")
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    assert result.cuisine == "Italian"


# ============================================================================
# Prep Time Validation Tests
# ============================================================================

@pytest.mark.unit
def test_prep_time_negative_raises_error():
    """Negative prep_time should raise ValidationError."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="pasta", prep_time_max=-10)
    
    from search.validation_module import validate_search_request
    
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert exc_info.value.field == "prep_time_max"


# ============================================================================
# Pagination Validation Tests
# ============================================================================

@pytest.mark.unit
def test_page_zero_raises_error():
    """Page number <1 should raise ValidationError."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="pasta", page=0)
    
    from search.validation_module import validate_search_request
    
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert exc_info.value.field == "page"


@pytest.mark.unit
def test_page_size_exceeds_max_raises_error():
    """Page size >MAX_PAGE_SIZE should raise ValidationError."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="pasta", page_size=MAX_PAGE_SIZE + 100)
    
    from search.validation_module import validate_search_request
    
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert exc_info.value.field == "page_size"


# ============================================================================
# Rating Validation Tests
# ============================================================================

@pytest.mark.unit
def test_min_rating_out_of_range_raises_error():
    """min_rating outside 0.0-5.0 range should raise ValidationError."""
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest(query="pasta", min_rating=6.0)
    
    from search.validation_module import validate_search_request
    
    with pytest.raises(ValidationError) as exc_info:
        validate_search_request(request, user)
    
    assert exc_info.value.field == "min_rating"


# ============================================================================
# Defaults and Comprehensive Tests
# ============================================================================

@pytest.mark.unit
def test_all_defaults_applied():
    """
    When all fields are None/default, validate_search_request()
    should apply all default values correctly.
    """
    user = User(id=uuid4(), name="Test", email="test@example.com", dietary_restrictions=None)
    request = SearchRequest()  # All None/defaults
    
    from search.validation_module import validate_search_request
    result = validate_search_request(request, user)
    
    # All fields should have safe defaults
    assert result.query == ""
    assert result.cuisine is None
    assert result.dietary_restrictions == []  # CRITICAL: Never None
    assert result.prep_time_max is None
    assert result.difficulty is None
    assert result.min_rating == 0.0
    assert result.page == 1
    assert result.page_size == 50
    assert result.user_id == str(user.id)
