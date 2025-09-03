#!/bin/bash
# Installation script for Touch Calendar on Raspberry Pi

set -e  # Exit on any error

echo "Touch Calendar Installation Script"
echo "=================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as the pi user (not root)"
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/home/pi/calendar-app"

echo "Installing Touch Calendar..."

# Create installation directory
echo "Creating installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown pi:pi "$INSTALL_DIR"

# Copy files to installation directory
echo "Copying application files..."
cp "$SCRIPT_DIR/calendar_app.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/start_calendar.sh" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/calendar-app.service" "$INSTALL_DIR/"

# Make scripts executable
chmod +x "$INSTALL_DIR/start_calendar.sh"

# Update system packages
echo "Updating system packages..."
sudo apt update

# Install required system packages
echo "Installing required packages..."
sudo apt install -y python3 python3-tk python3-pip xinput unclutter

# Install Python packages (if any additional ones are needed)
echo "Installing Python dependencies..."
# pip3 install --user <any-additional-packages>

# Configure systemd service
echo "Setting up systemd service..."
sudo cp "$INSTALL_DIR/calendar-app.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable calendar-app.service

# Configure auto-login (optional)
echo "Configuring auto-login..."
sudo raspi-config nonint do_boot_behaviour B4  # Desktop autologin

# Configure X11 to start automatically
echo "Configuring X11..."
if ! grep -q "@lxpanel" ~/.config/lxsession/LXDE-pi/autostart 2>/dev/null; then
    mkdir -p ~/.config/lxsession/LXDE-pi/
    cat > ~/.config/lxsession/LXDE-pi/autostart << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@unclutter -idle 10
EOF
fi

# Add calendar app to autostart
if ! grep -q "calendar-app" ~/.config/lxsession/LXDE-pi/autostart; then
    echo "@$INSTALL_DIR/start_calendar.sh" >> ~/.config/lxsession/LXDE-pi/autostart
fi

# Configure touchscreen calibration (if needed)
echo "Setting up touchscreen..."
if [ -f /usr/share/X11/xorg.conf.d/40-libinput.conf ]; then
    if ! grep -q "Option \"CalibrationMatrix\"" /usr/share/X11/xorg.conf.d/40-libinput.conf; then
        echo "Touchscreen calibration may be needed. Run 'xinput_calibrator' if touch input is not accurate."
    fi
fi

# Disable screen blanking globally
echo "Disabling screen blanking..."
sudo bash -c 'cat > /etc/xdg/lxsession/LXDE-pi/autostart << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 10
@'$INSTALL_DIR'/start_calendar.sh
EOF'

echo ""
echo "Installation complete!"
echo "====================="
echo ""
echo "The calendar application has been installed to: $INSTALL_DIR"
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
echo "The application will start automatically on next boot."
echo ""
echo "Reboot now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    sudo reboot
fi
