# backend/tests/audit_code.py
"""
Comprehensive code audit tool
Run: python backend/tests/audit_code.py
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

class CodeAuditor:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.routes_dir = root_dir / 'backend' / 'routes'
        self.utils_dir = root_dir / 'backend' / 'utils'
        self.issues = defaultdict(list)
        self.duplicates = {}
        self.missing_imports = {}
        self.duplicate_endpoints = {}
        
    def audit_all(self):
        """Run all audits"""
        print("="*70)
        print("🔍 CARBONTALLY CODE AUDIT")
        print("="*70)
        
        self.check_duplicate_functions()
        self.check_missing_imports()
        self.check_duplicate_endpoints()
        self.check_supabase_queries()
        self.check_error_handling()
        self.check_import_organization()
        
        self.print_summary()
    
    def check_duplicate_functions(self):
        """Find duplicate function definitions"""
        print("\n📌 Checking duplicate functions...")
        print("-" * 40)
        
        function_map = defaultdict(list)
        
        for py_file in self.routes_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or py_file.name == '__init__.py':
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Use regex to find function definitions
                func_pattern = r'^(?:async\s+)?def\s+(\w+)\s*\('
                matches = re.finditer(func_pattern, content, re.MULTILINE)
                
                file_path = str(py_file.relative_to(self.routes_dir))
                
                for match in matches:
                    func_name = match.group(1)
                    # Skip private/dunder methods
                    if not func_name.startswith('_'):
                        function_map[func_name].append(file_path)
                        
            except Exception as e:
                print(f"⚠️ Error parsing {py_file.name}: {e}")
        
        # Find duplicates
        duplicates_found = False
        self.duplicates = {}
        
        for func_name, files in function_map.items():
            if len(files) > 1:
                duplicates_found = True
                self.duplicates[func_name] = files
                print(f"\n  🔄 Duplicate function: {func_name}")
                for file in files:
                    print(f"     - {file}")
        
        if not duplicates_found:
            print("  ✅ No duplicate functions found!")
    
    def check_missing_imports(self):
        """Check for missing imports"""
        print("\n📌 Checking missing imports...")
        print("-" * 40)
        
        # Common imports that might be missing
        required_imports = {
            'require_auth': 'from auth import require_auth',
            'require_admin': 'from auth import require_admin',
            'require_org_member': 'from auth import require_org_member',
            'require_org_admin': 'from auth import require_org_admin',
            'require_role': 'from auth import require_role',
            'require_permission': 'from auth import require_permission',
            'get_current_user': 'from auth import get_current_user',
        }
        
        missing_found = False
        self.missing_imports = {}
        
        for py_file in self.routes_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or py_file.name == '__init__.py':
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_path = str(py_file.relative_to(self.routes_dir))
                missing = []
                
                for func_name, import_stmt in required_imports.items():
                    # Check if function is used AND import is missing
                    if func_name in content:
                        # Check if import exists
                        if import_stmt not in content:
                            # Also check for variations
                            import_variants = [
                                f'from auth import.*{func_name}',
                                f'from auth import.*\n.*{func_name}'
                            ]
                            found = False
                            for variant in import_variants:
                                if re.search(variant, content, re.DOTALL):
                                    found = True
                                    break
                            
                            if not found:
                                missing.append(func_name)
                
                if missing:
                    missing_found = True
                    self.missing_imports[file_path] = missing
                    print(f"\n  ⚠️ {file_path}")
                    for func in missing:
                        print(f"     - Missing: {func}")
                        
            except Exception as e:
                print(f"⚠️ Error reading {py_file.name}: {e}")
        
        if not missing_found:
            print("  ✅ All imports are present!")
    
    def check_duplicate_endpoints(self):
        """Check for duplicate endpoint paths"""
        print("\n📌 Checking duplicate endpoints...")
        print("-" * 40)
        
        endpoints = defaultdict(list)
        
        # Pattern to find route decorators
        route_pattern = r'@router\.(get|post|put|delete|patch|head|options)\s*\(\s*[\'"]([^\'"]+)[\'"]'
        
        duplicate_found = False
        self.duplicate_endpoints = {}
        
        for py_file in self.routes_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = re.finditer(route_pattern, content)
                file_path = str(py_file.relative_to(self.routes_dir))
                
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    # Only track non-empty paths
                    if path and path != '/':
                        endpoint_key = f"{method} {path}"
                        endpoints[endpoint_key].append(file_path)
                        
            except Exception as e:
                print(f"⚠️ Error reading {py_file.name}: {e}")
        
        # Find duplicates
        for endpoint, files in endpoints.items():
            if len(files) > 1:
                duplicate_found = True
                self.duplicate_endpoints[endpoint] = files
                print(f"\n  🔄 Duplicate endpoint: {endpoint}")
                for file in files:
                    print(f"     - {file}")
        
        if not duplicate_found:
            print("  ✅ No duplicate endpoints found!")
    
    def check_supabase_queries(self):
        """Check for common Supabase query issues"""
        print("\n📌 Checking Supabase queries...")
        print("-" * 40)
        
        issues_found = False
        
        for py_file in self.routes_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_path = str(py_file.relative_to(self.routes_dir))
                issues = []
                
                # Check for supabase queries without try/except
                if 'supabase.from_' in content:
                    # Check if there's a try block before any supabase call
                    if 'try:' not in content:
                        issues.append("Supabase query without try/except")
                
                # Check for .execute() without handling result
                if '.execute()' in content and 'result.data' not in content and 'result' not in content:
                    issues.append(".execute() called without result handling")
                
                # Check for potential SQL injection (raw SQL)
                if 'supabase.rpc' in content:
                    if 'params' not in content:
                        issues.append("RPC call without params")
                
                if issues:
                    issues_found = True
                    print(f"\n  ⚠️ {file_path}")
                    for issue in issues:
                        print(f"     - {issue}")
                        
            except Exception as e:
                print(f"⚠️ Error reading {py_file.name}: {e}")
        
        if not issues_found:
            print("  ✅ Supabase queries look good!")
    
    def check_error_handling(self):
        """Check for proper error handling"""
        print("\n📌 Checking error handling...")
        print("-" * 40)
        
        issues_found = False
        
        for py_file in self.routes_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_path = str(py_file.relative_to(self.routes_dir))
                issues = []
                
                # Check for bare except
                if 'except:' in content:
                    # Make sure it's not 'except Exception as e:'
                    if 'except Exception' not in content:
                        issues.append("Bare 'except:' found (use 'except Exception as e:')")
                
                # Check for try blocks without HTTPException
                if 'try:' in content:
                    if 'HTTPException' not in content:
                        issues.append("Try block without HTTPException handling")
                
                if issues:
                    issues_found = True
                    print(f"\n  ⚠️ {file_path}")
                    for issue in issues:
                        print(f"     - {issue}")
                        
            except Exception as e:
                print(f"⚠️ Error reading {py_file.name}: {e}")
        
        if not issues_found:
            print("  ✅ Error handling looks good!")
    
    def check_import_organization(self):
        """Check if imports are properly organized"""
        print("\n📌 Checking import organization...")
        print("-" * 40)
        
        issues_found = False
        
        for py_file in self.routes_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or py_file.name == '__init__.py':
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_path = str(py_file.relative_to(self.routes_dir))
                lines = content.split('\n')
                
                # Find where imports end and code begins
                import_lines = []
                code_start = 0
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('from ') or stripped.startswith('import '):
                        import_lines.append(i)
                    elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                        if not import_lines:
                            continue
                        code_start = i
                        break
                
                # Check if imports are mixed with code
                if import_lines and code_start > 0:
                    last_import = max(import_lines)
                    if last_import + 2 > code_start:
                        issues_found = True
                        print(f"\n  ⚠️ {file_path}")
                        print(f"     - Imports mixed with code (line {last_import + 1})")
                        
            except Exception as e:
                print(f"⚠️ Error reading {py_file.name}: {e}")
        
        if not issues_found:
            print("  ✅ Imports are well organized!")
    
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "="*70)
        print("📊 AUDIT SUMMARY")
        print("="*70)
        
        total_issues = (
            len(self.duplicates) + 
            len(self.missing_imports) + 
            len(self.duplicate_endpoints)
        )
        
        print(f"\n  📌 Duplicate Functions: {len(self.duplicates)}")
        print(f"  📌 Missing Imports: {len(self.missing_imports)}")
        print(f"  📌 Duplicate Endpoints: {len(self.duplicate_endpoints)}")
        
        if total_issues == 0:
            print("\n🎉 No issues found! Code is clean!")
        else:
            print(f"\n⚠️  {total_issues} issue(s) found. Check the details above.")
        
        print("="*70)

def main():
    # Find the root directory (where backend/ is located)
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent  # Go up from tests/ to backend/ to root/
    
    print(f"📂 Scanning root directory: {root_dir}")
    
    if not (root_dir / 'backend' / 'routes').exists():
        print(f"❌ Routes directory not found at: {root_dir / 'backend' / 'routes'}")
        print("   Please run this script from the project root directory")
        return
    
    auditor = CodeAuditor(root_dir)
    auditor.audit_all()

if __name__ == "__main__":
    main()