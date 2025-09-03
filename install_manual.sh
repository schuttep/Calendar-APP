#!/bin/bash
# Manual installation script for when automatic installation fails
# This script provides step-by-step manual installation

echo "Manual Calendar App Installation"
echo "================================"
echo ""

# Get current user info
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)
INSTALL_DIR="$USER_HOME/calendar-app"

echo "Installing for user: $CURRENT_USER"
echo "Home directory: $USER_HOME" 
echo "Install directory: $INSTALL_DIR"
echo ""

# Function to check if command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo "✓ $1 - SUCCESS"
    else
        echo "✗ $1 - FAILED"
        return 1
    fi
}

# Function to prompt user to continue
prompt_continue() {
    read -p "Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation aborted by user"
        exit 1
    fi
}

echo "This script will install the Calendar App manually step by step."
echo "You'll be prompted after each step."
echo ""
prompt_continue

# Step 1: Fix hostname
echo "STEP 1: Fixing hostname resolution"
echo "=================================="
HOSTNAME=$(hostname)
echo "Current hostname: $HOSTNAME"

if grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts 2>/dev/null; then
    echo "✓ Hostname already configured in /etc/hosts"
else
    echo "Adding hostname to /etc/hosts..."
    echo "127.0.1.1    $HOSTNAME" | sudo tee -a /etc/hosts
    check_success "Hostname configuration"
fi
prompt_continue

# Step 2: Create directories
echo "STEP 2: Creating directories"
echo "============================="
sudo mkdir -p "$INSTALL_DIR"
check_success "Directory creation"

sudo chown $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR"
check_success "Directory ownership"
prompt_continue

# Step 3: Copy files
echo "STEP 3: Copying application files"
echo "=================================="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SCRIPT_DIR/calendar_app.py" "$INSTALL_DIR/"
check_success "Copy calendar_app.py"

cp "$SCRIPT_DIR/start_calendar.sh" "$INSTALL_DIR/"
check_success "Copy start_calendar.sh"

# Create service file with correct user
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
check_success "Create service file"

chmod +x "$INSTALL_DIR/start_calendar.sh"
check_success "Make start script executable"
prompt_continue

# Step 4: Test Python
echo "STEP 4: Testing Python environment"
echo "==================================="
python3 --version
check_success "Python3 availability"

python3 -c "import sys; print(f'Python path: {sys.executable}')"
check_success "Python executable check"

python3 -c "import tkinter; print('tkinter imported successfully')"
if [ $? -eq 0 ]; then
    echo "✓ tkinter - SUCCESS"
else
    echo "✗ tkinter - FAILED"
    echo "Installing python3-tk..."
    sudo apt update
    sudo apt install -y python3-tk
    check_success "tkinter installation"
fi
prompt_continue

# Step 5: Test the app
echo "STEP 5: Testing the application"
echo "==============================="
cd "$INSTALL_DIR"

echo "Running basic app test..."
timeout 3 python3 calendar_app.py &
PID=$!
sleep 2
if kill -0 $PID 2>/dev/null; then
    echo "✓ App started successfully"
    kill $PID 2>/dev/null
else
    echo "✗ App failed to start"
    echo "Let's check for errors..."
    python3 calendar_app.py
fi
prompt_continue

# Step 6: Install additional packages
echo "STEP 6: Installing additional packages"
echo "======================================"
echo "This step is optional but recommended"

echo "Installing xinput (for touchscreen)..."
sudo apt install -y xinput
check_success "xinput installation"

echo "Installing unclutter (to hide cursor)..."
sudo apt install -y unclutter
check_success "unclutter installation"

echo "Installing rsync (for file sync)..."
sudo apt install -y rsync
check_success "rsync installation"
prompt_continue

# Step 7: Setup systemd service
echo "STEP 7: Setting up systemd service"
echo "==================================="
echo "This step is optional - you can always run manually"

sudo cp "$INSTALL_DIR/calendar-app.service" /etc/systemd/system/
check_success "Copy service file"

sudo systemctl daemon-reload
check_success "Reload systemd"

sudo systemctl enable calendar-app.service
check_success "Enable service"

echo "Testing service..."
sudo systemctl start calendar-app.service
check_success "Start service"

sleep 3
sudo systemctl status calendar-app.service --no-pager
prompt_continue

# Step 8: Setup autostart (optional)
echo "STEP 8: Setup autostart (optional)"
echo "=================================="
read -p "Do you want to setup autostart? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Detect the correct LXDE config directory
    if [ -d "/etc/xdg/lxsession/LXDE-pi" ]; then
        CONFIG_DIR="$USER_HOME/.config/lxsession/LXDE-pi"
    else
        CONFIG_DIR="$USER_HOME/.config/lxsession/LXDE"
    fi
    
    mkdir -p "$CONFIG_DIR"
    
    if [ ! -f "$CONFIG_DIR/autostart" ]; then
        cat > "$CONFIG_DIR/autostart" << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 10
@$INSTALL_DIR/start_calendar.sh
EOF
    else
        if ! grep -q "calendar-app" "$CONFIG_DIR/autostart"; then
            echo "@$INSTALL_DIR/start_calendar.sh" >> "$CONFIG_DIR/autostart"
        fi
    fi
    check_success "Autostart setup"
fi

# Final summary
echo ""
echo "INSTALLATION COMPLETE!"
echo "====================="
echo ""
echo "Installation location: $INSTALL_DIR"
echo ""
echo "Manual start commands:"
echo "  cd $INSTALL_DIR"
echo "  python3 calendar_app.py              # Direct start"
echo "  ./start_calendar.sh                  # With environment setup"
echo ""
echo "Service commands:"
echo "  sudo systemctl start calendar-app    # Start service"
echo "  sudo systemctl stop calendar-app     # Stop service"
echo "  sudo systemctl status calendar-app   # Check status"
echo ""
echo "Troubleshooting:"
echo "  Check logs: sudo journalctl -u calendar-app.service -f"
echo "  Test Python: python3 -c 'import tkinter'"
echo "  Check display: echo \$DISPLAY"
echo ""

read -p "Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
