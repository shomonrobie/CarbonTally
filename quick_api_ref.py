# quick_api_ref.py
"""
Quick API Reference - Interactive endpoint lookup
Run: py quick_api_ref.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

def load_routes_from_markdown(md_file: str = 'API_DOCUMENTATION.md') -> Dict[str, List[Dict]]:
    """Parse the generated markdown to extract route information."""
    routes = {}
    current_module = None
    
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
        print(f"⚠️  {md_file} not found. Run generate_api_docs.py first.")
        return {}
    
    return routes

def search_endpoints(routes: Dict[str, List[Dict]], search_term: str) -> List[Dict]:
    """Search for endpoints containing the search term."""
    results = []
    search_term = search_term.lower()
    
    for module, endpoints in routes.items():
        for endpoint in endpoints:
            if (search_term in endpoint['path'].lower() or
                search_term in endpoint['function'].lower() or
                search_term in endpoint['description'].lower() or
                search_term in module.lower()):
                results.append({
                    'module': module,
                    **endpoint
                })
    
    return results

def print_results(results: List[Dict], search_term: str):
    """Pretty print search results."""
    if not results:
        print(f"\n❌ No endpoints found for '{search_term}'")
        return
    
    print(f"\n🔍 Found {len(results)} endpoint(s) matching '{search_term}':")
    print("="*80)
    
    for result in results:
        method = result['method']
        path = result['path']
        func = result['function']
        module = result['module']
        desc = result.get('description', '')
        
        # Color code methods
        if method == 'GET':
            method_display = f"\033[92m{method:6}\033[0m"  # Green
        elif method == 'POST':
            method_display = f"\033[93m{method:6}\033[0m"  # Yellow
        elif method == 'DELETE':
            method_display = f"\033[91m{method:6}\033[0m"  # Red
        elif method in ['PUT', 'PATCH']:
            method_display = f"\033[94m{method:6}\033[0m"  # Blue
        else:
            method_display = method
        
        print(f"\n📁 {module}")
        print(f"  {method_display} {path}")
        print(f"  → {func}()")
        if desc:
            print(f"  📝 {desc}")

def interactive_search():
    """Run interactive search."""
    print("="*80)
    print("🔍 CarbonTally API Quick Reference")
    print("="*80)
    
    routes = load_routes_from_markdown()
    
    if not routes:
        print("\n💡 Please run 'py generate_api_docs.py' first to generate the API documentation.")
        return
    
    print(f"\n📊 Loaded {sum(len(r) for r in routes.values())} endpoints from {len(routes)} modules")
    print("\nCommands:")
    print("  • search <term>  - Search for endpoints")
    print("  • list           - List all modules")
    print("  • module <name>  - Show all endpoints in a module")
    print("  • stats          - Show statistics")
    print("  • help           - Show this help")
    print("  • quit           - Exit")
    
    while True:
        try:
            command = input("\n🔎 > ").strip()
            
            if not command:
                continue
            
            if command.lower() == 'quit':
                break
            
            if command.lower() == 'help':
                print("\nCommands:")
                print("  • search <term>  - Search for endpoints")
                print("  • list           - List all modules")
                print("  • module <name>  - Show all endpoints in a module")
                print("  • stats          - Show statistics")
                print("  • help           - Show this help")
                print("  • quit           - Exit")
                continue
            
            if command.lower() == 'stats':
                print(f"\n📊 Statistics:")
                print(f"  Total endpoints: {sum(len(r) for r in routes.values())}")
                print(f"  Total modules: {len(routes)}")
                print("\nTop modules by endpoint count:")
                sorted_modules = sorted(routes.items(), key=lambda x: len(x[1]), reverse=True)
                for module, endpoints in sorted_modules[:10]:
                    print(f"  • {module}: {len(endpoints)} endpoints")
                continue
            
            if command.lower() == 'list':
                print("\n📁 Available modules:")
                for module in sorted(routes.keys()):
                    print(f"  • {module} ({len(routes[module])} endpoints)")
                continue
            
            if command.lower().startswith('module '):
                module_name = command[7:].strip()
                # Find matching module
                matches = [m for m in routes.keys() if module_name.lower() in m.lower()]
                if not matches:
                    print(f"❌ No module found matching '{module_name}'")
                    continue
                
                for module in matches:
                    print(f"\n📁 {module}")
                    print("-"*60)
                    for endpoint in sorted(routes[module], key=lambda x: x['path']):
                        method = endpoint['method']
                        path = endpoint['path']
                        func = endpoint['function']
                        print(f"  {method:6} {path} → {func}()")
                continue
            
            if command.lower().startswith('search '):
                search_term = command[7:].strip()
                results = search_endpoints(routes, search_term)
                print_results(results, search_term)
                continue
            
            print("❌ Unknown command. Type 'help' for available commands.")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    interactive_search()