"""
FlavorHub Search Input Validation Module

Provides a Pydantic model for incoming search requests and a helper that
normalises raw request dicts into validated, typed filter maps.

Using Pydantic replaces the ad-hoc dict parsing in the original search.py
and catches bad input (wrong types, out-of-range values) at the API boundary
before it reaches filtering or ranking logic.
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


VALID_DIFFICULTIES = {"beginner", "easy", "intermediate", "advanced", "hard"}
MIN_RATING_VALUE: float = 0.0
MAX_RATING_VALUE: float = 5.0
MAX_PREP_TIME_LIMIT: int = 1440  # 24 hours in minutes


class SearchRequest(BaseModel):
    """Validated search request model."""

    query: str = Field(default="", max_length=200)
    cuisine: Optional[str] = Field(default=None, max_length=100)
    max_prep_time: Optional[int] = Field(default=None, ge=1, le=MAX_PREP_TIME_LIMIT)
    difficulty: Optional[str] = Field(default=None)
    min_rating: float = Field(default=MIN_RATING_VALUE, ge=MIN_RATING_VALUE, le=MAX_RATING_VALUE)
    dietary_restrictions: Optional[List[str]] = Field(default=None)

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in VALID_DIFFICULTIES:
            raise ValueError(
                f"difficulty must be one of {sorted(VALID_DIFFICULTIES)}, got '{v}'"
            )
        return v.lower() if v else v

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


def parse_and_validate(request_data: dict) -> dict:
    """
    Parse and validate a raw request dict against SearchRequest.

    Returns a plain dict of validated filter values ready for use by
    the filtering layer.
    """
    validated = SearchRequest.model_validate(request_data)
    return {
        "query": validated.query,
        "cuisine": validated.cuisine,
        "max_prep_time": validated.max_prep_time,
        "difficulty": validated.difficulty,
        "min_rating": validated.min_rating,
        "dietary_restrictions": validated.dietary_restrictions,
    }
