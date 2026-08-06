# test_endpoints.py
"""
Quick endpoint tester - Check if endpoints are accessible
Run: py test_endpoints.py
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, List, Any
import re

def load_routes_from_markdown(md_file: str = 'API_DOCUMENTATION.md') -> Dict[str, List[Dict]]:
    """Parse the generated markdown to extract route information."""
    routes = {}
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all route tables
        table_pattern = r'### 📁 `([^`]+)`\n\n\| Method \| Endpoint \| Function \| Description \|\n\|--------\|----------\|----------\|-------------\\|\n((?:\|.*\|.*\|.*\|.*\|\n)+)'
        
        matches = re.finditer(table_pattern, content, re.MULTILINE)
        
        for match in matches:
            module = match.group(1)
            table_rows = match.group(2)
            
            routes[module] = []
            
            # Parse table rows
            row_pattern = r'\| `([^`]+)` \| `([^`]+)` \| `([^`]+)\(\)` \| ([^|]+) \|'
            for row_match in re.finditer(row_pattern, table_rows):
                method = row_match.group(1).replace('🟢', '').replace('🟡', '').replace('🔵', '').replace('🔴', '').strip()
                path = row_match.group(2)
                function = row_match.group(3)
                description = row_match.group(4).strip()
                
                routes[module].append({
                    'method': method,
                    'path': path,
                    'function': function,
                    'description': description
                })
    
    except FileNotFoundError:
        print(f"⚠️  {md_file} not found.")
        return {}
    
    return routes

async def test_endpoint(session, method: str, path: str, base_url: str = "http://localhost:8000"):
    """Test a single endpoint."""
    url = f"{base_url}{path}"
    
    # Skip endpoints with path parameters for testing
    if '{' in path:
        return None
    
    try:
        async with session.request(method, url) as response:
            return {
                'path': path,
                'method': method,
                'status': response.status,
                'success': 200 <= response.status < 300
            }
    except Exception as e:
        return {
            'path': path,
            'method': method,
            'status': 'Error',
            'success': False,
            'error': str(e)
        }

async def test_all_endpoints(base_url: str = "http://localhost:8000"):
    """Test all endpoints."""
    routes = load_routes_from_markdown()
    
    if not routes:
        print("❌ No routes found. Run generate_api_docs.py first.")
        return
    
    # Collect all endpoints (skip those with path parameters)
    endpoints = []
    for module, module_routes in routes.items():
        for route in module_routes:
            if '{' not in route['path']:  # Skip endpoints with path parameters
                endpoints.append(route)
    
    print(f"🧪 Testing {len(endpoints)} endpoints at {base_url}")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        tasks = [test_endpoint(session, e['method'], e['path'], base_url) for e in endpoints]
        results = await asyncio.gather(*tasks)
    
    # Filter out None results
    results = [r for r in results if r is not None]
    
    # Print results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\n❌ Failed endpoints:")
        for result in failed:
            status = result.get('status', 'Unknown')
            error = result.get('error', '')
            print(f"  • {result['method']:6} {result['path']} → {status}")
            if error:
                print(f"      Error: {error}")

def main():
    import sys
    
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    asyncio.run(test_all_endpoints(base_url))

if __name__ == "__main__":
    main()