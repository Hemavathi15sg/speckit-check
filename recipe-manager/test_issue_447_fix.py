"""
Manual test for Issue #447 fix.

Test that a user with dietary_restrictions=None can successfully search
for recipes without getting a TypeError.
"""

from uuid import uuid4
from models import User
from search import SearchRequest, validate_search_request

# GIVEN: User with dietary_restrictions=None (Issue #447 scenario)
print("Creating user with dietary_restrictions=None...")
user = User(
    id=uuid4(),
    name="Test User",
    email="test@example.com",
    dietary_restrictions=None  # ← This caused TypeError in legacy code
)

# WHEN: Searching for "pasta"
print(f"User dietary_restrictions: {user.dietary_restrictions}")
print("\nSearching for 'pasta'...")

request = SearchRequest(query="pasta")
result = validate_search_request(request, user)

# THEN: No TypeError, dietary_restrictions is []
print(f"\n✓ SUCCESS: No TypeError!")
print(f"✓ dietary_restrictions normalized to: {result.dietary_restrictions}")
print(f"✓ dietary_restrictions type: {type(result.dietary_restrictions)}")
print(f"✓ dietary_restrictions is not None: {result.dietary_restrictions is not None}")

# Additional validations
assert result.dietary_restrictions == [], f"Expected [], got {result.dietary_restrictions}"
assert isinstance(result.dietary_restrictions, list), "dietary_restrictions must be a list"
assert result.query == "pasta", f"Expected 'pasta', got '{result.query}'"
assert result.page == 1, f"Expected page=1, got page={result.page}"
assert result.page_size == 50, f"Expected page_size=50, got page_size={result.page_size}"
assert result.min_rating == 0.0, f"Expected min_rating=0.0, got min_rating={result.min_rating}"

print("\n" + "="*60)
print("✓ Issue #447 FIXED!")
print("✓ All assertions passed")
print("✓ Users with dietary_restrictions=None can now search recipes")
print("="*60)
