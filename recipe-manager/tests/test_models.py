"""
Unit Tests for FlavorHub Models

Tests the User and Recipe model classes.
These tests don't touch existing code - they test existing functionality.
"""
import pytest
from uuid import uuid4
from models import User, Recipe


class TestUserModel:
    """Test User model class"""
    
    def test_user_creation_with_dietary_restrictions(self):
        """User can be created with dietary restrictions"""
        user = User(
            id=uuid4(),
            name="Alice",
            email="alice@example.com",
            dietary_restrictions=["vegetarian"]
        )
        
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        assert user.dietary_restrictions == ["vegetarian"]
    
    def test_user_creation_without_dietary_restrictions(self):
        """User can be created without dietary restrictions (None)"""
        user = User(
            id=uuid4(),
            name="Bob",
            email="bob@example.com",
            dietary_restrictions=None
        )
        
        assert user.name == "Bob"
        assert user.dietary_restrictions is None
    
    def test_user_has_id(self):
        """User has unique ID"""
        user = User(
            id=uuid4(),
            name="Charlie",
            email="charlie@example.com",
            dietary_restrictions=None
        )
        
        assert user.id is not None
        assert isinstance(user.id, type(uuid4()))
    
    def test_user_has_created_at_timestamp(self):
        """User has created_at timestamp"""
        user = User(
            id=uuid4(),
            name="David",
            email="david@example.com",
            dietary_restrictions=None
        )
        
        assert hasattr(user, 'created_at')
        assert user.created_at is not None


class TestRecipeModel:
    """Test Recipe model class"""
    
    def test_recipe_creation(self, sample_recipe):
        """Recipe can be created with all fields"""
        assert sample_recipe.name == "Spaghetti Carbonara"
        assert sample_recipe.cuisine == "Italian"
        assert sample_recipe.prep_time_minutes == 25
        assert sample_recipe.difficulty == "intermediate"
    
    def test_recipe_dietary_tags(self):
        """Recipe can have dietary tags"""
        recipe = Recipe(
            id=uuid4(),
            name="Vegan Bowl",
            ingredients=["tofu", "vegetables"],
            dietary_tags=["vegan", "gluten-free"],
            cuisine="fusion",
            prep_time_minutes=20,
            difficulty="easy"
        )
        
        assert "vegan" in recipe.dietary_tags
        assert "gluten-free" in recipe.dietary_tags
    
    def test_recipe_has_rating(self):
        """Recipe has average rating"""
        recipe = Recipe(
            id=uuid4(),
            name="Test Recipe",
            ingredients=["ingredient"],
            dietary_tags=[],
            cuisine="test",
            prep_time_minutes=10,
            difficulty="easy",
            avg_rating=4.5
        )
        
        assert recipe.avg_rating == 4.5
