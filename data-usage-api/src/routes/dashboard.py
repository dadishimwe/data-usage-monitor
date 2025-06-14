"""
Dashboard API Routes
Provides aggregated data for dashboard views
"""

from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data_usage.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@dashboard_bp.route('/overview', methods=['GET'])
def get_dashboard_overview():
    """Get dashboard overview data"""
    try:
        conn = get_db_connection()
        
        # Get total locations
        total_locations = conn.execute("SELECT COUNT(*) FROM locations WHERE is_active = 1").fetchone()[0]
        
        # Get total daily records
        total_records = conn.execute("SELECT COUNT(*) FROM daily_usage").fetchone()[0]
        
        # Get date range
        date_range = conn.execute("SELECT MIN(date), MAX(date) FROM daily_usage").fetchone()
        
        # Get recent activity (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).date()
        recent_activity = conn.execute("""
            SELECT COUNT(*) FROM daily_usage 
            WHERE date >= ?
        """, (seven_days_ago,)).fetchone()[0]
        
        # Get top 5 locations by recent usage
        top_locations = conn.execute("""
            SELECT l.display_name, SUM(du.usage_gb) as total_usage
            FROM daily_usage du
            JOIN locations l ON du.location_id = l.id
            WHERE du.date >= ?
            GROUP BY l.id, l.display_name
            ORDER BY total_usage DESC
            LIMIT 5
        """, (seven_days_ago,)).fetchall()
        
        conn.close()
        
        return jsonify({
            'total_locations': total_locations,
            'total_records': total_records,
            'date_range': {
                'start': date_range[0],
                'end': date_range[1]
            },
            'recent_activity': recent_activity,
            'top_locations': [dict(row) for row in top_locations]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/usage-trends', methods=['GET'])
def get_usage_trends():
    """Get usage trends data for charts"""
    try:
        days = request.args.get('days', 30, type=int)
        location_id = request.args.get('location_id')
        
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        conn = get_db_connection()
        
        query = """
            SELECT du.date, l.display_name, SUM(du.usage_gb) as daily_total
            FROM daily_usage du
            JOIN locations l ON du.location_id = l.id
            WHERE du.date >= ?
        """
        params = [start_date]
        
        if location_id:
            query += " AND du.location_id = ?"
            params.append(location_id)
        
        query += " GROUP BY du.date, l.id, l.display_name ORDER BY du.date"
        
        trends = conn.execute(query, params).fetchall()
        conn.close()
        
        return jsonify([dict(row) for row in trends])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/location-summary', methods=['GET'])
def get_location_summary():
    """Get summary data for each location"""
    try:
        period = request.args.get('period', 'month')  # week, month, year
        
        conn = get_db_connection()
        
        if period == 'week':
            date_filter = (datetime.now() - timedelta(days=7)).date()
        elif period == 'month':
            date_filter = (datetime.now() - timedelta(days=30)).date()
        else:  # year
            date_filter = (datetime.now() - timedelta(days=365)).date()
        
        summary = conn.execute("""
            SELECT 
                l.id,
                l.display_name,
                COUNT(du.id) as record_count,
                SUM(du.usage_gb) as total_usage,
                AVG(du.usage_gb) as avg_usage,
                MAX(du.usage_gb) as max_usage,
                MIN(du.usage_gb) as min_usage,
                MAX(du.date) as last_update
            FROM locations l
            LEFT JOIN daily_usage du ON l.id = du.location_id AND du.date >= ?
            WHERE l.is_active = 1
            GROUP BY l.id, l.display_name
            ORDER BY total_usage DESC
        """, (date_filter,)).fetchall()
        
        conn.close()
        
        return jsonify([dict(row) for row in summary])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent-updates', methods=['GET'])
def get_recent_updates():
    """Get recent data updates"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        
        recent = conn.execute("""
            SELECT 
                du.date,
                du.usage_gb,
                du.updated_at,
                l.display_name
            FROM daily_usage du
            JOIN locations l ON du.location_id = l.id
            ORDER BY du.updated_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        conn.close()
        
        return jsonify([dict(row) for row in recent])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

