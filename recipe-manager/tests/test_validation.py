"""
Unit Tests for the Validation Module (validation.py)
"""
import pytest
from pydantic import ValidationError

from validation import SearchRequest, parse_and_validate


class TestSearchRequest:
    def test_defaults_are_safe(self):
        req = SearchRequest()
        assert req.query == ""
        assert req.cuisine is None
        assert req.max_prep_time is None
        assert req.difficulty is None
        assert req.min_rating == 0.0

    def test_valid_request(self):
        req = SearchRequest(
            query="pasta",
            cuisine="Italian",
            max_prep_time=30,
            difficulty="intermediate",
            min_rating=4.0,
        )
        assert req.query == "pasta"
        assert req.max_prep_time == 30

    def test_difficulty_normalised_to_lowercase(self):
        req = SearchRequest(difficulty="BEGINNER")
        assert req.difficulty == "beginner"

    def test_invalid_difficulty_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(difficulty="super-hard")

    def test_min_rating_above_five_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(min_rating=5.1)

    def test_negative_min_rating_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(min_rating=-0.1)

    def test_negative_prep_time_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(max_prep_time=-10)

    def test_query_whitespace_is_stripped(self):
        req = SearchRequest(query="  pasta  ")
        assert req.query == "pasta"


class TestParseAndValidate:
    def test_returns_dict(self):
        result = parse_and_validate({"query": "soup"})
        assert isinstance(result, dict)

    def test_all_required_keys_present(self):
        result = parse_and_validate({})
        for key in ("query", "cuisine", "max_prep_time", "difficulty",
                    "min_rating", "dietary_restrictions"):
            assert key in result

    def test_invalid_input_raises(self):
        with pytest.raises(ValidationError):
            parse_and_validate({"min_rating": 99})
