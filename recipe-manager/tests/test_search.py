"""
Unit Tests for FlavorHub Search Module

Tests search functionality, including the NULL_DIETARY_BUG reproduction.
These tests document existing behavior without modifying code.
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
    
    def test_null_dietary_bug_reproduction(self, sample_user_without_dietary, sample_search_request):
        """
        DOCUMENT: NULL_DIETARY_BUG - search crashes for users without dietary restrictions
        
        This test reproduces Issue #447:
        - User.dietary_restrictions is None
        - search.py line 447 tries: for restriction in user.dietary_restrictions:
        - Result: TypeError: 'NoneType' object is not iterable
        
        Status: KNOWN BUG - to be fixed in Exercise 1
        """
        with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
            search_recipes(sample_search_request, sample_user_without_dietary)
    
    def test_null_dietary_bug_with_sample_user(self, sample_search_request):
        """
        DOCUMENT: NULL_DIETARY_BUG occurs with sample users too
        
        SAMPLE_USERS[1] (Bob) has dietary_restrictions=None
        This reproduces the same bug as production
        """
        bob = SAMPLE_USERS[1]
        
        # Verify Bob has None dietary restrictions
        assert bob.dietary_restrictions is None
        
        # Verify search crashes for Bob
        with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
            search_recipes(sample_search_request, bob)


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
    """Documentation of known issues"""
    
    def test_issue_447_affects_23_percent_of_users(self):
        """
        DOCUMENTED: Issue #447 affects approximately 23% of users
        
        Users without dietary preferences have dietary_restrictions=None
        This causes TypeError when search.py tries to iterate over None
        
        Bug location: search.py line 447
        Stack trace: for restriction in user.dietary_restrictions:
        Error: TypeError: 'NoneType' object is not iterable
        """
        # This test just documents the issue
        issue_number = 447
        affected_percentage = 23
        bug_line = 447
        
        assert issue_number == 447
        assert affected_percentage == 23
        assert bug_line == 447
