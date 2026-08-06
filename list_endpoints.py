# list_endpoints.py
import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Any

def extract_fastapi_routes(content: str, filepath: str) -> List[Dict]:
    """Extract FastAPI route information from file content."""
    routes = []
    
    # Pattern for FastAPI route decorators: @router.get(), @router.post(), etc.
    pattern = r'@router\.(get|post|put|delete|patch|head|options)\s*\(\s*([^)]+)\)\s*(?:async\s+)?def\s+(\w+)\s*\('
    
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        method = match.group(1).upper()
        args_str = match.group(2)
        func_name = match.group(3)
        
        # Extract the path from the arguments
        path = ''
        path_match = re.search(r'[\'"]([^\'"]+)[\'"]', args_str)
        if path_match:
            path = path_match.group(1)
        
        # Check for tags, response_model, etc.
        tags = []
        tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', args_str)
        if tags_match:
            tags_str = tags_match.group(1)
            tags = [t.strip().strip('"\'') for t in tags_str.split(',')]
        
        # Check for summary or description
        summary = ''
        summary_match = re.search(r'summary\s*=\s*[\'"]([^\'"]+)[\'"]', args_str)
        if summary_match:
            summary = summary_match.group(1)
        
        routes.append({
            'method': method,
            'path': path,
            'function': func_name,
            'tags': tags,
            'summary': summary,
            'file': os.path.basename(filepath),
            'is_async': 'async' in content[match.start():match.end()]
        })
    
    # Also handle @app routes
    pattern2 = r'@app\.(get|post|put|delete|patch)\s*\(\s*([^)]+)\)\s*(?:async\s+)?def\s+(\w+)\s*\('
    matches2 = re.finditer(pattern2, content, re.MULTILINE | re.DOTALL)
    
    for match in matches2:
        method = match.group(1).upper()
        args_str = match.group(2)
        func_name = match.group(3)
        
        path_match = re.search(r'[\'"]([^\'"]+)[\'"]', args_str)
        path = path_match.group(1) if path_match else ''
        
        routes.append({
            'method': method,
            'path': path,
            'function': func_name,
            'tags': ['app'],
            'summary': '',
            'file': os.path.basename(filepath),
            'is_async': 'async' in content[match.start():match.end()]
        })
    
    return routes

def scan_directory_for_routes(base_dir: Path, subdir: str) -> Dict[str, List[Dict]]:
    """Scan a specific directory for FastAPI routes."""
    all_routes = {}
    target_dir = base_dir / 'backend' / subdir
    
    if not target_dir.exists():
        print(f"⚠️  Directory not found: {target_dir}")
        return all_routes
    
    print(f"📁 Scanning: {target_dir}\n")
    
    # Get all Python files
    py_files = list(target_dir.rglob('*.py'))
    py_files = [f for f in py_files if '__pycache__' not in str(f) and f.name != '__init__.py']
    
    if not py_files:
        print(f"  No Python files found in {subdir}")
        return all_routes
    
    print(f"  Found {len(py_files)} Python files\n")
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            routes = extract_fastapi_routes(content, str(py_file))
            
            if routes:
                relative_path = py_file.relative_to(base_dir / 'backend')
                all_routes[str(relative_path)] = routes
                print(f"  ✅ {relative_path}: {len(routes)} routes found")
                
                # Show a sample
                for route in routes[:2]:
                    print(f"     → {route['method']:6} {route['path']}")
                if len(routes) > 2:
                    print(f"     ... and {len(routes)-2} more")
                    
        except Exception as e:
            print(f"  ⚠️  Error processing {py_file.name}: {e}")
    
    return all_routes

def scan_all_routes(base_dir: Path) -> Dict[str, List[Dict]]:
    """Scan all directories for FastAPI routes."""
    all_routes = {}
    
    # Scan routes directory
    routes_dir = base_dir / 'backend' / 'routes'
    if routes_dir.exists():
        print("\n" + "="*90)
        print("📂 SCANNING ROUTES DIRECTORY")
        print("="*90)
        routes_data = scan_directory_for_routes(base_dir, 'routes')
        all_routes.update(routes_data)
    
    # Scan utils directory
    utils_dir = base_dir / 'backend' / 'utils'
    if utils_dir.exists():
        print("\n" + "="*90)
        print("📂 SCANNING UTILS DIRECTORY")
        print("="*90)
        utils_data = scan_directory_for_routes(base_dir, 'utils')
        all_routes.update(utils_data)
    
    return all_routes

def print_endpoints(all_routes: Dict[str, List[Dict]]):
    """Pretty print all FastAPI endpoints."""
    if not all_routes:
        print("\n❌ No routes found!")
        return
    
    print("\n" + "="*90)
    print("🚀 CARBONTALLY FASTAPI ENDPOINTS")
    print("="*90)
    
    total_endpoints = 0
    
    # Group by directory
    for module, routes in sorted(all_routes.items()):
        # Determine the directory
        if module.startswith('routes/'):
            dir_name = "Routes"
        elif module.startswith('utils/'):
            dir_name = "Utils"
        else:
            dir_name = "Other"
        
        print(f"\n📁 [{dir_name}] {module}")
        print("-"*90)
        
        # Group by tags if available
        routes_by_tag = {}
        for route in routes:
            tag = route['tags'][0] if route['tags'] else 'General'
            if tag not in routes_by_tag:
                routes_by_tag[tag] = []
            routes_by_tag[tag].append(route)
        
        for tag, tag_routes in routes_by_tag.items():
            if len(routes_by_tag) > 1:
                print(f"\n  🏷️  [{tag}]")
            
            for route in sorted(tag_routes, key=lambda x: x['path']):
                method = route['method']
                path = route['path']
                func = route['function']
                summary = route.get('summary', '')
                
                # Color code methods
                if method == 'GET':
                    method_str = f"\033[92m{method:6}\033[0m"  # Green
                elif method == 'POST':
                    method_str = f"\033[93m{method:6}\033[0m"  # Yellow
                elif method == 'DELETE':
                    method_str = f"\033[91m{method:6}\033[0m"  # Red
                elif method in ['PUT', 'PATCH']:
                    method_str = f"\033[94m{method:6}\033[0m"  # Blue
                else:
                    method_str = f"{method:6}"
                
                # Show async
                async_marker = "⚡" if route.get('is_async') else " "
                
                print(f"    {method_str} {path:50} → {async_marker} {func}()")
                if summary:
                    print(f"      📝 {summary}")
                
                total_endpoints += 1
    
    print("\n" + "="*90)
    print(f"📊 SUMMARY:")
    print(f"  • Files with routes: {len(all_routes)}")
    print(f"  • Total endpoints: {total_endpoints}")
    print("="*90)

def export_to_markdown(all_routes: Dict[str, List[Dict]], output_file: str = 'API_ENDPOINTS.md'):
    """Export endpoints to a markdown file."""
    if not all_routes:
        print("No routes to export!")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CarbonTally API Endpoints\n\n")
        f.write(f"*Generated on {Path.cwd()}*\n\n")
        
        f.write("## Table of Contents\n\n")
        for module in sorted(all_routes.keys()):
            # Create anchor from module name
            anchor = module.replace('/', '').replace('.', '').replace('\\', '')
            f.write(f"- [{module}](#{anchor})\n")
        f.write("\n")
        
        total = 0
        for module, routes in sorted(all_routes.items()):
            # Determine the directory
            if module.startswith('routes/'):
                dir_name = "Routes"
            elif module.startswith('utils/'):
                dir_name = "Utils"
            else:
                dir_name = "Other"
            
            f.write(f"## {module}\n\n")
            f.write(f"*Directory: {dir_name}*\n\n")
            
            # Group by tags
            routes_by_tag = {}
            for route in routes:
                tag = route['tags'][0] if route['tags'] else 'General'
                if tag not in routes_by_tag:
                    routes_by_tag[tag] = []
                routes_by_tag[tag].append(route)
            
            for tag, tag_routes in routes_by_tag.items():
                if len(routes_by_tag) > 1:
                    f.write(f"### {tag}\n\n")
                
                f.write("| Method | Endpoint | Function | Async | Summary |\n")
                f.write("|--------|----------|----------|-------|---------|\n")
                
                for route in sorted(tag_routes, key=lambda x: x['path']):
                    method = route['method']
                    path = route['path']
                    func = route['function']
                    is_async = "✅" if route.get('is_async') else "❌"
                    summary = route.get('summary', '')
                    f.write(f"| `{method}` | `{path}` | `{func}()` | {is_async} | {summary} |\n")
                    total += 1
                
                f.write("\n")
            
            f.write("\n")
        
        f.write(f"\n**Total endpoints:** {total}\n")
    
    print(f"\n✅ Exported to {output_file}")

def debug_scan_file(filepath: Path):
    """Debug function to check a specific file."""
    print(f"\n🔍 Debug scanning: {filepath}")
    print("-"*40)
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    print(f"Contains 'APIRouter': {'APIRouter' in content}")
    print(f"Contains '@router.': {'@router.' in content}")
    print(f"Contains '@app.': {'@app.' in content}")
    
    # Find all router decorators
    router_pattern = r'@router\.(\w+)\s*\(([^)]+)\)'
    matches = re.findall(router_pattern, content)
    
    if matches:
        print(f"\nFound {len(matches)} router decorators:")
        for method, args in matches[:5]:
            print(f"  → @router.{method}({args.strip()[:60]}...)")
    else:
        print("\n❌ No router decorators found")
        print("\nFirst 500 characters of file:")
        print("-"*40)
        print(content[:500])
        print("-"*40)

def main():
    # Get the project root
    project_root = Path.cwd()
    
    print("🔍 Scanning FastAPI routes in: D:\\carbon_ledger\\backend")
    print("="*90)
    
    # Debug: Check the emissions.py file in utils
    emissions_file = project_root / 'backend' / 'utils' / 'emissions.py'
    if emissions_file.exists():
        debug_scan_file(emissions_file)
    
    # Scan all routes
    all_routes = scan_all_routes(project_root)
    
    if all_routes:
        print_endpoints(all_routes)
        export_to_markdown(all_routes)
    else:
        print("\n❌ No FastAPI routes found!")
        print("\n💡 Tips:")
        print("  1. Make sure your route files use @router.get(), @router.post(), etc.")
        print("  2. Check that files have 'APIRouter' imported")
        print("  3. Verify the files contain route decorators")
        print("\nFiles to check:")
        routes_dir = project_root / 'backend' / 'routes'
        if routes_dir.exists():
            py_files = list(routes_dir.rglob('*.py'))
            for f in py_files:
                if f.name != '__init__.py' and '__pycache__' not in str(f):
                    print(f"  • {f.relative_to(project_root)}")
        
        utils_dir = project_root / 'backend' / 'utils'
        if utils_dir.exists():
            py_files = list(utils_dir.rglob('*.py'))
            for f in py_files:
                if f.name != '__init__.py' and '__pycache__' not in str(f):
                    print(f"  • {f.relative_to(project_root)}")

if __name__ == "__main__":
    main()