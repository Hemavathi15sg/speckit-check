"""
API Routes for FlavorHub Recipe Manager

"""
import time
import logging
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, Dict, Any
from models import SAMPLE_USERS, User
from search import search_recipes
from logging_config import (
    get_logger,
    get_correlation_id,
    log_search_start,
    log_search_end,
    log_error,
)

router = APIRouter()
logger = get_logger(__name__)


def get_user_from_token(authorization: Optional[str] = Header(None)) -> User:
    """
    In workshop: Gets user with dietary_restrictions=None to trigger bug
    """
    if not authorization:
        # Default to Bob (has dietary_restrictions=None) - triggers the bug!
        return SAMPLE_USERS[1]
    
    # In real app: decode JWT, lookup user, etc.
    # For workshop: just return Bob (the problematic user)
    return SAMPLE_USERS[1]


@router.post("/search")
async def search_endpoint(
    request_data: dict,
    current_user: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Search recipes endpoint.
    
    THIS IS WHERE THE BUG HAPPENS in production!
    
    When request comes from user without dietary preferences,
    search.py line 447 crashes.
    
    Example request that crashes:
    {
        "query": "Bob",
        "dietary_restrictions": null,
        "cuisine": "Italian"
    }
    """
    # Map user name to actual user object
    if current_user:
        user_name_lower = current_user.lower()
        user = next((u for u in SAMPLE_USERS if u.name.lower() == user_name_lower), None)
        if not user:
            log_error(
                logger,
                "USER_NOT_FOUND",
                "User not found: %s" % current_user,
                user_name=current_user,
                correlation_id=get_correlation_id(),
            )
            raise HTTPException(status_code=404, detail="User not found")
    else:
        user = get_user_from_token()

    query = request_data.get("query", "")
    user_id = str(user.id)

    log_search_start(logger, query, user_id)
    start = time.perf_counter()

    try:
        results = search_recipes(request_data, user)
        duration_ms = (time.perf_counter() - start) * 1000
        results_count = len(results.get("recipes", results.get("results", [])))
        log_search_end(logger, query, user_id, results_count, duration_ms)
        return results

    except TypeError as e:
        duration_ms = (time.perf_counter() - start) * 1000
        if "'NoneType' object is not iterable" in str(e):
            log_error(
                logger,
                "NULL_DIETARY_BUG",
                "Search crashed – user.dietary_restrictions is None (Issue #447)",
                exc=e,
                user_id=user_id,
                query=query,
                duration_ms=duration_ms,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error in search filtering"
            )
        log_error(
            logger,
            "SEARCH_TYPE_ERROR",
            "Unexpected TypeError during search",
            exc=e,
            user_id=user_id,
            query=query,
            duration_ms=duration_ms,
        )
        raise

    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        log_error(
            logger,
            "SEARCH_UNEXPECTED_ERROR",
            "Unexpected error during search",
            exc=e,
            user_id=user_id,
            query=query,
            duration_ms=duration_ms,
        )
        raise


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    logger.debug("Health check requested", extra={"event": "health_check"})
    return {"status": "ok", "service": "recipe-search"}
