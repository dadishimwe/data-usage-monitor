# Data Usage Monitor - README

A comprehensive web application for monitoring data usage on Raspberry Pi, built with Python, Flask, and SQLite.

## Features

- **Web Dashboard**: Modern, responsive interface for viewing data usage statistics
- **SQLite Database**: Lightweight, reliable data storage optimized for Raspberry Pi
- **Automated Backups**: Comprehensive backup system with scheduling and retention policies
- **System Monitoring**: Real-time system status including CPU, memory, disk, and temperature
- **CSV Import**: Easy migration from existing spreadsheet-based tracking
- **Monthly Summaries**: Manual entry support for monthly billing periods (13th to 12th)
- **Raspberry Pi Optimized**: Designed specifically for single-board computer deployment

## Quick Start

1. **Download and Extract**:
   ```bash
   # Extract the application files to your Raspberry Pi
   tar -xzf data-usage-monitor.tar.gz
   cd data-usage-monitor
   ```

2. **Run Automated Installation**:
   ```bash
   sudo ./setup.sh install
   ```

3. **Access Dashboard**:
   Open your web browser and navigate to:
   ```
   http://your-raspberry-pi-ip:5000
   ```

## System Requirements

- Raspberry Pi 3B+ or newer (Raspberry Pi 4 recommended)
- 1GB RAM minimum (2GB+ recommended)
- 8GB storage minimum (16GB+ recommended)
- Raspberry Pi OS (Bullseye or newer)
- Python 3.7+

## File Structure

```
data-usage-monitor/
├── README.md                     # This file
├── DEPLOYMENT_GUIDE.md           # Comprehensive deployment documentation
├── setup.sh                      # Automated installation script
├── database.py                   # Database management and CSV import
├── backup_manager.py             # Backup and restore functionality
├── schema.sql                    # Database schema definition
├── test_application.py           # Application test suite
├── data-usage-api/               # Flask web application
│   ├── requirements.txt          # Python dependencies
│   ├── venv/                     # Python virtual environment
│   └── src/
│       ├── main.py               # Application entry point
│       ├── routes/               # API endpoints
│       │   ├── data_usage.py     # Data management APIs
│       │   ├── dashboard.py      # Dashboard APIs
│       │   └── system.py         # System monitoring APIs
│       └── static/               # Web interface
│           ├── index.html        # Main dashboard page
│           ├── styles.css        # Styling
│           └── app.js            # Frontend JavaScript
└── backups/                      # Database backups (created during setup)
```

## Key Features

### Dashboard Interface
- **Overview Tab**: Summary statistics and recent activity
- **Data Usage Tab**: Detailed usage records with filtering and search
- **Monthly Summary Tab**: Manual entry for monthly billing periods
- **System Status Tab**: Real-time Raspberry Pi monitoring

### Data Management
- **CSV Import**: Automatic import of existing data from spreadsheet files
- **Manual Entry**: Add and edit daily usage records through the web interface
- **Monthly Periods**: Support for billing cycles from 13th to 12th of each month
- **Location Management**: Track usage across multiple locations or services

### Backup System
- **Automated Backups**: Daily scheduled backups with configurable retention
- **Manual Backups**: On-demand backup creation before maintenance
- **Backup Verification**: Integrity checking of backup files
- **Easy Restore**: Simple restoration process from any backup

### System Monitoring
- **Resource Usage**: CPU, memory, and disk utilization monitoring
- **Temperature Monitoring**: Raspberry Pi temperature tracking
- **Database Statistics**: Storage usage and record counts
- **Service Health**: Application status and performance metrics

## Configuration

The application uses environment variables for configuration. Key settings include:

- `FLASK_PORT`: Web server port (default: 5000)
- `DATABASE_PATH`: SQLite database file location
- `BACKUP_RETENTION_DAYS`: Number of days to keep backups (default: 30)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## Security Considerations

- **Network Access**: Configure firewall to restrict access to trusted networks
- **File Permissions**: Database and backup files are protected with appropriate permissions
- **Regular Updates**: Keep system packages and dependencies updated
- **Backup Encryption**: Consider encrypting backups for sensitive deployments

## Maintenance

### Regular Tasks
- **Weekly**: Review system logs and performance metrics
- **Monthly**: Verify backup integrity and clean up old files
- **Quarterly**: Update system packages and application dependencies

### Monitoring
- **Log Files**: Application logs in `/var/log/data-usage-monitor/`
- **Service Status**: Check with `sudo systemctl status data-usage-monitor`
- **Resource Usage**: Monitor through the dashboard System Status tab

## Troubleshooting

### Common Issues
1. **Service won't start**: Check file permissions and Python dependencies
2. **Dashboard not accessible**: Verify firewall settings and service status
3. **Database errors**: Check disk space and file permissions
4. **Backup failures**: Ensure backup directory exists and has write permissions

### Getting Help
- Check the comprehensive DEPLOYMENT_GUIDE.md for detailed troubleshooting
- Review application logs for error messages
- Verify system requirements and dependencies

## Data Import

The application automatically imports data from the provided CSV file during initial setup. The CSV format should have:
- First column: Date (DD-MMM, DD/MM/YYYY, or YYYY-MM-DD format)
- Subsequent columns: Location names with usage values

Monthly summary records are left empty for manual entry as requested, since daily usage totals may differ from actual billing amounts.

## Support

For additional support or advanced configuration options, refer to the comprehensive DEPLOYMENT_GUIDE.md included with this application. The guide covers:
- Detailed installation procedures
- Advanced configuration options
- Performance optimization
- Security hardening
- Backup and recovery procedures
- Troubleshooting guides

## License

This application is provided as-is for personal and educational use. Please ensure compliance with any applicable data protection regulations when handling usage data.

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Compatibility**: Raspberry Pi OS, Ubuntu Server, Debian-based systems

