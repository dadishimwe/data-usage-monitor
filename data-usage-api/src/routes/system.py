"""
System API Routes
Handles system monitoring and backup operations
"""

from flask import Blueprint, request, jsonify
import sqlite3
import os
import psutil
import subprocess
from datetime import datetime

system_bp = Blueprint('system', __name__)

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data_usage.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@system_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get Raspberry Pi system status"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = round(memory.available / (1024**3), 2)  # GB
        memory_total = round(memory.total / (1024**3), 2)  # GB
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = round((disk.used / disk.total) * 100, 2)
        disk_free = round(disk.free / (1024**3), 2)  # GB
        disk_total = round(disk.total / (1024**3), 2)  # GB
        
        # System uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        # Database size
        db_size = 0
        if os.path.exists(DATABASE_PATH):
            db_size = round(os.path.getsize(DATABASE_PATH) / (1024**2), 2)  # MB
        
        # Temperature (Raspberry Pi specific)
        temperature = None
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_raw = f.read().strip()
                temperature = round(int(temp_raw) / 1000, 1)  # Convert to Celsius
        except:
            # Fallback for non-Raspberry Pi systems
            temperature = "N/A"
        
        return jsonify({
            'cpu_percent': cpu_percent,
            'memory': {
                'percent': memory_percent,
                'available_gb': memory_available,
                'total_gb': memory_total
            },
            'disk': {
                'percent': disk_percent,
                'free_gb': disk_free,
                'total_gb': disk_total
            },
            'uptime_days': uptime.days,
            'uptime_hours': uptime.seconds // 3600,
            'database_size_mb': db_size,
            'temperature_c': temperature,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/database-info', methods=['GET'])
def get_database_info():
    """Get database information and statistics"""
    try:
        conn = get_db_connection()
        
        # Get table counts
        locations_count = conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
        daily_usage_count = conn.execute("SELECT COUNT(*) FROM daily_usage").fetchone()[0]
        monthly_summaries_count = conn.execute("SELECT COUNT(*) FROM monthly_summaries").fetchone()[0]
        
        # Get date range
        date_range = conn.execute("SELECT MIN(date), MAX(date) FROM daily_usage").fetchone()
        
        # Get system info
        system_info = conn.execute("SELECT metric_name, metric_value, updated_at FROM system_info").fetchall()
        
        conn.close()
        
        # Database file info
        db_stats = {}
        if os.path.exists(DATABASE_PATH):
            stat = os.stat(DATABASE_PATH)
            db_stats = {
                'size_mb': round(stat.st_size / (1024**2), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        
        return jsonify({
            'table_counts': {
                'locations': locations_count,
                'daily_usage': daily_usage_count,
                'monthly_summaries': monthly_summaries_count
            },
            'date_range': {
                'start': date_range[0],
                'end': date_range[1]
            },
            'system_info': [dict(row) for row in system_info],
            'database_file': db_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/backup', methods=['POST'])
def create_backup():
    """Create database backup"""
    try:
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'data_usage_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy database file
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        
        # Update system info
        conn = get_db_connection()
        conn.execute("""
            UPDATE system_info 
            SET metric_value = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE metric_name = 'last_backup'
        """, (datetime.now().isoformat(),))
        conn.commit()
        conn.close()
        
        backup_size = round(os.path.getsize(backup_path) / (1024**2), 2)
        
        return jsonify({
            'message': 'Backup created successfully',
            'backup_file': backup_filename,
            'backup_path': backup_path,
            'backup_size_mb': backup_size,
            'timestamp': timestamp
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/backups', methods=['GET'])
def list_backups():
    """List available backups"""
    try:
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), 'backups')
        
        if not os.path.exists(backup_dir):
            return jsonify({'backups': []})
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db') and filename.startswith('data_usage_backup_'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'size_mb': round(stat.st_size / (1024**2), 2),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'backups': backups})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/logs', methods=['GET'])
def get_system_logs():
    """Get recent system logs (if available)"""
    try:
        logs = []
        
        # Try to get recent journal logs for the service
        try:
            result = subprocess.run(
                ['journalctl', '-u', 'data-usage-monitor', '-n', '50', '--no-pager'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                logs = result.stdout.split('\n')
        except:
            # Fallback to application logs if available
            log_file = os.path.join(os.path.dirname(DATABASE_PATH), 'app.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.readlines()[-50:]  # Last 50 lines
        
        return jsonify({
            'logs': logs,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

