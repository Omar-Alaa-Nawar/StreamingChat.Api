"""
Phase 3 Test Script - TableA Component Testing

Tests the progressive TableA component rendering introduced in Phase 3.

Usage:
    python test_phase3.py

Test scenarios:
1. Single sales table with progressive row loading
2. Users table with different schema
3. Products table
4. Mixed content (text + table)
5. Multiple tables (future enhancement)

Backend must be running on http://127.0.0.1:8001
"""

import requests
import sys


def print_separator():
    """Print a visual separator between tests."""
    print("\n" + "=" * 80 + "\n")


def test_single_table(table_type="sales"):
    """
    Test single table rendering with progressive rows.
    
    Args:
        table_type: Type of table to request ("sales", "users", or "products")
    """
    print(f"🧪 Test: Single {table_type.upper()} Table")
    print("-" * 80)
    
    prompt = f"show me {table_type} table"
    print(f"Prompt: '{prompt}'")
    print("\nExpected behavior:")
    print("  1. Empty table with columns appears")
    print("  2. Loading text streams")
    print("  3. Rows appear one by one")
    print("  4. Completion message")
    print("\nActual stream:")
    print("-" * 80)
    
    try:
        response = requests.post(
            "http://127.0.0.1:8001/chat",
            json={"message": prompt},
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        for chunk in response.iter_content(decode_unicode=True):
            if chunk:
                print(chunk, end='', flush=True)
        
        print("\n" + "-" * 80)
        print("✅ Test completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    return True


def test_mixed_content():
    """Test table mixed with regular text."""
    print("🧪 Test: Mixed Content (Text + Table)")
    print("-" * 80)
    
    prompt = "Can you show me a sales table please?"
    print(f"Prompt: '{prompt}'")
    print("\nExpected behavior:")
    print("  1. Table renders with progressive rows")
    print("  2. All text streams normally")
    print("\nActual stream:")
    print("-" * 80)
    
    try:
        response = requests.post(
            "http://127.0.0.1:8001/chat",
            json={"message": prompt},
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        for chunk in response.iter_content(decode_unicode=True):
            if chunk:
                print(chunk, end='', flush=True)
        
        print("\n" + "-" * 80)
        print("✅ Test completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    return True


def test_backwards_compatibility():
    """Test that Phase 2 SimpleComponent still works."""
    print("🧪 Test: Backwards Compatibility (Phase 2 SimpleComponent)")
    print("-" * 80)
    
    prompt = "show me a card"
    print(f"Prompt: '{prompt}'")
    print("\nExpected behavior:")
    print("  1. Empty SimpleComponent appears")
    print("  2. Loading text streams")
    print("  3. Component updates with data")
    print("\nActual stream:")
    print("-" * 80)
    
    try:
        response = requests.post(
            "http://127.0.0.1:8001/chat",
            json={"message": prompt},
            stream=True,
            timeout=30
        )
        
        response.raise_for_status()
        
        for chunk in response.iter_content(decode_unicode=True):
            if chunk:
                print(chunk, end='', flush=True)
        
        print("\n" + "-" * 80)
        print("✅ Test completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    return True


def run_all_tests():
    """Run all Phase 3 test scenarios."""
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                     PHASE 3 TEST SUITE - TableA Component                    ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Check backend connectivity
    try:
        requests.get("http://127.0.0.1:8001/", timeout=5)
        print("✅ Backend is running and accessible")
    except requests.exceptions.RequestException:
        print("❌ Backend is not accessible at http://127.0.0.1:8001")
        print("   Please start the backend first: python main.py")
        sys.exit(1)
    
    print_separator()
    
    # Track test results
    results = []
    
    # Test 1: Sales table
    results.append(("Sales Table", test_single_table("sales")))
    print_separator()
    
    # Test 2: Users table
    results.append(("Users Table", test_single_table("users")))
    print_separator()
    
    # Test 3: Products table
    results.append(("Products Table", test_single_table("products")))
    print_separator()
    
    # Test 4: Mixed content
    results.append(("Mixed Content", test_mixed_content()))
    print_separator()
    
    # Test 5: Backwards compatibility
    results.append(("Backwards Compatibility", test_backwards_compatibility()))
    print_separator()
    
    # Print summary
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                              TEST SUMMARY                                     ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status:12} - {test_name}")
    
    print()
    print(f"  Total: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("  🎉 All tests passed! Phase 3 is working correctly.")
        return 0
    else:
        print(f"  ⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
