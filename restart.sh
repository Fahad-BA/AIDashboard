#!/bin/bash

# Script to restart the aidashboard service
# Created by: Fahad
# Date: 2026-02-17

# Function to print messages with color
print_message() {
    local color=$1
    local message=$2
    
    case $color in
        "green")
            echo -e "\e[32m$message\e[0m"
            ;;
        "yellow")
            echo -e "\e[33m$message\e[0m"
            ;;
        "red")
            echo -e "\e[31m$message\e[0m"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Check if user has sudo privileges
if ! sudo -n true 2>/dev/null; then
    print_message "yellow" "This script requires sudo privileges to restart the service."
fi

# Start the restart process
print_message "yellow" "Restarting aidashboard service..."

# Restart the aidashboard service
if sudo systemctl restart aidashboard; then
    # Check if the service is running
    if sudo systemctl is-active --quiet aidashboard; then
        print_message "green" "✓ Service restarted successfully!"
        print_message "green" "✓ Aidashboard service is now running."
        
        # Show service status
        echo ""
        print_message "yellow" "Service Status:"
        sudo systemctl status aidashboard --no-pager -l
    else
        print_message "red" "✗ Service failed to start properly."
        print_message "red" "Please check the service logs with: journalctl -u aidashboard"
        exit 1
    fi
else
    print_message "red" "✗ Failed to restart aidashboard service."
    print_message "red" "Please check if the service exists and try again."
    exit 1
fi

exit 0