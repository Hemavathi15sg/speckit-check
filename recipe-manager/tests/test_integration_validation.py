"""
Integration tests for search.py + validation_module.py integration.

Tests that the validation module fix for Issue #447 works correctly
when integrated with the legacy search.py module.
"""
import pytest
import os
import sys
import importlib.util
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import search.py module directly (not the search/ package)
search_py_path = parent_dir / "search.py"
spec = importlib.util.spec_from_file_location("search_legacy", search_py_path)
if spec is None or spec.loader is None:
    raise ImportError("Could not load search.py module")
search_legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search_legacy)

from models import User, SAMPLE_RECIPES


class TestValidationModuleIntegration:
    """Test that validation module correctly integrates with search.py"""
    
    def test_dietary_restrictions_none_with_validation_enabled(self, monkeypatch):
        """
        Issue #447: Verify that user with dietary_restrictions=None
        doesn't crash when USE_NEW_VALIDATION=true
        """
        # Enable validation module
        monkeypatch.setenv("USE_NEW_VALIDATION", "true")
        
        # Create user with None dietary restrictions (23% of users)
        user = User(id=uuid4(), name="Test User", email="test@example.com", dietary_restrictions=None)
        
        # Search request
        request_data = {
            "query": "pasta",
            "cuisine": None,
            "dietary_restrictions": None,
            "max_prep_time": None,
            "difficulty": None,
            "min_rating": None
        }
        
        # MUST NOT crash with TypeError
        result = search_legacy.search_recipes(request_data, user)
        
        # Verify we got results
        assert isinstance(result, dict)
        assert "results" in result
        assert "total" in result
        assert result["total"] >= 0
    
    def test_dietary_restrictions_with_validation_disabled(self, monkeypatch):
        """Verify fallback to legacy behavior when validation disabled"""
        # Disable validation module
        monkeypatch.setenv("USE_NEW_VALIDATION", "false")
        
        # Create user with empty list (works in legacy)
        user = User(id=uuid4(), name="Test User", email="test@example.com", dietary_restrictions=[])
        
        request_data = {
            "query": "pasta",
            "dietary_restrictions": []
        }
        
        # Should work with legacy validation
        result = search_legacy.search_recipes(request_data, user)
        
        assert isinstance(result, dict)
        assert "results" in result
    
    def test_validated_dietary_restrictions_passed_to_filter(self, monkeypatch):
        """Verify that validated restrictions from validation module reach filter_by_dietary"""
        # Enable validation module
        monkeypatch.setenv("USE_NEW_VALIDATION", "true")
        
        # User with dietary restrictions
        user = User(id=uuid4(), name="Test User", email="test@example.com", dietary_restrictions=["vegan"])
        
        request_data = {
            "query": "",
            "dietary_restrictions": ["vegan", "gluten-free"]
        }
        
        # Search should use validated restrictions (normalized)
        result = search_legacy.search_recipes(request_data, user)
        
        # Verify filtering worked
        assert isinstance(result, dict)
        assert "results" in result
        
        # All results should match the dietary restrictions
        for recipe_dict in result["results"]:
            tags = recipe_dict.get("dietary_tags", [])
            # At least one restriction should be present
            assert any(restriction in tags for restriction in ["vegan", "gluten-free"])
    
    def test_validation_error_fallback_to_legacy(self, monkeypatch):
        """Verify that validation errors gracefully fall back to legacy parsing"""
        # Enable validation module
        monkeypatch.setenv("USE_NEW_VALIDATION", "true")
        
        # User with valid restrictions
        user = User(id=uuid4(), name="Test User", email="test@example.com", dietary_restrictions=[])
        
        # Invalid request data that might trigger validation error
        request_data = {
            "query": "",  # Empty query
            "page": -1,  # Invalid page
            "page_size": 0  # Invalid page size
        }
        
        # Should fall back to legacy and handle gracefully
        result = search_legacy.search_recipes(request_data, user)
        
        # Should still get a valid response (legacy fallback)
        assert isinstance(result, dict)
