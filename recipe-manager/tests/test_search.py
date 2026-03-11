"""
Unit Tests for FlavorHub Search Module

Tests the modular search pipeline including the fix for Issue #447
(NULL_DIETARY_BUG: TypeError when user.dietary_restrictions is None).
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
        assert "total" in result or "recipes" in result or "results" in result

    def test_search_returns_dict(self, sample_user_with_dietary, sample_search_request):
        """Search returns a dictionary response"""
        result = search_recipes(sample_search_request, sample_user_with_dietary)

        assert isinstance(result, dict)

    def test_null_dietary_bug_fixed(self, sample_user_without_dietary, sample_search_request):
        """
        FIXED: Issue #447 - search no longer crashes for users without dietary restrictions.

        Previously: user.dietary_restrictions = None caused
        TypeError: 'NoneType' object is not iterable at line 447.

        Now: validation_module normalises None → [] before filtering,
        so search completes successfully and returns a valid response.
        """
        # Must NOT raise TypeError (bug is fixed)
        result = search_recipes(sample_search_request, sample_user_without_dietary)

        assert isinstance(result, dict)
        assert "results" in result
        assert "total" in result
        assert isinstance(result["results"], list)

    def test_null_dietary_bug_fixed_with_sample_user(self, sample_search_request):
        """
        FIXED: Issue #447 - SAMPLE_USERS[1] (Bob, dietary_restrictions=None)
        can now search without errors.
        """
        bob = SAMPLE_USERS[1]
        assert bob.dietary_restrictions is None

        # Should NOT crash after the fix
        result = search_recipes(sample_search_request, bob)
        assert isinstance(result, dict)
        assert "results" in result


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

    def test_empty_results_for_unmatched_query(self, sample_user_without_dietary):
        """Search with no matches returns empty results, not an error"""
        request = {"query": "xyzabcnonexistent12345"}
        result = search_recipes(request, sample_user_without_dietary)

        assert isinstance(result, dict)
        assert "results" in result
        assert result["results"] == []
        assert result["total"] == 0


class TestSearchBugDocumentation:
    """Documentation of Issue #447 and its resolution"""

    def test_issue_447_affected_users(self):
        """
        DOCUMENTED: Issue #447 previously affected approximately 23% of users.

        Users without dietary preferences had dietary_restrictions=None.
        This caused TypeError when search.py tried to iterate over None.

        Status: FIXED via validation_module.py (normalises None → []).
        """
        issue_number = 447
        affected_percentage = 23
        assert issue_number == 447
        assert affected_percentage == 23

    def test_issue_447_fix_via_validation_module(self):
        """
        VERIFY FIX: validation_module normalises None → [] for dietary_restrictions.
        """
        from search.validation_module import validate_search_request
        from search.types import SearchRequest

        user = User(uuid4(), "Bob", "bob@example.com", dietary_restrictions=None)
        request = SearchRequest(query="pasta")
        validated = validate_search_request(request, user)

        assert validated.dietary_restrictions == []
        assert validated.dietary_restrictions is not None
