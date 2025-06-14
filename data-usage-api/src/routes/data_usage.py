"""
Data Usage API Routes
Handles CRUD operations for daily usage data and locations
"""

from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, date

data_usage_bp = Blueprint('data_usage', __name__)

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data_usage.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@data_usage_bp.route('/locations', methods=['GET'])
def get_locations():
    """Get all active locations"""
    try:
        conn = get_db_connection()
        locations = conn.execute("""
            SELECT id, name, display_name, is_active 
            FROM locations 
            WHERE is_active = 1 
            ORDER BY display_name
        """).fetchall()
        conn.close()
        
        return jsonify([dict(location) for location in locations])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_usage_bp.route('/daily-usage', methods=['GET'])
def get_daily_usage():
    """Get daily usage data with optional filters"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        location_id = request.args.get('location_id')
        
        conn = get_db_connection()
        
        # Build query
        query = """
            SELECT du.id, du.date, du.usage_gb, du.updated_at,
                   l.id as location_id, l.name as location_name, l.display_name
            FROM daily_usage du
            JOIN locations l ON du.location_id = l.id
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND du.date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND du.date <= ?"
            params.append(end_date)
        
        if location_id:
            query += " AND du.location_id = ?"
            params.append(location_id)
        
        query += " ORDER BY du.date DESC, l.display_name"
        
        usage_data = conn.execute(query, params).fetchall()
        conn.close()
        
        return jsonify([dict(row) for row in usage_data])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_usage_bp.route('/daily-usage', methods=['POST'])
def add_daily_usage():
    """Add or update daily usage record"""
    try:
        data = request.get_json()
        
        required_fields = ['date', 'location_id', 'usage_gb']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO daily_usage (date, location_id, usage_gb, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (data['date'], data['location_id'], data['usage_gb']))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Daily usage record saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_usage_bp.route('/daily-usage/<int:usage_id>', methods=['PUT'])
def update_daily_usage(usage_id):
    """Update existing daily usage record"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        conn.execute("""
            UPDATE daily_usage 
            SET usage_gb = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data['usage_gb'], usage_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Daily usage record updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_usage_bp.route('/daily-usage/<int:usage_id>', methods=['DELETE'])
def delete_daily_usage(usage_id):
    """Delete daily usage record"""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM daily_usage WHERE id = ?", (usage_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Daily usage record deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_usage_bp.route('/monthly-summary', methods=['GET'])
def get_monthly_summaries():
    """Get monthly summary data"""
    try:
        location_id = request.args.get('location_id')
        
        conn = get_db_connection()
        
        query = """
            SELECT ms.id, ms.period_start, ms.period_end, ms.total_usage_gb, 
                   ms.manual_entry, ms.updated_at,
                   l.id as location_id, l.name as location_name, l.display_name
            FROM monthly_summaries ms
            JOIN locations l ON ms.location_id = l.id
            WHERE 1=1
        """
        params = []
        
        if location_id:
            query += " AND ms.location_id = ?"
            params.append(location_id)
        
        query += " ORDER BY ms.period_start DESC, l.display_name"
        
        summaries = conn.execute(query, params).fetchall()
        conn.close()
        
        return jsonify([dict(row) for row in summaries])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_usage_bp.route('/monthly-summary', methods=['POST'])
def add_monthly_summary():
    """Add or update monthly summary"""
    try:
        data = request.get_json()
        
        required_fields = ['period_start', 'period_end', 'location_id', 'total_usage_gb']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO monthly_summaries 
            (period_start, period_end, location_id, total_usage_gb, manual_entry, updated_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        """, (data['period_start'], data['period_end'], data['location_id'], data['total_usage_gb']))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Monthly summary saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

