#!/usr/bin/env python3
"""
CarbonTally Data Generator - Base Generator
Abstract base class for all data generators.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import csv
import json
import logging
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from utils import DataValidator, IDGenerator, DateUtils

# Type variable for the record type
T = TypeVar('T')


class BaseGenerator(ABC, Generic[T]):
    """
    Abstract base class for data generators.
    
    Provides common functionality for CSV generation, logging,
    and data validation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the generator.
        
        Args:
            config: Configuration object. If None, uses default.
        """
        self.config = config or Config()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize random seed
        random.seed(self.config.RANDOM_SEED)
        
        # Initialize utilities
        self.id_gen = IDGenerator()
        self.date_utils = DateUtils()
        self.validator = DataValidator()
        
        # Track generated records
        self.generated_count = 0
        self.error_count = 0
        
        # Ensure output directory exists
        self.config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def generate(self) -> List[T]:
        """
        Generate the data records.
        
        Returns:
            List of generated records.
        """
        pass
    
    @abstractmethod
    def to_csv_row(self, record: T) -> Dict[str, Any]:
        """
        Convert a record to CSV row format.
        
        Args:
            record: The record to convert.
            
        Returns:
            Dictionary ready for CSV writing.
        """
        pass
    
    @abstractmethod
    def get_csv_fields(self) -> List[str]:
        """
        Get the CSV field names.
        
        Returns:
            List of field names for CSV header.
        """
        pass
    
    def write_csv(self, records: List[T], filename: Optional[str] = None) -> Path:
        """
        Write records to a CSV file.
        
        Args:
            records: List of records to write.
            filename: Output filename (default: based on class name).
            
        Returns:
            Path to the output file.
        """
        if not records:
            self.logger.warning("No records to write")
            return None
        
        if filename is None:
            filename = f"{self.__class__.__name__.replace('Generator', '').lower()}.csv"
        
        filepath = self.config.OUTPUT_DIR / filename
        
        # Get field names
        fieldnames = self.get_csv_fields()
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding=self.config.CSV_ENCODING) as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=self.config.CSV_DELIMITER,
                quotechar=self.config.CSV_QUOTE_CHAR,
                quoting=csv.QUOTE_MINIMAL
            )
            writer.writeheader()
            
            # Use tqdm for progress if enabled
            iterator = tqdm(records, desc=f"Writing {filename}") if self.config.ENABLE_PROGRESS_BAR else records
            
            for record in iterator:
                writer.writerow(self.to_csv_row(record))
        
        self.logger.info(f"Wrote {len(records)} records to {filepath}")
        return filepath
    
    def generate_batch(
        self,
        generator_func,
        total: int,
        batch_size: Optional[int] = None,
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate data in batches to manage memory.
        
        Args:
            generator_func: Function that yields records
            total: Total number of records to generate
            batch_size: Size of each batch
            filename: Output filename
            
        Returns:
            Path to the output file.
        """
        batch_size = batch_size or self.config.BATCH_SIZE
        filepath = self.config.OUTPUT_DIR / (filename or f"{self.__class__.__name__.replace('Generator', '').lower()}.csv")
        
        # Get field names
        fieldnames = self.get_csv_fields()
        
        # Write CSV in batches
        with open(filepath, 'w', newline='', encoding=self.config.CSV_ENCODING) as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=self.config.CSV_DELIMITER,
                quotechar=self.config.CSV_QUOTE_CHAR,
                quoting=csv.QUOTE_MINIMAL
            )
            writer.writeheader()
            
            # Generate in batches
            records_written = 0
            batch = []
            
            iterator = tqdm(range(total), desc=f"Generating {filename}") if self.config.ENABLE_PROGRESS_BAR else range(total)
            
            for i in iterator:
                record = generator_func()
                batch.append(self.to_csv_row(record))
                records_written += 1
                
                if len(batch) >= batch_size:
                    writer.writerows(batch)
                    batch = []
            
            # Write remaining
            if batch:
                writer.writerows(batch)
        
        self.logger.info(f"Generated {records_written} records to {filepath}")
        return filepath
    
    def validate_record(self, record: T, schema: Dict[str, Any]) -> bool:
        """
        Validate a record against a schema.
        
        Args:
            record: The record to validate
            schema: Validation schema
            
        Returns:
            True if valid, False otherwise.
        """
        try:
            # Convert to dict for validation
            record_dict = self.to_csv_row(record)
            
            # Check required fields
            required = schema.get('required', [])
            missing = self.validator.validate_required_fields(record_dict, required)
            
            if missing:
                self.logger.warning(f"Missing required fields: {missing}")
                return False
            
            # Check data types
            type_map = schema.get('types', {})
            type_errors = self.validator.validate_data_types(record_dict, type_map)
            
            if type_errors:
                self.logger.warning(f"Type errors: {type_errors}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False
    
    def get_generated_count(self) -> int:
        """Get the number of generated records."""
        return self.generated_count
    
    def get_error_count(self) -> int:
        """Get the number of errors encountered."""
        return self.error_count
    
    def reset_counts(self) -> None:
        """Reset counters."""
        self.generated_count = 0
        self.error_count = 0