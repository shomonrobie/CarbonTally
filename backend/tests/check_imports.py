# backend/tests/check_imports.py
import os
import re
from pathlib import Path

def check_imports():
    routes_dir = Path(__file__).parent.parent / 'routes'
    
    # All auth functions that should be available
    auth_functions = [
        'get_current_user',
        'require_auth',
        'require_admin',
        'require_staff',
        'require_org_member',
        'require_org_admin',
        'require_role',
        'require_permission',
        'require_any_permission',
        'require_all_permissions',
        'require_org_access',
    ]
    
    print("="*70)
    print("🔍 CHECKING AUTH IMPORTS IN ROUTE FILES")
    print("="*70)
    
    for py_file in routes_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find import line for auth
        import_match = re.search(r'from auth import ([^\n]+)', content)
        
        if import_match:
            imported = import_match.group(1)
            print(f"\n📁 {py_file.relative_to(routes_dir)}")
            print(f"  ✅ Imports: {imported}")
            
            # Check which functions are used but not imported
            used_functions = []
            for func in auth_functions:
                if func in content and func not in imported:
                    used_functions.append(func)
            
            if used_functions:
                print(f"  ⚠️  Missing imports for: {', '.join(used_functions)}")
        else:
            # Check if any auth functions are used
            used = []
            for func in auth_functions:
                if func in content:
                    used.append(func)
            
            if used:
                print(f"\n📁 {py_file.relative_to(routes_dir)}")
                print(f"  ❌ No auth import found but uses: {', '.join(used)}")

if __name__ == "__main__":
    check_imports()