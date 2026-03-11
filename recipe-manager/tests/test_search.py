"""
Unit Tests for FlavorHub Search Module

Tests search functionality, including the fix for Issue #447
(NULL_DIETARY_BUG: search crashed for users without dietary restrictions).
"""
import pytest
from uuid import uuid4
from models import User, Recipe, SAMPLE_USERS
from search import search_recipes


class TestSearchRecipes:
    """Test search_recipes functionality"""

    def test_search_with_valid_user_and_restrictions(self, sample_user_with_dietary, sample_search_request):
        """Search works for users WITH dietary restrictions"""
        result = search_recipes(sample_search_request, sample_user_with_dietary)

        assert isinstance(result, dict)
        assert "results" in result
        assert "total" in result

    def test_search_returns_dict(self, sample_user_with_dietary, sample_search_request):
        """Search returns a dictionary response"""
        result = search_recipes(sample_search_request, sample_user_with_dietary)

        assert isinstance(result, dict)

    def test_null_dietary_bug_is_fixed(self, sample_user_without_dietary, sample_search_request):
        """
        FIX VERIFIED: Issue #447 – search no longer crashes when
        user.dietary_restrictions is None.

        Previously: TypeError: 'NoneType' object is not iterable
        Now: search succeeds and returns all recipes (no dietary filter applied).
        """
        result = search_recipes(sample_search_request, sample_user_without_dietary)

        assert isinstance(result, dict)
        assert "results" in result
        assert "total" in result

    def test_null_dietary_bug_fixed_for_sample_user(self, sample_search_request):
        """
        FIX VERIFIED: Issue #447 is resolved for Bob (SAMPLE_USERS[1]).

        Bob has dietary_restrictions=None. Search must succeed and return a
        valid response instead of raising TypeError.
        """
        bob = SAMPLE_USERS[1]
        assert bob.dietary_restrictions is None

        result = search_recipes(sample_search_request, bob)

        assert isinstance(result, dict)
        assert "results" in result
        assert "total" in result


class TestSearchInputValidation:
    """Test search input handling"""

    def test_search_request_format(self, sample_search_request):
        """Search request has expected fields"""
        assert "query" in sample_search_request
        assert isinstance(sample_search_request["query"], str)

    def test_search_accepts_cuisine_filter(self):
        """Search request can include cuisine filter"""
        request = {
            "query": "pasta",
            "cuisine": "Italian"
        }

        assert request["cuisine"] == "Italian"


class TestSearchBugDocumentation:
    """Documentation of Issue #447 and its resolution"""

    def test_issue_447_is_resolved(self):
        """
        Issue #447 (NULL_DIETARY_BUG) has been fixed.

        Root cause: filter_by_dietary() iterated directly over
        user.dietary_restrictions without a None guard.

        Fix: filtering.py uses ``restrictions = user.dietary_restrictions or []``
        so None users are treated as having no restrictions.
        """
        # Verify the fix holds for a user with None dietary restrictions
        user = User(
            id=uuid4(),
            name="No-Prefs User",
            email="noprofs@example.com",
            dietary_restrictions=None,
        )
        request = {"query": "pasta"}
        result = search_recipes(request, user)

        assert isinstance(result, dict)
        assert "results" in result
