#!/usr/bin/env python3
"""
CarbonTally Data Generator - SQL Exporter
Converts CSV files to SQL INSERT statements.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from config import Config


class SQLExporter:
    """Export CSV data to SQL INSERT statements."""
    
    def __init__(self, output_format: str = "postgres"):
        """
        Initialize exporter.
        
        Args:
            output_format: SQL dialect (postgres, mysql, sqlite)
        """
        self.config = Config()
        self.output_format = output_format
        self.batch_size = 1000
        
        # SQL dialect settings
        self.dialects = {
            "postgres": {
                "quote": '"',
                "escape": "''",
                "null": "NULL",
                "bool_true": "TRUE",
                "bool_false": "FALSE",
                "date_format": "YYYY-MM-DD HH24:MI:SS",
                "json_cast": lambda x: f"'{json.dumps(x)}'::jsonb"
            },
            "mysql": {
                "quote": "`",
                "escape": "\\'",
                "null": "NULL",
                "bool_true": "1",
                "bool_false": "0",
                "date_format": "%Y-%m-%d %H:%i:%s",
                "json_cast": lambda x: f"'{json.dumps(x)}'"
            },
            "sqlite": {
                "quote": '"',
                "escape": "''",
                "null": "NULL",
                "bool_true": "1",
                "bool_false": "0",
                "date_format": "%Y-%m-%d %H:%M:%S",
                "json_cast": lambda x: f"'{json.dumps(x)}'"
            }
        }
        
        self.dialect = self.dialects.get(output_format, self.dialects["postgres"])
    
    def escape_value(self, value: Any, field_type: str = "text") -> str:
        """Escape a value for SQL."""
        if value is None or value == "":
            return self.dialect["null"]
        
        # Handle boolean
        if isinstance(value, bool):
            return self.dialect["bool_true"] if value else self.dialect["bool_false"]
        
        # Handle numeric
        if isinstance(value, (int, float)):
            return str(value)
        
        # Handle datetime
        if isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        
        # Handle JSON
        if field_type == "json" and isinstance(value, (dict, list)):
            return self.dialect["json_cast"](value)
        
        # Handle string
        if isinstance(value, str):
            escaped = value.replace("'", self.dialect["escape"])
            return f"'{escaped}'"
        
        return str(value)
    
    def csv_to_sql(self, csv_file: Path, table_name: Optional[str] = None) -> str:
        """
        Convert a CSV file to SQL INSERT statements.
        
        Args:
            csv_file: Path to CSV file.
            table_name: Table name (default: from filename).
            
        Returns:
            SQL INSERT statements.
        """
        if table_name is None:
            table_name = csv_file.stem
        
        sql_statements = []
        sql_statements.append(f"-- {csv_file.name}")
        sql_statements.append(f"-- Records: (to be counted)")
        sql_statements.append(f"-- Generated: {datetime.now()}")
        sql_statements.append("")
        
        # Read CSV
        records = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
        
        if not records:
            return "-- No records found"
        
        # Get field names
        fields = records[0].keys()
        
        # Build INSERT statement
        quote = self.dialect["quote"]
        field_list = ', '.join([f"{quote}{field}{quote}" for field in fields])
        insert_template = f"INSERT INTO {quote}{table_name}{quote} ({field_list}) VALUES"
        
        # Process in batches
        total_inserts = 0
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            # Build value lists
            value_lists = []
            for record in batch:
                values = []
                for field in fields:
                    value = record.get(field, None)
                    # Determine field type (heuristic)
                    field_type = "text"
                    if field in ["id", "created_at", "updated_at"]:
                        field_type = "text"
                    elif field == "metadata":
                        field_type = "json"
                    elif field.endswith("_at"):
                        field_type = "datetime"
                    
                    values.append(self.escape_value(value, field_type))
                
                value_lists.append(f"({', '.join(values)})")
            
            # Build complete INSERT
            insert = f"{insert_template}\n  {',\n  '.join(value_lists)};"
            sql_statements.append(insert)
            total_inserts += len(batch)
        
        # Add comment with count
        sql_statements[1] = f"-- Records: {total_inserts}"
        
        return '\n\n'.join(sql_statements)
    
    def convert_directory(
        self, 
        input_dir: Optional[Path] = None,
        output_file: Optional[Path] = None,
        table_mapping: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Convert all CSV files in a directory to SQL.
        
        Args:
            input_dir: Input directory (default: output_dir).
            output_file: Output SQL file.
            table_mapping: Map CSV filenames to table names.
        """
        input_dir = input_dir or self.config.OUTPUT_DIR
        output_file = output_file or self.config.OUTPUT_DIR / "seed_data.sql"
        
        table_mapping = table_mapping or {}
        
        # Get all CSV files
        csv_files = sorted(input_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"⚠️  No CSV files found in {input_dir}")
            return
        
        print(f"📁 Processing {len(csv_files)} CSV files...")
        
        # Generate SQL
        all_sql = []
        all_sql.append("-- ============================================")
        all_sql.append("-- CarbonTally Demo Data - SQL Seed")
        all_sql.append("-- Generated: " + datetime.now().isoformat())
        all_sql.append("-- Database: " + self.output_format.upper())
        all_sql.append("-- ============================================")
        all_sql.append("")
        all_sql.append("-- Enable required extensions")
        all_sql.append("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        all_sql.append("")
        
        # Process each CSV
        for csv_file in csv_files:
            table_name = table_mapping.get(csv_file.stem, csv_file.stem)
            print(f"  📄 {csv_file.name} → {table_name}")
            
            sql = self.csv_to_sql(csv_file, table_name)
            all_sql.append(sql)
            all_sql.append("")
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_sql))
        
        print(f"\n✅ SQL generated successfully")
        print(f"📁 Output: {output_file}")
        print(f"📊 Total records: (see individual file comments)")


def main():
    """Main entry point."""
    config = Config()
    exporter = SQLExporter()
    
    print("🗄️  CarbonTally SQL Exporter")
    print("=" * 60)
    
    # Export
    exporter.convert_directory()
    
    print("\n💡 To import into PostgreSQL:")
    print(f"   psql -d carbontally -f {config.OUTPUT_DIR / 'seed_data.sql'}")


if __name__ == "__main__":
    main()