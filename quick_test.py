import requests
import json
import re

def test_two_line_charts():
    print("Testing: 'show me two line charts'")
    print("="*60)
    
    r = requests.post(
        'http://127.0.0.1:8001/chat',
        json={'message': 'show me two line charts'},
        stream=True
    )
    
    full_response = ""
    for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            full_response += chunk
    
    # Extract JSON components
    pattern = r'\$\$\$({.*?})\$\$\$'
    matches = re.findall(pattern, full_response, re.DOTALL)
    
    print(f"\nTotal components found: {len(matches)}")
    
    line_count = 0
    bar_count = 0
    
    for i, match in enumerate(matches):
        try:
            comp = json.loads(match)
            if comp.get('type') == 'ChartComponent':
                chart_type = comp.get('data', {}).get('chart_type')
                title = comp.get('data', {}).get('title', 'N/A')
                print(f"\nChart {i+1}:")
                print(f"  Type: {chart_type}")
                print(f"  Title: {title}")
                
                if chart_type == 'line':
                    line_count += 1
                elif chart_type == 'bar':
                    bar_count += 1
        except:
            pass
    
    print(f"\n" + "="*60)
    print(f"Summary: {line_count} line charts, {bar_count} bar charts")
    
    if line_count >= 2:
        print("✅ PASS: Got 2+ line charts (Phase 5.1 working!)")
        return True
    else:
        print(f"❌ FAIL: Expected 2 line charts, got {line_count}")
        return False

def test_two_sales_tables():
    print("\n\nTesting: 'show me two sales tables'")
    print("="*60)
    
    r = requests.post(
        'http://127.0.0.1:8001/chat',
        json={'message': 'show me two sales tables'},
        stream=True
    )
    
    full_response = ""
    for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            full_response += chunk
    
    # Extract JSON components
    pattern = r'\$\$\$({.*?})\$\$\$'
    matches = re.findall(pattern, full_response, re.DOTALL)
    
    print(f"\nTotal components found: {len(matches)}")
    
    sales_count = 0
    users_count = 0
    
    for i, match in enumerate(matches):
        try:
            comp = json.loads(match)
            if comp.get('type') == 'TableA':
                columns = comp.get('data', {}).get('columns', [])
                print(f"\nTable {i+1}:")
                print(f"  Columns: {columns}")
                
                # Check if it's a sales table
                if 'Name' in columns and 'Sales' in columns:
                    sales_count += 1
                # Check if it's a users table
                elif 'Username' in columns and 'Email' in columns:
                    users_count += 1
        except:
            pass
    
    print(f"\n" + "="*60)
    print(f"Summary: {sales_count} sales tables, {users_count} users tables")
    
    if sales_count >= 2:
        print("✅ PASS: Got 2+ sales tables (Phase 5.1 working!)")
        return True
    else:
        print(f"❌ FAIL: Expected 2 sales tables, got {sales_count}")
        return False

if __name__ == "__main__":
    result1 = test_two_line_charts()
    result2 = test_two_sales_tables()
    
    print("\n\n" + "="*60)
    print("FINAL RESULTS:")
    print("="*60)
    print(f"Two Line Charts: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Two Sales Tables: {'✅ PASS' if result2 else '❌ FAIL'}")
