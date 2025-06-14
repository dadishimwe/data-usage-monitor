#!/usr/bin/env python3
"""
Backup Management System for Data Usage Monitor
Handles database backups, restoration, and scheduled operations
"""

import os
import sys
import sqlite3
import shutil
import gzip
import json
import argparse
from datetime import datetime, timedelta
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, db_path='data_usage.db', backup_dir='backups'):
        self.db_path = os.path.abspath(db_path)
        self.backup_dir = os.path.abspath(backup_dir)
        self.config_file = os.path.join(self.backup_dir, 'backup_config.json')
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Default configuration
        self.default_config = {
            'retention_days': 30,
            'max_backups': 50,
            'compress_backups': True,
            'backup_schedule': 'daily',
            'notification_email': None
        }
        
        self.config = self.load_config()
    
    def load_config(self):
        """Load backup configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                return {**self.default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config, using defaults: {e}")
        
        return self.default_config.copy()
    
    def save_config(self):
        """Save backup configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def create_backup(self, backup_name=None):
        """Create a database backup"""
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found: {self.db_path}")
            return False
        
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if backup_name:
                filename = f"{backup_name}_{timestamp}.db"
            else:
                filename = f"data_usage_backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backup_dir, filename)
            
            # Create backup using SQLite backup API for consistency
            self._create_sqlite_backup(backup_path)
            
            # Compress if enabled
            if self.config['compress_backups']:
                compressed_path = backup_path + '.gz'
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                os.remove(backup_path)
                backup_path = compressed_path
                filename = filename + '.gz'
            
            # Get backup size
            backup_size = os.path.getsize(backup_path)
            backup_size_mb = round(backup_size / (1024 * 1024), 2)
            
            # Update database with backup info
            self._update_backup_info(filename, backup_size_mb)
            
            logger.info(f"Backup created successfully: {filename} ({backup_size_mb} MB)")
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            return {
                'filename': filename,
                'path': backup_path,
                'size_mb': backup_size_mb,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _create_sqlite_backup(self, backup_path):
        """Create SQLite backup using the backup API"""
        source_conn = sqlite3.connect(self.db_path)
        backup_conn = sqlite3.connect(backup_path)
        
        try:
            source_conn.backup(backup_conn)
            logger.info("SQLite backup completed successfully")
        finally:
            source_conn.close()
            backup_conn.close()
    
    def _update_backup_info(self, filename, size_mb):
        """Update system info with backup details"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE system_info 
                SET metric_value = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE metric_name = 'last_backup'
            """, (datetime.now().isoformat(),))
            
            cursor.execute("""
                INSERT OR REPLACE INTO system_info (metric_name, metric_value, updated_at)
                VALUES ('last_backup_size', ?, CURRENT_TIMESTAMP)
            """, (f"{size_mb} MB",))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"Failed to update backup info in database: {e}")
    
    def restore_backup(self, backup_filename, confirm=False):
        """Restore database from backup"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        if not confirm:
            logger.warning("Restore operation requires confirmation. Use --confirm flag.")
            return False
        
        try:
            # Create a backup of current database before restore
            current_backup = self.create_backup("pre_restore")
            if current_backup:
                logger.info(f"Current database backed up as: {current_backup['filename']}")
            
            # Handle compressed backups
            restore_path = backup_path
            if backup_filename.endswith('.gz'):
                # Decompress to temporary file
                temp_path = backup_path[:-3]  # Remove .gz extension
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_path = temp_path
            
            # Restore database
            shutil.copy2(restore_path, self.db_path)
            
            # Clean up temporary file if created
            if restore_path != backup_path:
                os.remove(restore_path)
            
            logger.info(f"Database restored successfully from: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db') or filename.endswith('.db.gz'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'compressed': filename.endswith('.gz')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            backups = self.list_backups()
            
            # Remove backups older than retention period
            cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
            removed_count = 0
            
            for backup in backups:
                if backup['created'] < cutoff_date:
                    backup_path = os.path.join(self.backup_dir, backup['filename'])
                    os.remove(backup_path)
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup['filename']}")
            
            # Remove excess backups if over max limit
            remaining_backups = self.list_backups()
            if len(remaining_backups) > self.config['max_backups']:
                excess_count = len(remaining_backups) - self.config['max_backups']
                # Remove oldest backups
                for backup in remaining_backups[-excess_count:]:
                    backup_path = os.path.join(self.backup_dir, backup['filename'])
                    os.remove(backup_path)
                    removed_count += 1
                    logger.info(f"Removed excess backup: {backup['filename']}")
            
            if removed_count > 0:
                logger.info(f"Cleanup completed: {removed_count} backups removed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def verify_backup(self, backup_filename):
        """Verify backup integrity"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Handle compressed backups
            test_path = backup_path
            if backup_filename.endswith('.gz'):
                # Decompress to temporary file for testing
                temp_path = backup_path + '.test'
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                test_path = temp_path
            
            # Test database integrity
            conn = sqlite3.connect(test_path)
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            # Count tables and records
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            conn.close()
            
            # Clean up temporary file if created
            if test_path != backup_path:
                os.remove(test_path)
            
            if result == 'ok':
                logger.info(f"Backup verification successful: {backup_filename}")
                logger.info(f"Tables found: {len(tables)}")
                return True
            else:
                logger.error(f"Backup verification failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify backup: {e}")
            return False
    
    def setup_cron_job(self, schedule='daily'):
        """Setup cron job for automatic backups"""
        try:
            script_path = os.path.abspath(__file__)
            
            # Define cron schedules
            schedules = {
                'hourly': '0 * * * *',
                'daily': '0 2 * * *',      # 2 AM daily
                'weekly': '0 2 * * 0',     # 2 AM every Sunday
                'monthly': '0 2 1 * *'     # 2 AM on 1st of month
            }
            
            if schedule not in schedules:
                logger.error(f"Invalid schedule: {schedule}")
                return False
            
            cron_command = f"{schedules[schedule]} cd {os.path.dirname(script_path)} && python3 {script_path} --backup --auto >> backup.log 2>&1"
            
            # Add to crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Remove existing backup job
            lines = current_crontab.split('\n')
            filtered_lines = [line for line in lines if 'data_usage_backup' not in line and script_path not in line]
            
            # Add new job
            filtered_lines.append(f"# Data Usage Monitor Backup - {schedule}")
            filtered_lines.append(cron_command)
            
            new_crontab = '\n'.join(filtered_lines)
            
            # Install new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                logger.info(f"Cron job setup successfully for {schedule} backups")
                self.config['backup_schedule'] = schedule
                self.save_config()
                return True
            else:
                logger.error("Failed to setup cron job")
                return False
                
        except Exception as e:
            logger.error(f"Failed to setup cron job: {e}")
            return False
    
    def remove_cron_job(self):
        """Remove backup cron job"""
        try:
            script_path = os.path.abspath(__file__)
            
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.info("No crontab found")
                return True
            
            current_crontab = result.stdout
            
            # Remove backup-related lines
            lines = current_crontab.split('\n')
            filtered_lines = [line for line in lines if 'data_usage_backup' not in line and script_path not in line]
            
            new_crontab = '\n'.join(filtered_lines)
            
            # Install new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                logger.info("Backup cron job removed successfully")
                return True
            else:
                logger.error("Failed to remove cron job")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove cron job: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Data Usage Monitor Backup Manager')
    parser.add_argument('--backup', action='store_true', help='Create a backup')
    parser.add_argument('--restore', type=str, help='Restore from backup file')
    parser.add_argument('--list', action='store_true', help='List all backups')
    parser.add_argument('--verify', type=str, help='Verify backup integrity')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old backups')
    parser.add_argument('--setup-cron', type=str, choices=['hourly', 'daily', 'weekly', 'monthly'], 
                       help='Setup automatic backup schedule')
    parser.add_argument('--remove-cron', action='store_true', help='Remove automatic backup schedule')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    parser.add_argument('--db-path', type=str, default='data_usage.db', help='Database file path')
    parser.add_argument('--backup-dir', type=str, default='backups', help='Backup directory')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive operations')
    parser.add_argument('--auto', action='store_true', help='Automatic mode (for cron jobs)')
    
    args = parser.parse_args()
    
    # Initialize backup manager
    backup_manager = BackupManager(args.db_path, args.backup_dir)
    
    if args.backup:
        result = backup_manager.create_backup()
        if result:
            print(f"Backup created: {result['filename']} ({result['size_mb']} MB)")
        else:
            sys.exit(1)
    
    elif args.restore:
        success = backup_manager.restore_backup(args.restore, args.confirm)
        if not success:
            sys.exit(1)
    
    elif args.list:
        backups = backup_manager.list_backups()
        if backups:
            print(f"{'Filename':<40} {'Size (MB)':<10} {'Created':<20} {'Compressed'}")
            print("-" * 80)
            for backup in backups:
                compressed = "Yes" if backup['compressed'] else "No"
                print(f"{backup['filename']:<40} {backup['size_mb']:<10} {backup['created'].strftime('%Y-%m-%d %H:%M'):<20} {compressed}")
        else:
            print("No backups found")
    
    elif args.verify:
        success = backup_manager.verify_backup(args.verify)
        if not success:
            sys.exit(1)
    
    elif args.cleanup:
        backup_manager.cleanup_old_backups()
    
    elif args.setup_cron:
        success = backup_manager.setup_cron_job(args.setup_cron)
        if not success:
            sys.exit(1)
    
    elif args.remove_cron:
        success = backup_manager.remove_cron_job()
        if not success:
            sys.exit(1)
    
    elif args.config:
        print("Current Configuration:")
        for key, value in backup_manager.config.items():
            print(f"  {key}: {value}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

