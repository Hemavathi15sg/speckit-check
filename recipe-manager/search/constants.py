"""
Search Module Constants

Extracted from legacy search.py magic numbers (74 total).
Centralized for maintainability and testability.

Constitution Principle V: Maintainability
- All magic numbers extracted and named
- Clear documentation of valid values
- Easy to update without code changes
"""

from typing import Set

# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

# Valid cuisine types
VALID_CUISINES: Set[str] = {
    "Italian",
    "Chinese",
    "Mexican",
    "Indian",
    "Thai",
    "Japanese",
    "American",
    "French",
    "Mediterranean",
    "Korean",
}

# Valid dietary restriction tags
VALID_DIETARY_RESTRICTIONS: Set[str] = {
    "vegetarian",
    "vegan",
    "gluten-free",
    "dairy-free",
    "nut-free",
    "keto",
    "paleo",
    "low-carb",
}

# Valid difficulty levels
VALID_DIFFICULTIES: Set[str] = {
    "easy",
    "medium",
    "hard",
}

# Query validation limits
MAX_QUERY_LENGTH: int = 500  # Maximum characters in search query
MIN_QUERY_LENGTH: int = 0  # Minimum query length (0 = search all)

# Rating validation
MIN_RATING: float = 0.0  # Minimum recipe rating
MAX_RATING: float = 5.0  # Maximum recipe rating

# Prep time validation
MIN_PREP_TIME: int = 1  # Minimum prep time in minutes
MAX_PREP_TIME: int = 9999  # Maximum prep time in minutes

# Pagination validation
MIN_PAGE: int = 1  # First page number
DEFAULT_PAGE: int = 1  # Default page if not specified
MIN_PAGE_SIZE: int = 1  # Minimum results per page
MAX_PAGE_SIZE: int = 200  # Maximum results per page (prevent abuse)
DEFAULT_PAGE_SIZE: int = 50  # Default results per page

# ============================================================================
# FILTERING CONSTANTS
# ============================================================================

# Filter execution order (optimized for performance)
FILTER_ORDER = [
    "cuisine",  # Fast: single field equality check
    "difficulty",  # Fast: single field equality check
    "prep_time",  # Fast: single field numeric comparison
    "rating",  # Fast: single field numeric comparison
    "dietary_restrictions",  # Medium: set intersection
    "query",  # Slow: text search across multiple fields
]

# Text search fields (for query filtering)
SEARCHABLE_FIELDS = [
    "name",
    "ingredients",
    "dietary_tags",
]

# ============================================================================
# AGGREGATION/CACHING CONSTANTS
# ============================================================================

# LRU cache configuration (fixes Issue #183)
MAX_CACHE_SIZE: int = 1000  # Maximum number of cached search results
CACHE_TTL_SECONDS: int = 300  # Cache entry time-to-live (5 minutes)

# Ranking algorithm weights (hybrid_v3)
RANKING_WEIGHT_TEXT_MATCH: float = 0.4  # 40% weight for text relevance
RANKING_WEIGHT_QUALITY: float = 0.3  # 30% weight for recipe rating
RANKING_WEIGHT_POPULARITY: float = 0.3  # 30% weight for views/favorites

# Text matching scoring
TEXT_MATCH_EXACT: float = 10.0  # Score for exact query match in name
TEXT_MATCH_PARTIAL: float = 5.0  # Score for partial match in name
TEXT_MATCH_INGREDIENT: float = 3.0  # Score for match in ingredients
TEXT_MATCH_TAG: float = 2.0  # Score for match in dietary tags

# ============================================================================
# PERFORMANCE TARGETS (for monitoring)
# ============================================================================

# Target latencies (P50)
TARGET_VALIDATION_LATENCY_MS: float = 5.0
TARGET_FILTERING_LATENCY_MS: float = 20.0
TARGET_AGGREGATION_LATENCY_MS: float = 5.0  # Cache hit
TARGET_AGGREGATION_CACHE_MISS_LATENCY_MS: float = 30.0
TARGET_FORMATTING_LATENCY_MS: float = 5.0
TARGET_TOTAL_LATENCY_MS: float = 100.0  # End-to-end

# Cache performance targets
TARGET_CACHE_HIT_RATE: float = 0.60  # 60% of requests should hit cache

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Environment variable names for gradual rollout
FLAG_USE_NEW_VALIDATION: str = "USE_NEW_VALIDATION"
FLAG_USE_NEW_FILTERING: str = "USE_NEW_FILTERING"
FLAG_USE_NEW_AGGREGATION: str = "USE_NEW_AGGREGATION"
FLAG_USE_NEW_FORMATTING: str = "USE_NEW_FORMATTING"

# Default feature flag states (disabled until tested)
DEFAULT_FLAG_STATE: bool = False
