"""
Data Model: Module Interface Contracts

All dataclasses use frozen=True for immutability and type safety.
These types define the interfaces between the 4 search modules.

Data Flow:
    SearchRequest → ValidatedSearchInput → FilteredRecipes → RankedResults → SearchResponse
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from models import Recipe


@dataclass(frozen=True)
class SearchRequest:
    """
    Raw, untrusted input from API layer.
    
    All fields are Optional because API may send incomplete data.
    validation_module is responsible for normalizing and validating.
    """
    query: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None  # Can be None! (Issue #447)
    prep_time_max: Optional[int] = None
    difficulty: Optional[str] = None
    min_rating: Optional[float] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 50


@dataclass(frozen=True)
class ValidatedSearchInput:
    """
    Validated and normalized search parameters.
    
    All Optional fields from SearchRequest have been validated.
    dietary_restrictions is NEVER None (Issue #447 fix).
    
    Guarantees:
    - query: Always string (empty if None), max 500 chars, safe for DB
    - dietary_restrictions: ALWAYS list (never None), fixes Issue #447
    - page: Always ≥1
    - page_size: Always 1-200
    - min_rating: Always 0.0-5.0
    - user_id: Always populated
    """
    query: str  # Never None, max 500 chars, trimmed, lowercased
    cuisine: Optional[str]  # Validated or None
    dietary_restrictions: List[str]  # NEVER None, always list (may be empty)
    prep_time_max: Optional[int]  # Positive int or None
    difficulty: Optional[str]  # One of: easy/medium/hard or None
    min_rating: float  # 0.0-5.0, never None (default 0.0)
    page: int  # ≥1, never None
    page_size: int  # 1-200, never None
    user_id: str  # For caching and logging


@dataclass(frozen=True)
class FilteredRecipes:
    """
    Recipes after all filters applied.
    
    Includes metadata about which filters were applied and performance metrics.
    """
    recipes: List[Recipe]  # Recipes matching all filters (may be empty)
    applied_filters: Dict[str, Any]  # Which filters were applied
    filter_duration_ms: float  # Performance metric for filtering
    total_before_filters: int  # Total recipes before filtering (for metrics)


@dataclass(frozen=True)
class RankedResults:
    """
    Recipes after ranking and pagination.
    
    Includes cache hit information and performance metrics.
    """
    recipes: List[Recipe]  # Top N recipes for the requested page
    total_results: int  # Total matching recipes (before pagination)
    page: int  # Current page number
    page_size: int  # Results per page
    total_pages: int  # Total pages available
    cache_hit: bool  # Whether results came from cache
    ranking_duration_ms: float  # Performance metric for ranking
    cache_key: str  # Cache key used (for debugging)


@dataclass(frozen=True)
class SearchResponse:
    """
    Final formatted response for API layer.
    
    100% backward compatible with legacy search.py response format.
    """
    results: List[Dict[str, Any]]  # Recipes formatted as dicts
    pagination: Dict[str, Any]  # Pagination metadata
    metadata: Dict[str, Any]  # Performance and debugging metadata
    total_duration_ms: float  # End-to-end search duration
