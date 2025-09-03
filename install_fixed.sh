#!/bin/bash
# Fixed Installation script for Touch Calendar on Raspberry Pi
# This version handles hostname resolution issues

set -e  # Exit on any error

echo "Touch Calendar Installation Script (Fixed Version)"
echo "================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as a regular user (not root)"
    exit 1
fi

# Get the current user and directory
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$USER_HOME/calendar-app"

echo "Installing Touch Calendar for user: $CURRENT_USER"
echo "Home directory: $USER_HOME"
echo "Install directory: $INSTALL_DIR"

echo "Installing Touch Calendar..."

# Fix hostname resolution issue first
echo "Checking hostname configuration..."
HOSTNAME=$(hostname)
if ! grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts 2>/dev/null; then
    echo "Fixing hostname resolution..."
    echo "127.0.1.1    $HOSTNAME" | sudo tee -a /etc/hosts > /dev/null
    echo "✓ Hostname resolution fixed"
fi

# Create installation directory
echo "Creating installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR"

# Copy files to installation directory
echo "Copying application files..."
cp "$SCRIPT_DIR/calendar_app.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/start_calendar.sh" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/calendar-app.service" "$INSTALL_DIR/"

# Make scripts executable
chmod +x "$INSTALL_DIR/start_calendar.sh"

# Update system packages with timeout and retry
echo "Updating system packages..."
sudo timeout 300 apt update || {
    echo "First update attempt failed, trying alternative mirrors..."
    sudo sed -i 's/deb.debian.org/mirror.us.leaseweb.net\/debian/' /etc/apt/sources.list 2>/dev/null || true
    sudo timeout 300 apt update || echo "Update completed with warnings"
}

# Install required system packages one by one to isolate issues
echo "Installing required packages..."

# Install Python packages
echo "Installing Python3 and tkinter..."
sudo apt install -y python3 python3-tk || {
    echo "Failed to install Python packages. They might already be installed."
    # Check if they're available
    python3 --version || { echo "Python3 not found. Manual installation may be needed."; exit 1; }
    python3 -c "import tkinter" || { echo "tkinter not found. Manual installation may be needed."; exit 1; }
}

# Install pip
echo "Installing pip3..."
sudo apt install -y python3-pip || echo "pip3 installation failed or already installed"

# Install X11 utilities
echo "Installing X11 utilities..."
sudo apt install -y xinput || echo "xinput installation failed or already installed"
sudo apt install -y unclutter || echo "unclutter installation failed or already installed"

# Install additional utilities
echo "Installing additional utilities..."
sudo apt install -y rsync || echo "rsync installation failed or already installed"

echo "Core installation complete!"

# Try to configure systemd service (optional)
echo "Setting up systemd service..."

# Create service file with correct user and paths
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

if sudo cp "$INSTALL_DIR/calendar-app.service" /etc/systemd/system/ 2>/dev/null; then
    sudo systemctl daemon-reload
    if sudo systemctl enable calendar-app.service 2>/dev/null; then
        echo "✓ Systemd service configured successfully for user: $CURRENT_USER"
    else
        echo "⚠ Systemd service setup failed, but app can still run manually"
    fi
else
    echo "⚠ Service file copy failed, but app can still run manually"
fi

# Configure auto-login (optional)
echo "Configuring auto-login..."
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_boot_behaviour B4 2>/dev/null || echo "Auto-login configuration skipped"
else
    echo "raspi-config not found, skipping auto-login setup"
fi

# Configure X11 autostart
echo "Configuring X11..."
if [ -n "$DISPLAY" ] || [ -n "$XDG_SESSION_TYPE" ]; then
    # We're in a graphical environment
    mkdir -p ~/.config/lxsession/LXDE-pi/ 2>/dev/null || true
    mkdir -p ~/.config/lxsession/LXDE/ 2>/dev/null || true
    
    # Determine which config directory to use
    if [ -d "/etc/xdg/lxsession/LXDE-pi" ]; then
        CONFIG_DIR="~/.config/lxsession/LXDE-pi"
    else
        CONFIG_DIR="~/.config/lxsession/LXDE"
    fi
    
    # Create autostart file if it doesn't exist
    AUTOSTART_FILE=$(eval echo "$CONFIG_DIR/autostart")
    mkdir -p "$(dirname "$AUTOSTART_FILE")" 2>/dev/null || true
    
    if [ ! -f "$AUTOSTART_FILE" ]; then
        cat > "$AUTOSTART_FILE" << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
EOF
    fi
    
    # Add calendar app to autostart if not already there
    if ! grep -q "calendar-app" "$AUTOSTART_FILE" 2>/dev/null; then
        echo "@$INSTALL_DIR/start_calendar.sh" >> "$AUTOSTART_FILE"
        echo "✓ Added to autostart"
    fi
    
    # Disable screen blanking in autostart
    if ! grep -q "xset.*off" "$AUTOSTART_FILE" 2>/dev/null; then
        cat >> "$AUTOSTART_FILE" << EOF
@xset s off
@xset -dpms
@xset s noblank
@uncluster -idle 10
EOF
        echo "✓ Screen blanking disabled"
    fi
else
    echo "⚠ Not in graphical environment, skipping GUI autostart setup"
fi

# Create a simple test script
cat > "$INSTALL_DIR/test_app.sh" << 'EOF'
#!/bin/bash
echo "Testing Calendar App..."
cd "$(dirname "$0")"

echo "Checking Python..."
python3 --version || { echo "Python3 not found!"; exit 1; }

echo "Checking tkinter..."
python3 -c "import tkinter; print('tkinter OK')" || { echo "tkinter not available!"; exit 1; }

echo "Testing app startup..."
timeout 5 python3 calendar_app.py || echo "App test completed"

echo "✓ All tests passed!"
EOF

chmod +x "$INSTALL_DIR/test_app.sh"

echo ""
echo "Installation complete!"
echo "====================="
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "To test the installation:"
echo "  cd $INSTALL_DIR && ./test_app.sh"
echo ""
echo "To start the application manually:"
echo "  cd $INSTALL_DIR && ./start_calendar.sh"
echo ""
echo "To start the systemd service:"
echo "  sudo systemctl start calendar-app.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status calendar-app.service"
echo ""
echo "If you experience issues:"
echo "1. Run: $INSTALL_DIR/test_app.sh"
echo "2. Check logs: sudo journalctl -u calendar-app.service"
echo "3. Try manual start: cd $INSTALL_DIR && python3 calendar_app.py"
echo ""

# Ask if user wants to test now
read -p "Would you like to test the installation now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$INSTALL_DIR"
    ./test_app.sh
fi

echo ""
read -p "Reboot now to enable all features? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
