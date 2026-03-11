"""
API Routes for FlavorHub Recipe Manager

"""
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, Dict, Any
from models import SAMPLE_USERS, User
from search import search_recipes

router = APIRouter()


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
            raise HTTPException(status_code=404, detail="User not found")
    else:
        user = get_user_from_token()
    
    try:
        # This is where it crashes!
        results = search_recipes(request_data, user)
        return results
    
    except TypeError as e:
        # Production error logs show this:
        if "'NoneType' object is not iterable" in str(e):
            raise HTTPException(
                status_code=500,
                detail="Internal server error in search filtering"
            )
        raise


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "service": "recipe-search"}
