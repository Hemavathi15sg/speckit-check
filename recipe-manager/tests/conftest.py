"""
Pytest Configuration and Fixtures for FlavorHub Tests

This file defines shared test fixtures and configuration.
Imported by all test modules.
"""
import pytest
from uuid import uuid4
from models import User, Recipe


@pytest.fixture
def sample_user_with_dietary():
    """User with dietary restrictions (Alice)"""
    return User(
        id=uuid4(),
        name="Alice",
        email="alice@example.com",
        dietary_restrictions=["vegetarian", "nut-free"]
    )


@pytest.fixture
def sample_user_without_dietary():
    """User without dietary restrictions - triggers NULL_DIETARY_BUG (Bob)"""
    return User(
        id=uuid4(),
        name="Bob",
        email="bob@example.com",
        dietary_restrictions=None  # ← This triggers the bug
    )


@pytest.fixture
def sample_recipe():
    """Sample recipe for testing"""
    return Recipe(
        id=uuid4(),
        name="Spaghetti Carbonara",
        ingredients=["pasta", "eggs", "bacon", "parmesan"],
        dietary_tags=[],
        cuisine="Italian",
        prep_time_minutes=25,
        difficulty="intermediate",
        avg_rating=4.5
    )


@pytest.fixture
def vegetarian_recipe():
    """Vegetarian recipe"""
    return Recipe(
        id=uuid4(),
        name="Vegetable Stir Fry",
        ingredients=["broccoli", "carrots", "soy sauce", "ginger"],
        dietary_tags=["vegetarian", "vegan"],
        cuisine="Asian",
        prep_time_minutes=15,
        difficulty="easy",
        avg_rating=4.2
    )


@pytest.fixture
def sample_search_request():
    """Sample search request"""
    return {
        "query": "pasta",
        "cuisine": "Italian",
        "max_prep_time": 30
    }
