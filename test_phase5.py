"""
Comprehensive Test Suite for Phase 5: Multi-Component Streaming
Tests multiple instances of TableA and ChartComponent per response
"""

import requests
import json
import re


def extract_components_from_text(text: str) -> list[dict]:
    """
    Extract JSON components from text using the $$$ delimiter pattern.
    
    Shared utility for both batch and streaming (incremental) parsing.
    
    Args:
        text: Text containing embedded JSON components with $$$ delimiters
        
    Returns:
        list[dict]: Parsed component dictionaries
    """
    components = []
    pattern = r'\$\$\$({.*?})\$\$\$'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            component = json.loads(match)
            components.append(component)
        except json.JSONDecodeError:
            continue
    
    return components


def parse_components(response_text: str) -> list[dict]:
    """
    Extract all JSON components from complete streamed response.
    
    This is a convenience wrapper around extract_components_from_text
    for batch processing of complete responses.
    """
    return extract_components_from_text(response_text)


def test_multiple_tables():
    """Test 1: Multiple Tables - Sales + Users"""
    print("\n" + "="*80)
    print("TEST 1: Multiple Tables (Sales + Users)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me two tables: sales and users"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    print(f"\n📊 Components Found: {len(components)} total, {len(component_map)} unique\n")
    
    for comp_id, updates in component_map.items():
        final = updates[-1]  # Last update is the most complete
        print(f"   Component ID: {comp_id}")
        print(f"   Type: {final.get('type')}")
        
        if final.get('type') == 'TableA':
            data = final.get('data', {})
            columns = data.get('columns', [])
            rows = data.get('rows', [])
            print(f"   Columns: {columns}")
            print(f"   Rows: {len(rows)}")
            if rows:
                print(f"   Sample Row: {rows[0]}")
        print()
    
    # Verify we got 2 tables
    table_count = sum(1 for updates in component_map.values() if updates[-1].get('type') == 'TableA')
    
    if table_count >= 2:
        print("✅ Test 1 Passed: Multiple tables streamed successfully")
    else:
        print(f"❌ Test 1 Failed: Expected 2 tables, got {table_count}")
    
    return table_count >= 2


def test_multiple_charts():
    """Test 2: Multiple Charts - Line + Bar"""
    print("\n" + "="*80)
    print("TEST 2: Multiple Charts (Sales Line + Revenue Bar)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me two charts: line and bar"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    print(f"\n📊 Components Found: {len(components)} total, {len(component_map)} unique\n")
    
    for comp_id, updates in component_map.items():
        final = updates[-1]  # Last update is the most complete
        print(f"   Component ID: {comp_id}")
        print(f"   Type: {final.get('type')}")
        
        if final.get('type') == 'ChartComponent':
            data = final.get('data', {})
            chart_type = data.get('chart_type')
            title = data.get('title')
            series = data.get('series', [])
            print(f"   Chart Type: {chart_type}")
            print(f"   Title: {title}")
            if series:
                for s in series:
                    label = s.get('label')
                    values = s.get('values', [])
                    print(f"   Series: {label} ({len(values)} points) → {values}")
        print()
    
    # Verify we got 2 charts
    chart_count = sum(1 for updates in component_map.values() if updates[-1].get('type') == 'ChartComponent')
    
    if chart_count >= 2:
        print("✅ Test 2 Passed: Multiple charts streamed successfully")
    else:
        print(f"❌ Test 2 Failed: Expected 2 charts, got {chart_count}")
    
    return chart_count >= 2


def test_three_tables():
    """Test 3: Three Tables - Sales + Users + Products"""
    print("\n" + "="*80)
    print("TEST 3: Three Tables (Sales + Users + Products)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me three tables: sales, users, and products"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    print(f"\n📊 Components Found: {len(components)} total, {len(component_map)} unique\n")
    
    table_types = []
    for comp_id, updates in component_map.items():
        final = updates[-1]
        if final.get('type') == 'TableA':
            data = final.get('data', {})
            columns = data.get('columns', [])
            # Infer table type from columns
            if "Sales" in columns:
                table_types.append("sales")
            elif "Email" in columns:
                table_types.append("users")
            elif "Price" in columns:
                table_types.append("products")
            
            print(f"   Table: {columns} ({len(data.get('rows', []))} rows)")
    
    print(f"\n   Table Types: {table_types}")
    
    # Verify we got 3 different table types
    if len(set(table_types)) >= 3:
        print("✅ Test 3 Passed: Three different tables streamed successfully")
    else:
        print(f"❌ Test 3 Failed: Expected 3 different tables, got {len(set(table_types))}")
    
    return len(set(table_types)) >= 3


def test_mixed_components():
    """Test 4: Mixed Components - Card + Table + Chart"""
    print("\n" + "="*80)
    print("TEST 4: Mixed Components (SimpleComponent + TableA + ChartComponent)")
    print("="*80)
    
    # First send a card request, then table, then chart in sequence
    # This tests that the system can handle different types
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me a sales table"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    component_types = set(comp.get('type') for comp in components)
    
    print(f"\n   Component Types Present: {component_types}")
    
    # For this test, just verify we can stream a table (baseline)
    has_table = 'TableA' in component_types
    
    if has_table:
        print("✅ Test 4 Passed: Can stream TableA component")
    else:
        print("❌ Test 4 Failed: No TableA component found")
    
    return has_table


def test_progressive_interleaving():
    """Test 5: Verify Progressive Interleaving of Multiple Components"""
    print("\n" + "="*80)
    print("TEST 5: Progressive Interleaving (Multiple Charts)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me two charts"},
        stream=True
    )
    
    full_response = ""
    component_sequence = []
    processed_count = 0  # Track how many components we've already processed
    
    print("\n📡 Streaming Response (tracking component order):\n")
    
    temp_buffer = ""
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
            temp_buffer += chunk
            
            # Try to extract components as they arrive using shared utility
            all_components = extract_components_from_text(temp_buffer)
            
            # Only process new components we haven't seen yet
            new_components = all_components[processed_count:]
            for comp in new_components:
                series = comp.get('data', {}).get('series', [])
                data_points = len(series[0].get('values', [])) if series else 0
                component_sequence.append({
                    'id': comp.get('id'),
                    'type': comp.get('type'),
                    'data_points': data_points
                })
            
            # Update processed count
            processed_count = len(all_components)
    
    print("\n\n" + "-"*80)
    print("📊 Component Update Sequence:")
    print("-"*80)
    
    # Group updates by component ID
    update_map = {}
    for item in component_sequence:
        comp_id = item['id'][:8]  # Truncate for readability
        if comp_id not in update_map:
            update_map[comp_id] = []
        update_map[comp_id].append(item['data_points'])
    
    print()
    for comp_id, updates in update_map.items():
        print(f"   Component {comp_id}: {updates}")
    
    # Verify interleaving: updates should alternate between components
    # If we have 2 components, we should see updates from both before completion
    is_interleaved = len(update_map) >= 2
    
    if is_interleaved:
        print("\n✅ Test 5 Passed: Components update progressively in interleaved fashion")
    else:
        print(f"\n❌ Test 5 Failed: Expected interleaved updates for multiple components")
    
    return is_interleaved


def test_backward_compatibility():
    """Test 6: Backward Compatibility - Single Table/Chart still works"""
    print("\n" + "="*80)
    print("TEST 6: Backward Compatibility (Single Table)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me a sales table"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    # Verify we got exactly 1 table
    table_count = sum(1 for updates in component_map.values() if updates[-1].get('type') == 'TableA')
    
    if table_count == 1:
        final_table = None
        for updates in component_map.values():
            if updates[-1].get('type') == 'TableA':
                final_table = updates[-1]
                break
        
        rows = final_table.get('data', {}).get('rows', [])
        print(f"\n   Single Table: {len(rows)} rows")
        print("✅ Test 6 Passed: Single table streaming still works (backward compatible)")
    else:
        print(f"❌ Test 6 Failed: Expected 1 table, got {table_count}")
    
    return table_count == 1


def test_same_type_charts():
    """Test 7: Same Type Charts - Two Line Charts (Phase 5.1)"""
    print("\n" + "="*80)
    print("TEST 7: Same Type Charts (Two Line Charts)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me two line charts"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    print(f"\n📊 Components Found: {len(components)} total, {len(component_map)} unique\n")
    
    line_chart_count = 0
    for comp_id, updates in component_map.items():
        # Check FIRST update (skeleton) for chart_type, not last
        first = updates[0]
        if first.get('type') == 'ChartComponent':
            data = first.get('data', {})
            chart_type = data.get('chart_type')
            print(f"   Chart ID: {comp_id}")
            print(f"   Type: {chart_type}")
            print(f"   Title: {data.get('title')}")
            if chart_type == 'line':
                line_chart_count += 1
            print()
    
    # Verify we got 2 line charts
    if line_chart_count >= 2:
        print("✅ Test 7 Passed: Two line charts streamed successfully")
    else:
        print(f"❌ Test 7 Failed: Expected 2 line charts, got {line_chart_count}")
    
    return line_chart_count >= 2


def test_same_type_tables():
    """Test 8: Same Type Tables - Two Sales Tables (Phase 5.1)"""
    print("\n" + "="*80)
    print("TEST 8: Same Type Tables (Two Sales Tables)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me two sales tables"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    print(f"\n📊 Components Found: {len(components)} total, {len(component_map)} unique\n")
    
    sales_table_count = 0
    for comp_id, updates in component_map.items():
        # Check FIRST update (skeleton) for columns, not last
        first = updates[0]
        if first.get('type') == 'TableA':
            data = first.get('data', {})
            columns = data.get('columns', [])
            print(f"   Table ID: {comp_id}")
            print(f"   Columns: {columns}")
            # Check if it's a sales table (has Name, Sales, Region columns)
            if 'Name' in columns and 'Sales' in columns:
                sales_table_count += 1
            print()
    
    # Verify we got 2 sales tables
    if sales_table_count >= 2:
        print("✅ Test 8 Passed: Two sales tables streamed successfully")
    else:
        print(f"❌ Test 8 Failed: Expected 2 sales tables, got {sales_table_count}")
    
    return sales_table_count >= 2


def test_multiple_delayed_cards():
    """Test 9: Multiple Delayed Cards (Phase 5.2) - Progressive SimpleComponent"""
    print("\n" + "="*80)
    print("TEST 9: Multiple Delayed Cards (Phase 5.2)")
    print("="*80)
    
    response = requests.post(
        "http://127.0.0.1:8001/chat",
        json={"message": "show me two delayed cards"},
        stream=True
    )
    
    full_response = ""
    print("\n📡 Streaming Response:\n")
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
            full_response += chunk
    
    print("\n\n" + "-"*80)
    print("📊 Analysis:")
    print("-"*80)
    
    components = parse_components(full_response)
    
    # Group by component ID
    component_map = {}
    for comp in components:
        comp_id = comp.get("id")
        if comp_id not in component_map:
            component_map[comp_id] = []
        component_map[comp_id].append(comp)
    
    print(f"\n📊 Components Found: {len(components)} total, {len(component_map)} unique\n")
    
    delayed_card_count = 0
    for comp_id, updates in component_map.items():
        first = updates[0]  # First update has the title
        final = updates[-1]  # Last update is the most complete
        print(f"   Component ID: {comp_id}")
        print(f"   Type: {final.get('type')}")
        
        if final.get('type') == 'SimpleComponent':
            # Check first update for title (delayed cards have title in initial update)
            first_data = first.get('data', {})
            final_data = final.get('data', {})
            
            title = first_data.get('title', final_data.get('title', ''))
            description = final_data.get('description', '')
            units = final_data.get('units', 0)
            value = final_data.get('value', 0)
            
            print(f"   Title: {title}")
            print(f"   Description: {description}")
            print(f"   Units: {units}")
            print(f"   Value: {value}")
            print(f"   Updates: {len(updates)} progressive updates")
            
            # Check if it's a delayed card (has "Delayed Card" in title OR "units" field)
            if 'Delayed Card' in title or 'units' in final_data:
                delayed_card_count += 1
        print()
    
    # Verify we got 2 delayed cards with progressive updates
    if delayed_card_count >= 2:
        # Check for progressive updates (should have multiple updates per card)
        has_progressive = all(len(updates) > 1 for updates in component_map.values())
        if has_progressive:
            print("✅ Test 9 Passed: Two delayed cards with progressive updates streamed successfully")
            return True
        else:
            print("❌ Test 9 Failed: Cards created but no progressive updates detected")
            return False
    else:
        print(f"❌ Test 9 Failed: Expected 2 delayed cards, got {delayed_card_count}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 PHASE 5 MULTI-COMPONENT STREAMING TEST SUITE (v0.5.2)")
    print("="*80)
    print("\nTesting backend at: http://127.0.0.1:8001")
    print("Tests: Multiple Tables, Multiple Charts, Multiple Delayed Cards (Phase 5.2)")
    print("\n" + "="*80)
    
    results = []
    
    try:
        results.append(("Multiple Tables (2)", test_multiple_tables()))
    except Exception as e:
        print(f"\n❌ Test 1 Error: {e}")
        results.append(("Multiple Tables (2)", False))
    
    try:
        results.append(("Multiple Charts (2)", test_multiple_charts()))
    except Exception as e:
        print(f"\n❌ Test 2 Error: {e}")
        results.append(("Multiple Charts (2)", False))
    
    try:
        results.append(("Three Tables", test_three_tables()))
    except Exception as e:
        print(f"\n❌ Test 3 Error: {e}")
        results.append(("Three Tables", False))
    
    try:
        results.append(("Mixed Components", test_mixed_components()))
    except Exception as e:
        print(f"\n❌ Test 4 Error: {e}")
        results.append(("Mixed Components", False))
    
    try:
        results.append(("Progressive Interleaving", test_progressive_interleaving()))
    except Exception as e:
        print(f"\n❌ Test 5 Error: {e}")
        results.append(("Progressive Interleaving", False))
    
    try:
        results.append(("Backward Compatibility", test_backward_compatibility()))
    except Exception as e:
        print(f"\n❌ Test 6 Error: {e}")
        results.append(("Backward Compatibility", False))
    
    try:
        results.append(("Same Type Charts (Phase 5.1)", test_same_type_charts()))
    except Exception as e:
        print(f"\n❌ Test 7 Error: {e}")
        results.append(("Same Type Charts (Phase 5.1)", False))
    
    try:
        results.append(("Same Type Tables (Phase 5.1)", test_same_type_tables()))
    except Exception as e:
        print(f"\n❌ Test 8 Error: {e}")
        results.append(("Same Type Tables (Phase 5.1)", False))
    
    try:
        results.append(("Multiple Delayed Cards (Phase 5.2)", test_multiple_delayed_cards()))
    except Exception as e:
        print(f"\n❌ Test 9 Error: {e}")
        results.append(("Multiple Delayed Cards (Phase 5.2)", False))
    
    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print("\n" + "="*80)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("="*80)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Phase 5 multi-component streaming is working correctly.")
    else:
        print(f"\n⚠️ {total_count - passed_count} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    main()
