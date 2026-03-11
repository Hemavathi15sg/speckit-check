"""
Contract Tests for Validation Module

Tests interface guarantees between validation_module and downstream modules.
These tests enforce the critical contract: dietary_restrictions is NEVER None.

Test Coverage Target: 100% of interface contract
Constitution Principle III: Testability

Focus: Verify ValidatedSearchInput guarantees hold for ALL inputs
"""

import pytest
from uuid import uuid4
import random
import string
from models import User
from search.types import SearchRequest, ValidatedSearchInput
from search.constants import VALID_CUISINES, VALID_DIETARY_RESTRICTIONS, VALID_DIFFICULTIES


# ============================================================================
# Contract Test Fixture: Random Input Generator
# ============================================================================

def generate_random_search_request() -> SearchRequest:
    """
    Generate a random but valid SearchRequest for contract testing.
    
    Returns requests with varying field combinations to test all paths.
    """
    # 50% chance each field is None vs. populated
    query = None if random.random() < 0.5 else ''.join(random.choices(string.ascii_letters, k=random.randint(0, 50)))
    
    cuisine = None if random.random() < 0.5 else random.choice(list(VALID_CUISINES))
    
    # CRITICAL: Test None, [], and valid lists for dietary_restrictions
    dietary_choice = random.random()
    if dietary_choice < 0.33:
        dietary_restrictions = None  # Issue #447 case
    elif dietary_choice < 0.67:
        dietary_restrictions = []  # Empty list case
    else:
        # Random subset of valid restrictions
        count = random.randint(1, 3)
        dietary_restrictions = random.sample(list(VALID_DIETARY_RESTRICTIONS), count)
    
    prep_time_max = None if random.random() < 0.5 else random.randint(10, 120)
    
    difficulty = None if random.random() < 0.5 else random.choice(list(VALID_DIFFICULTIES))
    
    min_rating = None if random.random() < 0.5 else round(random.uniform(0.0, 5.0), 1)
    
    page = random.randint(1, 10)
    page_size = random.randint(10, 100)
    
    return SearchRequest(
        query=query,
        cuisine=cuisine,
        dietary_restrictions=dietary_restrictions,
        prep_time_max=prep_time_max,
        difficulty=difficulty,
        min_rating=min_rating,
        page=page,
        page_size=page_size,
    )


def generate_random_user() -> User:
    """Generate a random user for contract testing."""
    # 50% chance of None dietary_restrictions (Issue #447)
    dietary_restrictions = None if random.random() < 0.5 else random.sample(
        list(VALID_DIETARY_RESTRICTIONS),
        random.randint(0, 3)
    )
    
    return User(
        id=uuid4(),
        name=f"User_{random.randint(1000, 9999)}",
        email=f"user{random.randint(1000, 9999)}@example.com",
        dietary_restrictions=dietary_restrictions,
    )


# ============================================================================
# CONTRACT 1: dietary_restrictions is NEVER None (Issue #447 Fix)
# ============================================================================

@pytest.mark.contract
@pytest.mark.bug
def test_contract_dietary_restrictions_never_none():
    """
    CRITICAL CONTRACT: ValidatedSearchInput.dietary_restrictions is NEVER None.
    
    This contract test runs 100 random inputs to verify the Issue #447 fix
    holds for ALL possible input combinations.
    
    If this test fails, Issue #447 will regress.
    """
    from search.validation_module import validate_search_request
    
    failures = []
    
    # Test 100 random valid inputs
    for i in range(100):
        user = generate_random_user()
        request = generate_random_search_request()
        
        try:
            result = validate_search_request(request, user)
            
            # CRITICAL: dietary_restrictions must NEVER be None
            if result.dietary_restrictions is None:
                failures.append({
                    "iteration": i,
                    "user_dietary": user.dietary_restrictions,
                    "request_dietary": request.dietary_restrictions,
                    "result_dietary": result.dietary_restrictions,
                    "error": "dietary_restrictions is None (VIOLATES CONTRACT)"
                })
            
            # Must always be a list
            if not isinstance(result.dietary_restrictions, list):
                failures.append({
                    "iteration": i,
                    "type": type(result.dietary_restrictions),
                    "error": f"dietary_restrictions is not a list (got {type(result.dietary_restrictions)})"
                })
        
        except Exception as e:
            # Validation errors are acceptable, but crashes are not
            if not isinstance(e, pytest.importorskip("search.exceptions").ValidationError):
                failures.append({
                    "iteration": i,
                    "error": f"Unexpected exception: {e}"
                })
    
    # All 100 iterations must pass
    assert len(failures) == 0, f"Contract violations found:\n{failures}"


# ============================================================================
# CONTRACT 2: All Required Fields Are Populated
# ============================================================================

@pytest.mark.contract
def test_contract_all_required_fields_populated():
    """
    CONTRACT: All non-Optional fields in ValidatedSearchInput are always populated.
    
    Fields that MUST NEVER be None:
    - query (str)
    - dietary_restrictions (List[str])
    - min_rating (float)
    - page (int)
    - page_size (int)
    - user_id (str)
    """
    from search.validation_module import validate_search_request
    
    failures = []
    
    # Test 50 random valid inputs
    for i in range(50):
        user = generate_random_user()
        request = generate_random_search_request()
        
        try:
            result = validate_search_request(request, user)
            
            # Check all required fields are populated
            if result.query is None:
                failures.append({"iteration": i, "field": "query", "error": "query is None"})
            
            if result.dietary_restrictions is None:
                failures.append({"iteration": i, "field": "dietary_restrictions", "error": "dietary_restrictions is None"})
            
            if result.min_rating is None:
                failures.append({"iteration": i, "field": "min_rating", "error": "min_rating is None"})
            
            if result.page is None:
                failures.append({"iteration": i, "field": "page", "error": "page is None"})
            
            if result.page_size is None:
                failures.append({"iteration": i, "field": "page_size", "error": "page_size is None"})
            
            if result.user_id is None:
                failures.append({"iteration": i, "field": "user_id", "error": "user_id is None"})
        
        except Exception as e:
            if not isinstance(e, pytest.importorskip("search.exceptions").ValidationError):
                failures.append({"iteration": i, "error": f"Unexpected exception: {e}"})
    
    assert len(failures) == 0, f"Contract violations found:\n{failures}"


# ============================================================================
# CONTRACT 3: Immutability (frozen=True)
# ============================================================================

@pytest.mark.contract
def test_contract_immutability():
    """
    CONTRACT: ValidatedSearchInput is immutable (frozen=True).
    
    Attempting to modify any field should raise FrozenInstanceError.
    This prevents accidental mutations in downstream modules.
    """
    from search.validation_module import validate_search_request
    from dataclasses import FrozenInstanceError
    
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=["vegan"],
    )
    request = SearchRequest(query="pasta")
    
    result = validate_search_request(request, user)
    
    # Attempt to modify each field - all should raise FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        result.query = "modified"  # type: ignore
    
    with pytest.raises(FrozenInstanceError):
        result.dietary_restrictions = []  # type: ignore
    
    with pytest.raises(FrozenInstanceError):
        result.page = 999  # type: ignore
    
    with pytest.raises(FrozenInstanceError):
        result.min_rating = 10.0  # type: ignore
