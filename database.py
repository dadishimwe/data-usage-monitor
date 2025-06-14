#!/usr/bin/env python3
"""
Database initialization and management for Data Usage Monitor
"""

import sqlite3
import os
import csv
from datetime import datetime, date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path='data_usage.db'):
        self.db_path = db_path
        self.schema_path = 'schema.sql'
    
    def initialize_database(self):
        """Initialize the database with schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Read and execute schema
                with open(self.schema_path, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def import_locations_from_csv(self, csv_file_path):
        """Extract and import location names from CSV header"""
        try:
            with open(csv_file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
            # Skip the 'Date' column, get all location names
            locations = headers[1:]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for location in locations:
                    # Clean up location name and create display name
                    clean_name = location.strip()
                    display_name = clean_name.replace('_', ' ').title()
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO locations (name, display_name) 
                        VALUES (?, ?)
                    """, (clean_name, display_name))
                
                conn.commit()
                logger.info(f"Imported {len(locations)} locations")
                return True
                
        except Exception as e:
            logger.error(f"Error importing locations: {e}")
            return False
    
    def import_daily_usage_from_csv(self, csv_file_path):
        """Import daily usage data from CSV"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get location mappings
                cursor.execute("SELECT name, id FROM locations")
                location_map = dict(cursor.fetchall())
                
                with open(csv_file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        date_str = row['Date']
                        if not date_str:
                            continue
                            
                        # Parse date (format: DD-MMM)
                        try:
                            # Add current year for parsing
                            date_obj = datetime.strptime(f"{date_str}-2024", "%d-%b-%Y").date()
                        except ValueError:
                            logger.warning(f"Skipping invalid date: {date_str}")
                            continue
                        
                        # Import usage for each location
                        for location_name, location_id in location_map.items():
                            usage_value = row.get(location_name, '')
                            
                            if usage_value and usage_value.strip():
                                try:
                                    usage_gb = float(usage_value)
                                    
                                    cursor.execute("""
                                        INSERT OR REPLACE INTO daily_usage 
                                        (date, location_id, usage_gb, updated_at) 
                                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                    """, (date_obj, location_id, usage_gb))
                                    
                                except ValueError:
                                    # Skip non-numeric values
                                    continue
                
                conn.commit()
                
                # Update system info
                cursor.execute("SELECT COUNT(*) FROM daily_usage")
                total_records = cursor.fetchone()[0]
                
                cursor.execute("""
                    UPDATE system_info 
                    SET metric_value = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE metric_name = 'total_records'
                """, (str(total_records),))
                
                conn.commit()
                logger.info(f"Imported daily usage data. Total records: {total_records}")
                return True
                
        except Exception as e:
            logger.error(f"Error importing daily usage data: {e}")
            return False
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Get table counts
                cursor.execute("SELECT COUNT(*) FROM locations")
                stats['locations'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM daily_usage")
                stats['daily_records'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM monthly_summaries")
                stats['monthly_records'] = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM daily_usage")
                date_range = cursor.fetchone()
                stats['date_range'] = date_range
                
                # Get database file size
                if os.path.exists(self.db_path):
                    size_bytes = os.path.getsize(self.db_path)
                    stats['db_size_mb'] = round(size_bytes / (1024 * 1024), 2)
                else:
                    stats['db_size_mb'] = 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

def main():
    """Main function to initialize database and import data"""
    db_manager = DatabaseManager()
    
    # Initialize database
    if not db_manager.initialize_database():
        logger.error("Failed to initialize database")
        return
    
    # Import data from CSV if it exists
    csv_file = '../upload/WEEKLY_REPORTS(datausage).csv'
    if os.path.exists(csv_file):
        logger.info("Importing data from CSV...")
        
        if db_manager.import_locations_from_csv(csv_file):
            logger.info("Locations imported successfully")
        
        if db_manager.import_daily_usage_from_csv(csv_file):
            logger.info("Daily usage data imported successfully")
        
        # Show stats
        stats = db_manager.get_database_stats()
        logger.info(f"Database stats: {stats}")
    else:
        logger.warning(f"CSV file not found: {csv_file}")

if __name__ == "__main__":
    main()

