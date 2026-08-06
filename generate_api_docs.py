# generate_api_docs.py
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def generate_structured_docs(all_routes: Dict[str, List[Dict]]) -> str:
    """Generate a more structured and readable API documentation."""
    
    # Categorize endpoints
    categories = {
        "🏢 Organization Management": [],
        "👥 Team & Members": [],
        "📊 Analytics & Reports": [],
        "📁 Documents & Files": [],
        "⚙️ Admin & Staff": [],
        "📝 Reviews & Assignments": [],
        "📋 Reference Data": [],
        "👤 User Management": [],
        "🔔 Notifications": [],
        "📈 Emissions": [],
        "📚 Glossary": [],
        "📤 Upload": [],
        "📝 Drafts": [],
        "📊 Reports": [],
        "📋 Logs": [],
        "✉️ Waitlist": [],
    }
    
    # Categorize each endpoint
    for module, routes in all_routes.items():
        for route in routes:
            path = route['path']
            method = route['method']
            func = route['function']
            summary = route.get('summary', '')
            
            # Determine category based on module and path
            category = "Other"
            
            if 'organizations' in module:
                if 'team' in module or 'members' in module:
                    category = "👥 Team & Members"
                elif 'analytics' in module:
                    category = "📊 Analytics & Reports"
                elif 'assets' in module:
                    category = "🏢 Organization Management"
                elif 'management' in module:
                    category = "🏢 Organization Management"
                elif 'files' in module:
                    category = "📁 Documents & Files"
                elif 'dashboard' in module:
                    category = "📊 Analytics & Reports"
                elif 'data' in module:
                    category = "📊 Analytics & Reports"
            elif 'admin' in module:
                if 'assignments' in module or 'reviews' in module:
                    category = "📝 Reviews & Assignments"
                elif 'staff' in module:
                    category = "⚙️ Admin & Staff"
                elif 'defra' in module or 'extraction' in module:
                    category = "⚙️ Admin & Staff"
                elif 'permissions' in module:
                    category = "⚙️ Admin & Staff"
            elif 'documents' in module:
                category = "📁 Documents & Files"
            elif 'drafts' in module:
                category = "📝 Drafts"
            elif 'emissions' in module:
                category = "📈 Emissions"
            elif 'glossary' in module:
                category = "📚 Glossary"
            elif 'logs' in module:
                category = "📋 Logs"
            elif 'notifications' in module:
                category = "🔔 Notifications"
            elif 'reference' in module:
                category = "📋 Reference Data"
            elif 'reports' in module:
                category = "📊 Reports"
            elif 'upload' in module:
                category = "📤 Upload"
            elif 'users' in module:
                category = "👤 User Management"
            elif 'waitlist' in module:
                category = "✉️ Waitlist"
            
            if category in categories:
                categories[category].append({
                    'module': module,
                    'path': path,
                    'method': method,
                    'function': func,
                    'summary': summary,
                    'full_path': f"{path}"
                })
            else:
                categories["Other"].append({
                    'module': module,
                    'path': path,
                    'method': method,
                    'function': func,
                    'summary': summary,
                    'full_path': f"{path}"
                })
    
    # Generate markdown
    md = []
    md.append("# 🌿 CarbonTally API Documentation\n\n")
    md.append(f"*Generated on {Path.cwd()}*\n\n")
    md.append("## 📊 Summary\n\n")
    
    total_endpoints = sum(len(routes) for routes in categories.values())
    md.append(f"**Total Endpoints:** {total_endpoints}\n\n")
    
    # Table of Contents
    md.append("## 📑 Table of Contents\n\n")
    for category in categories:
        if categories[category]:
            count = len(categories[category])
            md.append(f"- [{category}](#{category.replace(' ', '-').lower()}) ({count} endpoints)\n")
    md.append("\n")
    
    # Detailed sections
    for category, endpoints in categories.items():
        if not endpoints:
            continue
            
        md.append(f"\n## {category}\n\n")
        
        # Group by module within category
        by_module = defaultdict(list)
        for endpoint in endpoints:
            module_name = endpoint['module'].replace('routes\\', '').replace('routes/', '')
            by_module[module_name].append(endpoint)
        
        for module, module_endpoints in sorted(by_module.items()):
            if len(by_module) > 1:
                md.append(f"### 📁 `{module}`\n\n")
            
            md.append("| Method | Endpoint | Function | Description |\n")
            md.append("|--------|----------|----------|-------------|\n")
            
            for endpoint in sorted(module_endpoints, key=lambda x: x['path']):
                method = endpoint['method']
                path = endpoint['path']
                func = endpoint['function']
                summary = endpoint['summary'] or ' '
                
                # Add method badges
                if method == 'GET':
                    method_display = f"🟢 {method}"
                elif method == 'POST':
                    method_display = f"🟡 {method}"
                elif method == 'DELETE':
                    method_display = f"🔴 {method}"
                elif method in ['PUT', 'PATCH']:
                    method_display = f"🔵 {method}"
                else:
                    method_display = method
                
                md.append(f"| `{method_display}` | `{path}` | `{func}()` | {summary} |\n")
            
            md.append("\n")
    
    # Add footnotes
    md.append("\n---\n\n")
    md.append("### 🎨 Legend\n\n")
    md.append("- 🟢 **GET** - Retrieve data\n")
    md.append("- 🟡 **POST** - Create new data\n")
    md.append("- 🔵 **PUT/PATCH** - Update existing data\n")
    md.append("- 🔴 **DELETE** - Remove data\n")
    md.append("- ✅ **Async** - Asynchronous endpoint\n\n")
    
    md.append("### 📝 Notes\n\n")
    md.append("- All endpoints are asynchronous (FastAPI)\n")
    md.append("- Authentication required for all endpoints (except waitlist)\n")
    md.append("- All responses are in JSON format\n")
    
    return ''.join(md)

def create_summary_markdown(all_routes: Dict[str, List[Dict]]) -> str:
    """Create a summary markdown with endpoint counts by module."""
    
    md = []
    md.append("# 📊 API Endpoint Summary\n\n")
    
    # Count by module
    module_counts = {}
    for module, routes in all_routes.items():
        module_counts[module] = len(routes)
    
    md.append("## 📈 Endpoints by Module\n\n")
    md.append("| Module | Endpoints |\n")
    md.append("|--------|-----------|\n")
    
    for module, count in sorted(module_counts.items(), key=lambda x: x[1], reverse=True):
        md.append(f"| `{module}` | {count} |\n")
    
    md.append("\n")
    
    # Count by method
    method_counts = defaultdict(int)
    for routes in all_routes.values():
        for route in routes:
            method_counts[route['method']] += 1
    
    md.append("## 📊 Endpoints by HTTP Method\n\n")
    md.append("| Method | Count |\n")
    md.append("|--------|-------|\n")
    
    for method, count in sorted(method_counts.items()):
        md.append(f"| {method} | {count} |\n")
    
    return ''.join(md)

def main():
    # Load the routes from the previously generated JSON or parse the markdown
    # For now, we'll assume you want to regenerate from the existing script
    
    print("📝 Generating enhanced API documentation...")
    
    # This would normally use the output from list_endpoints.py
    # Since we have the markdown, let's create a better version
    
    # Run the existing script to get the data, but we'll just create the enhanced version
    from list_endpoints import scan_all_routes, extract_fastapi_routes
    from pathlib import Path
    
    project_root = Path.cwd()
    all_routes = scan_all_routes(project_root)
    
    if all_routes:
        # Generate enhanced documentation
        enhanced_docs = generate_structured_docs(all_routes)
        
        with open('API_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
            f.write(enhanced_docs)
        
        print("✅ Enhanced API documentation saved to API_DOCUMENTATION.md")
        
        # Also generate summary
        summary = create_summary_markdown(all_routes)
        with open('API_SUMMARY.md', 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print("✅ Summary saved to API_SUMMARY.md")
    else:
        print("❌ No routes found!")

if __name__ == "__main__":
    main()