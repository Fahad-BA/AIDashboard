#!/bin/bash
# Simple monitor for AIDashboard

DASHBOARD_PID=$!
WORKDIR="/home/fahad/AIDB"
APP_FILE="$WORKDIR/app.py"
PYTHON_CMD="$WORKDIR/venv/bin/python"
LOG_FILE="$WORKDIR/dashboard_monitor.log"

echo "$(date): Starting AIDashboard monitor" >> "$LOG_FILE"

while true; do
    # Check if dashboard is still running
    if ! ps -p $DASHBOARD_PID > /dev/null 2>&1; then
        echo "$(date): AIDashboard died, restarting..." >> "$LOG_FILE"
        cd "$WORKDIR"
        nohup "$PYTHON_CMD" "$APP_FILE" > /dev/null 2>&1 &
        DASHBOARD_PID=$!
        echo "$(date): Restarted AIDashboard with PID $DASHBOARD_PID" >> "$LOG_FILE"
    fi
    
    # Sleep for 10 seconds before checking again
    sleep 10
done