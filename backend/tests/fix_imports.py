# backend/tests/fix_imports.py
import os
import re
from pathlib import Path

def fix_auth_imports():
    routes_dir = Path(__file__).parent.parent / 'routes'
    
    # Files that need fixing with their missing imports
    fixes = {
        'emissions.py': ['require_auth', 'require_org_admin'],
        'upload.py': ['require_auth'],
        'admin/reviews.py': ['require_admin'],
        'organizations/assets.py': ['require_org_admin'],
        'organizations/files.py': ['require_org_admin'],
        'organizations/members.py': ['require_org_admin'],
    }
    
    print("="*70)
    print("🔧 FIXING AUTH IMPORTS IN ROUTE FILES")
    print("="*70)
    
    for file_path, missing_imports in fixes.items():
        full_path = routes_dir / file_path
        
        if not full_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the auth import line
        import_match = re.search(r'from auth import ([^\n]+)', content)
        
        if import_match:
            current_imports = set(import_match.group(1).replace(' ', '').split(','))
            new_imports = sorted(current_imports.union(set(missing_imports)))
            new_import_line = f"from auth import {', '.join(new_imports)}"
            
            # Replace the import line
            new_content = re.sub(
                r'from auth import [^\n]+',
                new_import_line,
                content
            )
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Fixed: {file_path}")
            print(f"   Added: {', '.join(missing_imports)}")
        else:
            print(f"⚠️  No auth import found in: {file_path}")

if __name__ == "__main__":
    fix_auth_imports()