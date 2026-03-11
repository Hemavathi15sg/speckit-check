"""
Test script to reproduce Issue #447

This demonstrates the production bug that crashes search
for users without dietary restrictions.
"""
import importlib.util
import sys
from pathlib import Path
from uuid import uuid4
from models import User, SAMPLE_USERS

# Fix Windows encoding issue for emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # type: ignore

# Load search.py directly (workaround for search/ package name collision)
search_py_path = Path(__file__).parent / "search.py"
spec = importlib.util.spec_from_file_location("search_legacy", search_py_path)
if spec is None or spec.loader is None:
    raise ImportError("Could not load search.py module")
search_legacy = importlib.util.module_from_spec(spec)
sys.modules['search_legacy'] = search_legacy
spec.loader.exec_module(search_legacy)

# Now we can use search_recipes from the loaded module
search_recipes = search_legacy.search_recipes


def test_bug_with_null_dietary():
    """
    Reproduce Issue #447: TypeError when dietary_restrictions is None
    
    Expected: TypeError: 'NoneType' object is not iterable
    Location: search.py, line 447
    """
    print("🧪 Testing search with user who has dietary_restrictions=None...")
    print()
    
    # Create user with None dietary restrictions (like Bob in SAMPLE_USERS)
    user = User(
        id=uuid4(),
        name="Test User",
        email="test@example.com",
        dietary_restrictions=None  # ← This causes the crash!
    )
    
    # Simple search request
    request = {
        "query": "pasta",
        "cuisine": "Italian"
    }
    
    print(f"User: {user.name}")
    print(f"Dietary restrictions: {user.dietary_restrictions}")
    print(f"Search query: {request['query']}")
    print()
    
    try:
        results = search_recipes(request, user)
        print("✅ Search succeeded!")
        print(f"Found {results['total']} recipes")
    except TypeError as e:
        print("❌ CRASH! (This is Issue #447)")
        print(f"Error: {e}")
        print()
        print("Stack trace points to search.py line 447:")
        print("  for restriction in user.dietary_restrictions:")
        print("  TypeError: 'NoneType' object is not iterable")
        print()
        print("💡 This is the bug you'll fix in the workshop!")
        return False
    
    return True


def test_bug_with_sample_user():
    """Test with Bob from SAMPLE_USERS (also has None)"""
    print("\n" + "="*60)
    print("🧪 Testing with Bob (SAMPLE_USERS[1])...")
    print()
    
    user = SAMPLE_USERS[1]  # Bob has dietary_restrictions=None
    
    request = {
        "query": "pasta",
        "cuisine": None
    }
    
    print(f"User: {user.name}")
    print(f"Dietary restrictions: {user.dietary_restrictions}")
    print()
    
    try:
        results = search_recipes(request, user)
        print("✅ Search succeeded!")
        print(f"Found {results['total']} recipes")
        return True
    except TypeError as e:
        print("❌ CRASH! Same issue as production")
        print(f"Error: {e}")
        return False


def test_working_case():
    """Test with user who HAS dietary restrictions (works fine)"""
    print("\n" + "="*60)
    print("🧪 Testing with Alice (has dietary restrictions)...")
    print()
    
    user = SAMPLE_USERS[0]  # Alice has dietary_restrictions=["vegan"]
    
    request = {
        "query": "bowl",
        "cuisine": None
    }
    
    print(f"User: {user.name}")
    print(f"Dietary restrictions: {user.dietary_restrictions}")
    print()
    
    try:
        results = search_recipes(request, user)
        print("✅ Search succeeded!")
        print(f"Found {results['total']} recipes")
        for r in results['results']:
            print(f"  - {r['name']} ({r['dietary_tags']})")
        return True
    except TypeError as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    import os
    
    print("="*60)
    print("FlavorHub Issue #447 Reproduction Test")
    print("="*60)
    print()
    print("This script demonstrates the production bug that affects")
    print("30% of searches (users without dietary restrictions).")
    print()
    
    # Check if validation module fix is enabled
    validation_enabled = os.getenv("USE_NEW_VALIDATION", "false").lower() == "true"
    
    # Run tests
    working = test_working_case()  # This works
    null_test = test_bug_with_null_dietary()  # Fixed with validation module
    sample_test = test_bug_with_sample_user()  # Fixed with validation module
    
    print("\n" + "="*60)
    print("Summary:")
    print("  ✅ Users WITH dietary preferences: Search works")
    
    if null_test and sample_test:
        print("  ✅ Users WITHOUT dietary preferences: Search works (FIXED!)")
        print()
        if validation_enabled:
            print("✅ Issue #447 FIXED via validation module (USE_NEW_VALIDATION=true)")
        else:
            print("✅ Issue #447 FIXED via inline null check in filter_by_dietary()")
    else:
        print("  ❌ Users WITHOUT dietary preferences: Search crashes")
        print()
        print("Follow the workshop to fix this using GitHub agents!")
    print("="*60)
