# export_postman.py
"""
Export API endpoints to Postman Collection format
Run: py export_postman.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def load_routes_from_markdown(md_file: str = 'API_DOCUMENTATION.md') -> Dict[str, List[Dict]]:
    """Parse the generated markdown to extract route information."""
    routes = {}
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        table_pattern = r'### 📁 `([^`]+)`\n\n\| Method \| Endpoint \| Function \| Description \|\n\|--------\|----------\|----------\|-------------\\|\n((?:\|.*\|.*\|.*\|.*\|\n)+)'
        matches = re.finditer(table_pattern, content, re.MULTILINE)
        
        for match in matches:
            module = match.group(1)
            table_rows = match.group(2)
            
            routes[module] = []
            
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

def generate_postman_collection(routes: Dict[str, List[Dict]], base_url: str = "{{BASE_URL}}") -> Dict:
    """Generate Postman Collection v2.1 format."""
    
    collection = {
        "info": {
            "name": "CarbonTally API",
            "description": "CarbonTally API Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": "1.0.0",
            "updated": datetime.now().isoformat()
        },
        "item": [],
        "variable": [
            {
                "key": "BASE_URL",
                "value": "http://localhost:8000",
                "type": "string"
            }
        ]
    }
    
    # Group by module
    for module, endpoints in sorted(routes.items()):
        # Create folder for module
        folder = {
            "name": module,
            "item": []
        }
        
        for endpoint in sorted(endpoints, key=lambda x: x['path']):
            # Create request item
            item = {
                "name": f"{endpoint['method']} {endpoint['path']}",
                "request": {
                    "method": endpoint['method'],
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "key": "Authorization",
                            "value": "Bearer {{AUTH_TOKEN}}",
                            "type": "text"
                        }
                    ],
                    "url": {
                        "raw": f"{{{{BASE_URL}}}}{endpoint['path']}",
                        "host": ["{{BASE_URL}}"],
                        "path": endpoint['path'].strip('/').split('/') if endpoint['path'] != '/' else []
                    },
                    "description": endpoint.get('description', '')
                },
                "response": []
            }
            
            # Add request body for POST/PUT/PATCH
            if endpoint['method'] in ['POST', 'PUT', 'PATCH']:
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": "{}",
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            folder["item"].append(item)
        
        collection["item"].append(folder)
    
    return collection

def main():
    routes = load_routes_from_markdown()
    
    if not routes:
        print("❌ No routes found. Run generate_api_docs.py first.")
        return
    
    collection = generate_postman_collection(routes)
    
    output_file = 'CarbonTally_API.postman_collection.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2)
    
    print(f"✅ Postman collection exported to {output_file}")
    print(f"📊 Total: {sum(len(r) for r in routes.values())} endpoints")

if __name__ == "__main__":
    main()