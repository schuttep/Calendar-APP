#!/bin/bash
# Calendar App Startup Script for Raspberry Pi
# This script sets up the environment and starts the calendar app in kiosk mode

# Set the display (for cases where DISPLAY isn't set)
export DISPLAY=:0

# Navigate to the calendar app directory
cd "$(dirname "$0")"

# Disable screen blanking and screensaver
xset s off
xset -dpms
xset s noblank

# Hide cursor after inactivity (optional)
# unclutter -idle 10 &

# Set up X server settings for touchscreen
xinput --set-prop "pointer:FT5406 memory based driver" "Coordinate Transformation Matrix" 1 0 0 0 1 0 0 0 1 2>/dev/null || true

# Try to start virtual keyboard in background (for touchscreen)
onboard --layout Small &
ONBOARD_PID=$!

# Give onboard a moment to start
sleep 1

# Start the calendar application
python3 calendar_app.py

# Clean up: kill onboard when calendar app exits
kill $ONBOARD_PID 2>/dev/null || true

# If the app exits, restart it (optional - remove if you don't want auto-restart)
# while true; do
#     python3 calendar_app.py
#     sleep 2
# done
