"""
Phase 6 Test Suite: LLM Integration Service

Tests for the LLMPlannerService that uses AWS Bedrock to dynamically
generate dashboard components based on natural language queries.

Run with: python test_phase6.py
"""

import asyncio
import json
import sys
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, '.')

from services.llm.llm_planner_service import LLMPlannerService


# ============================================================================
# Mock Bedrock Response Generator
# ============================================================================

def create_mock_bedrock_response(components: list) -> Dict[str, Any]:
    """Create a mock Bedrock API response."""
    component_json = json.dumps(components)
    llm_text = f"$$${component_json}$$$"

    return {
        'body': AsyncMock(read=AsyncMock(return_value=json.dumps({
            'content': [{'text': llm_text}]
        }).encode()))
    }


# ============================================================================
# Test 1: Basic Plan Generation
# ============================================================================

async def test_basic_plan_generation():
    """Test that LLM service generates a valid 3-component plan."""
    print("\n🧪 Test 1: Basic Plan Generation")

    service = LLMPlannerService()

    # Mock Bedrock response
    mock_components = [
        {
            "type": "SimpleComponent",
            "data": {
                "title": "Sales Summary",
                "description": "Total revenue increased by 12%"
            }
        },
        {
            "type": "TableA",
            "data": {
                "columns": ["Region", "Revenue"],
                "rows": [["US", 12000], ["EU", 10000]]
            }
        },
        {
            "type": "ChartComponent",
            "data": {
                "chart_type": "line",
                "title": "Revenue Trend",
                "x_axis": ["Jan", "Feb", "Mar"],
                "series": [{"label": "Sales", "values": [100, 120, 150]}]
            }
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    # Mock the Bedrock client
    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        result = await service.generate_layout("show me sales dashboard")

        # Validate result structure
        assert "components" in result, "Result should have 'components'"
        assert "from_cache" in result, "Result should have 'from_cache'"
        assert "processing_time_ms" in result, "Result should have 'processing_time_ms'"
        assert "model_id" in result, "Result should have 'model_id'"

        # Validate components
        components = result["components"]
        assert len(components) == 3, f"Should have 3 components, got {len(components)}"

        # Check each component has UUID
        for comp in components:
            assert "id" in comp, "Component should have 'id'"
            assert "type" in comp, "Component should have 'type'"
            assert "data" in comp, "Component should have 'data'"

        print(f"   ✅ Generated {len(components)} valid components")
        print(f"   ✅ Processing time: {result['processing_time_ms']:.1f}ms")
        print(f"   ✅ Model: {result['model_id']}")


# ============================================================================
# Test 2: Chart Detection
# ============================================================================

async def test_chart_detection():
    """Test that LLM generates chart for trend queries."""
    print("\n🧪 Test 2: Chart Detection")

    service = LLMPlannerService()

    mock_components = [
        {
            "type": "ChartComponent",
            "data": {
                "chart_type": "line",
                "title": "Sales Trend",
                "x_axis": ["Q1", "Q2", "Q3", "Q4"],
                "series": [{"label": "Revenue", "values": [1000, 1200, 1500, 1800]}]
            }
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        result = await service.generate_layout("show me sales trend over time")

        components = result["components"]
        assert len(components) >= 1, "Should have at least 1 component"

        chart_found = any(c["type"] == "ChartComponent" for c in components)
        assert chart_found, "Should include a ChartComponent"

        print(f"   ✅ Chart detected in response")
        print(f"   ✅ Component types: {[c['type'] for c in components]}")


# ============================================================================
# Test 3: Table Detection
# ============================================================================

async def test_table_detection():
    """Test that LLM generates table for list queries."""
    print("\n🧪 Test 3: Table Detection")

    service = LLMPlannerService()

    mock_components = [
        {
            "type": "TableA",
            "data": {
                "columns": ["Name", "Email", "Role"],
                "rows": [
                    ["Alice", "alice@example.com", "Admin"],
                    ["Bob", "bob@example.com", "User"]
                ]
            }
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        result = await service.generate_layout("list all users")

        components = result["components"]
        table_found = any(c["type"] == "TableA" for c in components)
        assert table_found, "Should include a TableA component"

        print(f"   ✅ Table detected in response")
        print(f"   ✅ Component types: {[c['type'] for c in components]}")


# ============================================================================
# Test 4: Cache Hit
# ============================================================================

async def test_cache_hit():
    """Test that second identical call uses cache."""
    print("\n🧪 Test 4: Cache Hit")

    service = LLMPlannerService()
    service.clear_cache()  # Clear any existing cache

    mock_components = [
        {
            "type": "SimpleComponent",
            "data": {"title": "Cached Result", "description": "This is cached"}
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        # First call - should call Bedrock
        result1 = await service.generate_layout("show me dashboard")
        assert result1["from_cache"] is False, "First call should not be from cache"
        first_call_count = mock_client.invoke_model.call_count

        # Second call - should use cache
        result2 = await service.generate_layout("show me dashboard")
        assert result2["from_cache"] is True, "Second call should be from cache"
        second_call_count = mock_client.invoke_model.call_count

        # Bedrock should not be called again
        assert first_call_count == second_call_count, "Bedrock should not be called for cached query"

        print(f"   ✅ First call: from_cache={result1['from_cache']}")
        print(f"   ✅ Second call: from_cache={result2['from_cache']}")
        print(f"   ✅ Bedrock calls: {second_call_count} (expected: 1)")


# ============================================================================
# Test 5: Invalid JSON Recovery
# ============================================================================

async def test_invalid_json_recovery():
    """Test that service handles and recovers from malformed JSON."""
    print("\n🧪 Test 5: Invalid JSON Recovery")

    service = LLMPlannerService()

    # Test with markdown code blocks (common LLM output)
    malformed_json = '''```json
$$$[
  {"type":"SimpleComponent","data":{"title":"Test"}}
]$$$
```'''

    mock_response = {
        'body': AsyncMock(read=AsyncMock(return_value=json.dumps({
            'content': [{'text': malformed_json}]
        }).encode()))
    }

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        result = await service.generate_layout("test markdown recovery")

        # Should successfully parse despite markdown wrapper
        components = result["components"]
        assert len(components) >= 1, "Should recover from markdown-wrapped JSON"

        print(f"   ✅ Recovered from markdown code blocks")
        print(f"   ✅ Parsed {len(components)} component(s)")


# ============================================================================
# Test 6: Component Validation
# ============================================================================

async def test_component_validation():
    """Test that service validates and filters invalid components."""
    print("\n🧪 Test 6: Component Validation")

    service = LLMPlannerService()

    # Mix of valid and invalid components
    mock_components = [
        # Valid
        {
            "type": "SimpleComponent",
            "data": {"title": "Valid Card"}
        },
        # Invalid - missing required field
        {
            "type": "TableA",
            "data": {"columns": ["A", "B"]}  # Missing "rows"
        },
        # Invalid - unknown type
        {
            "type": "InvalidComponent",
            "data": {"something": "here"}
        },
        # Valid
        {
            "type": "ChartComponent",
            "data": {
                "chart_type": "bar",
                "title": "Valid Chart",
                "x_axis": ["A", "B"],
                "series": [{"label": "Data", "values": [1, 2]}]
            }
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        result = await service.generate_layout("test validation")

        components = result["components"]

        # Should only include 2 valid components (filter out invalid ones)
        assert len(components) == 2, f"Should filter to 2 valid components, got {len(components)}"

        # Check that all returned components are valid types
        valid_types = ["SimpleComponent", "ChartComponent"]
        for comp in components:
            assert comp["type"] in valid_types, f"Invalid component type: {comp['type']}"

        print(f"   ✅ Filtered {len(components)} valid components from 4 total")
        print(f"   ✅ Valid types: {[c['type'] for c in components]}")


# ============================================================================
# Test 7: Multi-Component Response
# ============================================================================

async def test_multi_component_response():
    """Test that service can handle complex multi-type responses."""
    print("\n🧪 Test 7: Multi-Component Response")

    service = LLMPlannerService()

    mock_components = [
        {
            "type": "SimpleComponent",
            "data": {"title": "Dashboard Overview", "description": "Summary of key metrics"}
        },
        {
            "type": "TableA",
            "data": {
                "columns": ["Metric", "Value", "Change"],
                "rows": [
                    ["Revenue", "$45K", "+12%"],
                    ["Users", "1,234", "+5%"]
                ]
            }
        },
        {
            "type": "ChartComponent",
            "data": {
                "chart_type": "line",
                "title": "Growth Trend",
                "x_axis": ["Mon", "Tue", "Wed"],
                "series": [{"label": "Active Users", "values": [100, 120, 150]}]
            }
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        result = await service.generate_layout("show me complete dashboard")

        components = result["components"]

        # Should have all 3 component types
        types_present = {c["type"] for c in components}
        expected_types = {"SimpleComponent", "TableA", "ChartComponent"}
        assert types_present == expected_types, f"Should have all component types: {types_present}"

        print(f"   ✅ Multi-component layout with {len(components)} components")
        print(f"   ✅ Types present: {types_present}")


# ============================================================================
# Test 8: Cache Clear
# ============================================================================

async def test_cache_clear():
    """Test that cache can be cleared."""
    print("\n🧪 Test 8: Cache Clear")

    service = LLMPlannerService()
    service.clear_cache()

    mock_components = [
        {
            "type": "SimpleComponent",
            "data": {"title": "Test", "description": "Cache clear test"}
        }
    ]

    mock_response = create_mock_bedrock_response(mock_components)

    with patch('aioboto3.Session') as mock_session:
        mock_client = AsyncMock()
        mock_client.invoke_model = AsyncMock(return_value=mock_response)
        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

        # First call
        result1 = await service.generate_layout("test cache")
        assert result1["from_cache"] is False

        # Second call - should be cached
        result2 = await service.generate_layout("test cache")
        assert result2["from_cache"] is True

        # Clear cache
        service.clear_cache()

        # Third call - should NOT be cached after clear
        result3 = await service.generate_layout("test cache")
        assert result3["from_cache"] is False

        print(f"   ✅ Cache populated: from_cache={result2['from_cache']}")
        print(f"   ✅ Cache cleared successfully")
        print(f"   ✅ New call after clear: from_cache={result3['from_cache']}")


# ============================================================================
# Test Runner
# ============================================================================

async def run_all_tests():
    """Run all Phase 6 tests."""
    print("=" * 70)
    print("🧠 PHASE 6: LLM INTEGRATION SERVICE - TEST SUITE")
    print("=" * 70)

    tests = [
        ("Basic Plan Generation", test_basic_plan_generation),
        ("Chart Detection", test_chart_detection),
        ("Table Detection", test_table_detection),
        ("Cache Hit", test_cache_hit),
        ("Invalid JSON Recovery", test_invalid_json_recovery),
        ("Component Validation", test_component_validation),
        ("Multi-Component Response", test_multi_component_response),
        ("Cache Clear", test_cache_clear),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
            print(f"   ✅ PASS - {test_name}")
        except AssertionError as e:
            failed += 1
            print(f"   ❌ FAIL - {test_name}")
            print(f"      Error: {str(e)}")
        except Exception as e:
            failed += 1
            print(f"   ❌ ERROR - {test_name}")
            print(f"      {type(e).__name__}: {str(e)}")

    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("🎉 All tests passed! Phase 6 LLM Integration Service is working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.")

    return failed == 0


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
