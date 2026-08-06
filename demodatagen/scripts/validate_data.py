#!/usr/bin/env python3
"""
CarbonTally Data Generator - Data Validator
Validates generated data for quality and referential integrity.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set

sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from utils.data_validators import DataValidator


class DataValidatorCLI:
    """Command-line data validator."""
    
    def __init__(self):
        """Initialize validator."""
        self.config = Config()
        self.validator = DataValidator()
        self.errors = []
        self.warnings = []
    
    def validate_csv(self, filepath: Path) -> Dict[str, Any]:
        """Validate a single CSV file."""
        results = {
            "file": str(filepath),
            "records": 0,
            "errors": 0,
            "warnings": 0,
            "issues": []
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 2):
                    results["records"] += 1
                    
                    # Check for required fields
                    if not row.get('id'):
                        results["issues"].append({
                            "row": row_num,
                            "field": "id",
                            "issue": "Missing ID"
                        })
                        results["errors"] += 1
                    
                    # Check for empty values
                    for field, value in row.items():
                        if not value or value.strip() == '':
                            results["warnings"] += 1
                            results["issues"].append({
                                "row": row_num,
                                "field": field,
                                "issue": "Empty value"
                            })
                    
                    # Validate specific fields based on file name
                    if "organizations" in str(filepath):
                        self._validate_organization(row, row_num, results)
                    
                    elif "users" in str(filepath):
                        self._validate_user(row, row_num, results)
                    
                    elif "documents" in str(filepath):
                        self._validate_document(row, row_num, results)
        
        except Exception as e:
            results["issues"].append({
                "row": 0,
                "field": "file",
                "issue": f"Error reading file: {e}"
            })
            results["errors"] += 1
        
        return results
    
    def _validate_organization(self, row: Dict, row_num: int, results: Dict):
        """Validate organization record."""
        # Validate email
        if row.get('primary_contact_email'):
            if not self.validator.is_valid_email(row['primary_contact_email']):
                results["issues"].append({
                    "row": row_num,
                    "field": "primary_contact_email",
                    "issue": f"Invalid email: {row['primary_contact_email']}"
                })
                results["errors"] += 1
        
        # Validate VAT number
        if row.get('vat_number'):
            country = row.get('country', 'UK')
            if not self.validator.is_valid_vat_number(row['vat_number'], country):
                results["warnings"] += 1
                results["issues"].append({
                    "row": row_num,
                    "field": "vat_number",
                    "issue": f"Possible invalid VAT: {row['vat_number']} for {country}"
                })
        
        # Validate postcode
        if row.get('postcode'):
            country = row.get('country', 'UK')
            if not self.validator.is_valid_postcode(row['postcode'], country):
                results["warnings"] += 1
                results["issues"].append({
                    "row": row_num,
                    "field": "postcode",
                    "issue": f"Possible invalid postcode: {row['postcode']} for {country}"
                })
        
        # Validate dates
        for date_field in ['created_at', 'updated_at']:
            if row.get(date_field):
                if not self.validator.is_valid_date(row[date_field]):
                    results["warnings"] += 1
                    results["issues"].append({
                        "row": row_num,
                        "field": date_field,
                        "issue": f"Invalid date format: {row[date_field]}"
                    })
        
        # Validate JSON fields
        for json_field in ['metadata']:
            if row.get(json_field):
                if not self.validator.is_valid_json(row[json_field]):
                    results["warnings"] += 1
                    results["issues"].append({
                        "row": row_num,
                        "field": json_field,
                        "issue": "Invalid JSON format"
                    })
    
    def _validate_user(self, row: Dict, row_num: int, results: Dict):
        """Validate user record."""
        # Validate email
        if row.get('email'):
            if not self.validator.is_valid_email(row['email']):
                results["issues"].append({
                    "row": row_num,
                    "field": "email",
                    "issue": f"Invalid email: {row['email']}"
                })
                results["errors"] += 1
        
        # Validate user_type
        valid_types = ['staff', 'company_user', 'consultant', 'admin']
        if row.get('user_type') and row['user_type'] not in valid_types:
            results["warnings"] += 1
            results["issues"].append({
                "row": row_num,
                "field": "user_type",
                "issue": f"Unknown user type: {row['user_type']}"
            })
    
    def _validate_document(self, row: Dict, row_num: int, results: Dict):
        """Validate document record."""
        # Validate file name
        if row.get('file_name'):
            if len(row['file_name']) > 255:
                results["warnings"] += 1
                results["issues"].append({
                    "row": row_num,
                    "field": "file_name",
                    "issue": f"Filename too long ({len(row['file_name'])} chars)"
                })
        
        # Validate file URL
        if row.get('file_url'):
            if not row['file_url'].startswith(('http://', 'https://', '/')):
                results["warnings"] += 1
                results["issues"].append({
                    "row": row_num,
                    "field": "file_url",
                    "issue": "Invalid URL format"
                })
    
    def validate_directory(self, directory: Path) -> Dict[str, Any]:
        """Validate all CSV files in a directory."""
        results = {
            "directory": str(directory),
            "files": 0,
            "total_records": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "file_results": []
        }
        
        for filepath in directory.glob("*.csv"):
            file_result = self.validate_csv(filepath)
            results["files"] += 1
            results["total_records"] += file_result["records"]
            results["total_errors"] += file_result["errors"]
            results["total_warnings"] += file_result["warnings"]
            results["file_results"].append(file_result)
        
        return results
    
    def print_report(self, results: Dict[str, Any]):
        """Print validation report."""
        print("\n" + "=" * 60)
        print("📊 Data Validation Report")
        print("=" * 60)
        
        if results.get("directory"):
            print(f"📁 Directory: {results['directory']}")
        
        print(f"📁 Files Processed: {results.get('files', 0)}")
        print(f"📊 Total Records: {results.get('total_records', 0):,}")
        print(f"❌ Total Errors: {results.get('total_errors', 0)}")
        print(f"⚠️  Total Warnings: {results.get('total_warnings', 0)}")
        print("=" * 60)
        
        # Detailed file reports
        for file_result in results.get("file_results", []):
            if file_result.get("errors", 0) > 0 or file_result.get("warnings", 0) > 0:
                print(f"\n📄 {file_result['file']}")
                print(f"   Records: {file_result['records']}")
                print(f"   Errors: {file_result['errors']}")
                print(f"   Warnings: {file_result['warnings']}")
                
                # Show first 5 issues
                for issue in file_result.get("issues", [])[:5]:
                    print(f"   ⚠️  Row {issue['row']}: {issue['field']} - {issue['issue']}")
                
                if len(file_result.get("issues", [])) > 5:
                    print(f"   ... and {len(file_result['issues']) - 5} more issues")
        
        # Summary
        total_issues = results.get('total_errors', 0) + results.get('total_warnings', 0)
        if total_issues == 0:
            print("\n🎉 All data is valid!")
        else:
            print(f"\n⚠️  Found {total_issues} issues to review")


def main():
    """Main entry point."""
    config = Config()
    validator = DataValidatorCLI()
    
    print("🔍 CarbonTally Data Validator")
    print("=" * 60)
    
    # Validate output directory
    output_dir = config.OUTPUT_DIR
    
    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        sys.exit(1)
    
    if not any(output_dir.glob("*.csv")):
        print(f"⚠️  No CSV files found in {output_dir}")
        print("   Run the generators first:")
        print("   python scripts/run_all_generators.py")
        sys.exit(1)
    
    # Run validation
    results = validator.validate_directory(output_dir)
    
    # Print report
    validator.print_report(results)
    
    # Exit with error code if errors found
    if results.get("total_errors", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()