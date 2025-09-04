#!/bin/bash
# Simple, foolproof installation script for Calendar App
# This version is designed to work with any username

set -e  # Exit on error

echo "Simple Calendar App Installation"
echo "==============================="

# Get user information
CURRENT_USER=$(whoami)
USER_HOME="$HOME"
INSTALL_DIR="$USER_HOME/calendar-app"

echo "Installing for:"
echo "  User: $CURRENT_USER"
echo "  Home: $USER_HOME"
echo "  Install directory: $INSTALL_DIR"
echo ""

# Fix hostname first
echo "Step 1: Fixing hostname resolution..."
HOSTNAME=$(hostname)
if ! grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts 2>/dev/null; then
    echo "127.0.1.1    $HOSTNAME" | sudo tee -a /etc/hosts > /dev/null
    echo "✓ Fixed hostname resolution"
else
    echo "✓ Hostname already configured"
fi

# Create directory
echo ""
echo "Step 2: Creating installation directory..."
mkdir -p "$INSTALL_DIR"
echo "✓ Directory created: $INSTALL_DIR"

# Copy files
echo ""
echo "Step 3: Copying application files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/calendar_app.py" ]; then
    cp "$SCRIPT_DIR/calendar_app.py" "$INSTALL_DIR/"
    echo "✓ Copied calendar_app.py"
else
    echo "✗ calendar_app.py not found in $SCRIPT_DIR"
    exit 1
fi

if [ -f "$SCRIPT_DIR/start_calendar.sh" ]; then
    cp "$SCRIPT_DIR/start_calendar.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/start_calendar.sh"
    echo "✓ Copied start_calendar.sh"
else
    echo "✗ start_calendar.sh not found"
    exit 1
fi

if [ -f "$SCRIPT_DIR/classes.txt" ]; then
    cp "$SCRIPT_DIR/classes.txt" "$INSTALL_DIR/"
    echo "✓ Copied classes.txt"
else
    echo "⚠ classes.txt not found - will create empty file"
    touch "$INSTALL_DIR/classes.txt"
fi

# Copy any ICS files for calendar import
for ics_file in "$SCRIPT_DIR"/*.ics; do
    if [ -f "$ics_file" ]; then
        cp "$ics_file" "$INSTALL_DIR/"
        echo "✓ Copied $(basename "$ics_file")"
    fi
done

# Create a simple service file
echo ""
echo "Step 4: Creating service file..."
cat > "$INSTALL_DIR/calendar-app.service" << EOF
[Unit]
Description=Touch Calendar Application
After=graphical-session.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment=DISPLAY=:0
ExecStartPre=/bin/sleep 10
ExecStart=$INSTALL_DIR/start_calendar.sh
Restart=always
RestartSec=3

[Install]
WantedBy=graphical-session.target
EOF
echo "✓ Service file created"

# Install Python packages
echo ""
echo "Step 5: Installing required packages..."
sudo apt update -qq || echo "Package update had warnings (continuing...)"

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Installing python3-tk..."
    sudo apt install -y python3-tk
    echo "✓ Installed python3-tk"
else
    echo "✓ python3-tk already available"
fi

# Test the app
echo ""
echo "Step 6: Testing the application..."
cd "$INSTALL_DIR"
timeout 3 python3 calendar_app.py &
APP_PID=$!
sleep 2

if kill -0 $APP_PID 2>/dev/null; then
    kill $APP_PID 2>/dev/null || true
    echo "✓ Application test successful!"
else
    echo "Testing application startup..."
    if python3 -c "import tkinter; print('tkinter OK')"; then
        echo "✓ Python environment is working"
    else
        echo "✗ Python environment issue"
        exit 1
    fi
fi

# Optional: Install service
echo ""
read -p "Install as system service? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo cp "$INSTALL_DIR/calendar-app.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable calendar-app.service
    echo "✓ Service installed and enabled"
    
    # Test service
    echo "Testing service..."
    sudo systemctl start calendar-app.service
    sleep 3
    if sudo systemctl is-active --quiet calendar-app.service; then
        echo "✓ Service is running successfully!"
        sudo systemctl stop calendar-app.service
        echo "Service stopped (will start on reboot)"
    else
        echo "⚠ Service had issues - check with: sudo journalctl -u calendar-app.service"
    fi
else
    echo "Skipped service installation"
fi

# Create simple start script
echo ""
echo "Step 7: Creating convenience scripts..."
cat > "$USER_HOME/start-calendar.sh" << EOF
#!/bin/bash
# Quick start script for calendar app
echo "Starting Calendar App..."
cd "$INSTALL_DIR"
python3 calendar_app.py
EOF
chmod +x "$USER_HOME/start-calendar.sh"
echo "✓ Created ~/start-calendar.sh"

echo ""
echo "INSTALLATION COMPLETE!"
echo "====================="
echo ""
echo "Your calendar app is installed in: $INSTALL_DIR"
echo ""
echo "To start the app:"
echo "  Method 1: ~/start-calendar.sh"
echo "  Method 2: cd $INSTALL_DIR && python3 calendar_app.py"
echo "  Method 3: cd $INSTALL_DIR && ./start_calendar.sh"
if [[ $REPLY =~ ^[Yy]$ ]]; then
echo "  Method 4: sudo systemctl start calendar-app.service"
fi
echo ""
echo "Files installed:"
echo "  Main app: $INSTALL_DIR/calendar_app.py"
echo "  Starter: $INSTALL_DIR/start_calendar.sh"
echo "  Quick start: $USER_HOME/start-calendar.sh"
if [[ $REPLY =~ ^[Yy]$ ]]; then
echo "  Service: /etc/systemd/system/calendar-app.service"
fi
echo ""

# Ask to test now
read -p "Test the app now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting calendar app..."
    cd "$INSTALL_DIR"
    python3 calendar_app.py
fi
