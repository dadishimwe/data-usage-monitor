-- Database schema for Data Usage Monitor
-- SQLite database for Raspberry Pi deployment

-- Table to store location information
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store daily usage data
CREATE TABLE IF NOT EXISTS daily_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    location_id INTEGER NOT NULL,
    usage_gb REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations (id),
    UNIQUE(date, location_id)
);

-- Table to store monthly summaries (13th to 12th cycle)
CREATE TABLE IF NOT EXISTS monthly_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start DATE NOT NULL, -- 13th of the month
    period_end DATE NOT NULL,   -- 12th of next month
    location_id INTEGER NOT NULL,
    total_usage_gb REAL DEFAULT 0,
    manual_entry BOOLEAN DEFAULT 1, -- Flag to indicate manual entry
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations (id),
    UNIQUE(period_start, location_id)
);

-- Table to store system information for dashboard
CREATE TABLE IF NOT EXISTS system_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL UNIQUE,
    metric_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_daily_usage_date ON daily_usage(date);
CREATE INDEX IF NOT EXISTS idx_daily_usage_location ON daily_usage(location_id);
CREATE INDEX IF NOT EXISTS idx_monthly_summaries_period ON monthly_summaries(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_monthly_summaries_location ON monthly_summaries(location_id);

-- Insert initial system info metrics
INSERT OR IGNORE INTO system_info (metric_name, metric_value) VALUES 
    ('last_backup', 'Never'),
    ('database_size', '0 MB'),
    ('total_records', '0'),
    ('app_version', '1.0.0');

