#!/usr/bin/env python3
"""
CarbonTally Data Generator - Main Runner
Executes all data generation modules in the correct order.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from generators.core.generate_organizations import OrganizationGenerator


class DataGeneratorRunner:
    """Main runner for all data generation modules."""
    
    def __init__(self):
        """Initialize the runner."""
        self.config = Config()
        self.start_time = None
        self.end_time = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Track generation statistics
        self.stats = {
            "started": datetime.now(),
            "completed": None,
            "modules": {},
            "total_records": 0,
            "errors": 0
        }
        
        # Module execution order (maintaining dependencies)
        self.module_order = [
            # Phase 1: Core Identity
            {
                "module": "generate_organizations",
                "generator": OrganizationGenerator,
                "priority": 1,
                "description": "Organizations (100)"
            },
            # Phase 2-17: Additional modules will be added here
            # as they are developed
        ]
    
    def run_module(self, module_config: Dict[str, Any]) -> bool:
        """
        Run a single generation module.
        
        Args:
            module_config: Module configuration.
            
        Returns:
            True if successful, False otherwise.
        """
        module_name = module_config["module"]
        generator_class = module_config["generator"]
        description = module_config.get("description", module_name)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"▶️  Running: {description}")
        self.logger.info(f"{'='*60}")
        
        try:
            start = time.time()
            
            # Initialize generator
            generator = generator_class()
            
            # Generate data
            records = generator.generate()
            record_count = len(records)
            
            # Write to CSV
            output_file = generator.write_csv(records)
            
            elapsed = time.time() - start
            
            # Record stats
            self.stats["modules"][module_name] = {
                "records": record_count,
                "elapsed": elapsed,
                "output": str(output_file),
                "success": True
            }
            self.stats["total_records"] += record_count
            
            self.logger.info(f"✅ Completed in {elapsed:.2f} seconds")
            self.logger.info(f"📊 Generated {record_count} records")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            
            self.stats["modules"][module_name] = {
                "records": 0,
                "elapsed": 0,
                "success": False,
                "error": str(e)
            }
            self.stats["errors"] += 1
            return False
    
    def run_all(self) -> bool:
        """
        Run all generation modules.
        
        Returns:
            True if all succeeded, False otherwise.
        """
        self.logger.info("🚀 CarbonTally Demo Data Generator")
        self.logger.info("=" * 60)
        self.logger.info(f"📅 Started: {datetime.now()}")
        self.logger.info(f"📊 Target Scale: {self.config.SCALE}")
        self.logger.info("=" * 60)
        
        self.start_time = time.time()
        
        # Run each module in order
        all_success = True
        for module in self.module_order:
            success = self.run_module(module)
            if not success:
                all_success = False
                self.logger.error(f"❌ Module {module['module']} failed")
                # Continue with other modules unless critical
                if module.get("critical", False):
                    self.logger.error("🛑 Critical module failed - stopping")
                    break
        
        self.end_time = time.time()
        self.stats["completed"] = datetime.now()
        
        # Print summary
        self._print_summary()
        
        return all_success
    
    def _print_summary(self):
        """Print generation summary."""
        total_time = self.end_time - self.start_time
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 Generation Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Modules Executed: {len(self.stats['modules'])}")
        self.logger.info(f"📊 Total Records: {self.stats['total_records']:,}")
        self.logger.info(f"⏱️  Total Time: {total_time:.2f} seconds")
        self.logger.info(f"📉 Errors: {self.stats['errors']}")
        
        # Module breakdown
        self.logger.info("\n📋 Module Breakdown:")
        for module_name, stats in self.stats["modules"].items():
            status = "✅" if stats["success"] else "❌"
            records = stats.get("records", 0)
            elapsed = stats.get("elapsed", 0)
            self.logger.info(f"  {status} {module_name}: {records:,} records ({elapsed:.2f}s)")
        
        if self.stats["errors"] == 0:
            self.logger.info("\n🎉 All modules completed successfully!")
        else:
            self.logger.warning(f"\n⚠️  {self.stats['errors']} module(s) failed")
        
        self.logger.info("\n📁 Output Directory:")
        self.logger.info(f"   {self.config.OUTPUT_DIR.absolute()}")
        self.logger.info("=" * 60)


def main():
    """Main entry point."""
    runner = DataGeneratorRunner()
    success = runner.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()