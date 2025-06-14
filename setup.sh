#!/bin/bash
# Data Usage Monitor - Quick Setup and Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/data-usage-monitor"
SERVICE_NAME="data-usage-monitor"
USER="pi"  # Default Raspberry Pi user

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Data Usage Monitor Setup${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_requirements() {
    print_info "Checking system requirements..."
    
    # Check if running on Raspberry Pi
    if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        print_success "Running on Raspberry Pi"
    else
        print_warning "Not running on Raspberry Pi - some features may not work"
    fi
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_error "pip3 not found"
        exit 1
    fi
    
    # Check systemctl
    if command -v systemctl &> /dev/null; then
        print_success "systemctl found"
    else
        print_warning "systemctl not found - service management may not work"
    fi
}

install_dependencies() {
    print_info "Installing system dependencies..."
    
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv sqlite3 cron
    
    print_success "System dependencies installed"
}

setup_application() {
    print_info "Setting up application..."
    
    # Create application directory
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    
    # Copy application files
    cp -r . $APP_DIR/
    
    # Set up Python virtual environment
    cd $APP_DIR
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install flask flask-cors psutil
    
    # Make scripts executable
    chmod +x backup_manager.py
    chmod +x database.py
    
    print_success "Application setup completed"
}

setup_database() {
    print_info "Setting up database..."
    
    cd $APP_DIR
    source venv/bin/activate
    
    # Initialize database
    python3 database.py
    
    print_success "Database initialized"
}

create_systemd_service() {
    print_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Data Usage Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/data-usage-api/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Systemd service created and enabled"
}

setup_backup_cron() {
    print_info "Setting up automatic backups..."
    
    cd $APP_DIR
    
    # Setup daily backup at 2 AM
    python3 backup_manager.py --setup-cron daily
    
    print_success "Daily backup scheduled at 2 AM"
}

start_service() {
    print_info "Starting service..."
    
    sudo systemctl start $SERVICE_NAME
    
    # Wait a moment for service to start
    sleep 3
    
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Service started successfully"
        print_info "Dashboard available at: http://$(hostname -I | awk '{print $1}'):5000"
    else
        print_error "Failed to start service"
        print_info "Check logs with: sudo journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

show_status() {
    print_info "Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager
    
    echo
    print_info "Recent logs:"
    sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
}

backup_database() {
    print_info "Creating database backup..."
    
    cd $APP_DIR
    python3 backup_manager.py --backup
    
    print_success "Backup completed"
}

restore_database() {
    if [ -z "$1" ]; then
        print_error "Please specify backup filename"
        print_info "Available backups:"
        cd $APP_DIR
        python3 backup_manager.py --list
        exit 1
    fi
    
    print_warning "This will replace the current database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd $APP_DIR
        python3 backup_manager.py --restore "$1" --confirm
        print_success "Database restored"
        
        # Restart service
        sudo systemctl restart $SERVICE_NAME
        print_success "Service restarted"
    else
        print_info "Restore cancelled"
    fi
}

show_help() {
    echo "Data Usage Monitor Management Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  install     - Full installation and setup"
    echo "  start       - Start the service"
    echo "  stop        - Stop the service"
    echo "  restart     - Restart the service"
    echo "  status      - Show service status"
    echo "  logs        - Show recent logs"
    echo "  backup      - Create database backup"
    echo "  restore     - Restore database from backup"
    echo "  update      - Update application"
    echo "  uninstall   - Remove application and service"
    echo "  help        - Show this help"
    echo
}

case "${1:-help}" in
    install)
        print_header
        check_requirements
        install_dependencies
        setup_application
        setup_database
        create_systemd_service
        setup_backup_cron
        start_service
        print_success "Installation completed successfully!"
        print_info "Dashboard available at: http://$(hostname -I | awk '{print $1}'):5000"
        ;;
    
    start)
        sudo systemctl start $SERVICE_NAME
        print_success "Service started"
        ;;
    
    stop)
        sudo systemctl stop $SERVICE_NAME
        print_success "Service stopped"
        ;;
    
    restart)
        sudo systemctl restart $SERVICE_NAME
        print_success "Service restarted"
        ;;
    
    status)
        show_status
        ;;
    
    logs)
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    
    backup)
        backup_database
        ;;
    
    restore)
        restore_database "$2"
        ;;
    
    update)
        print_info "Stopping service..."
        sudo systemctl stop $SERVICE_NAME
        
        print_info "Updating application..."
        setup_application
        
        print_info "Starting service..."
        sudo systemctl start $SERVICE_NAME
        
        print_success "Update completed"
        ;;
    
    uninstall)
        print_warning "This will remove the application and all data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
            sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
            sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
            sudo systemctl daemon-reload
            sudo rm -rf $APP_DIR
            
            # Remove cron job
            cd $APP_DIR 2>/dev/null && python3 backup_manager.py --remove-cron || true
            
            print_success "Application uninstalled"
        else
            print_info "Uninstall cancelled"
        fi
        ;;
    
    help|*)
        show_help
        ;;
esac

