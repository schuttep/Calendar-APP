#!/bin/bash
# Remote Access Setup Script for Raspberry Pi Calendar App
# This script enables SSH, VNC, and sets up file sharing for easy remote updates

# Get current user information
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)
INSTALL_DIR="$USER_HOME/calendar-app"

echo "Setting up remote access for Calendar App development..."
echo "User: $CURRENT_USER"
echo "Home: $USER_HOME"
echo "======================================================"

# Enable SSH
echo "Enabling SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

# Enable VNC (for remote desktop access)
echo "Enabling VNC..."
sudo raspi-config nonint do_vnc 0

# Install and configure Samba for file sharing
echo "Installing Samba for file sharing..."
sudo apt update
sudo apt install -y samba samba-common-bin

# Create Samba configuration for calendar app directory
echo "Configuring Samba share..."
sudo tee -a /etc/samba/smb.conf > /dev/null << EOF

[calendar-app]
    comment = Calendar App Development Share
    path = $INSTALL_DIR
    browseable = yes
    read only = no
    only guest = no
    create mask = 0777
    directory mask = 0777
    public = no
    writable = yes
    valid users = $CURRENT_USER

[${CURRENT_USER}-home]
    comment = User Home Directory
    path = $USER_HOME
    browseable = yes
    read only = no
    only guest = no
    create mask = 0755
    directory mask = 0755
    public = no
    writable = yes
    valid users = $CURRENT_USER
EOF

# Set Samba password for current user
echo "Setting up Samba password for user '$CURRENT_USER'..."
echo "You'll be prompted to set a password for remote file access:"
sudo smbpasswd -a $CURRENT_USER

# Restart Samba
sudo systemctl restart smbd
sudo systemctl enable smbd

# Install rsync for efficient file synchronization
echo "Installing rsync..."
sudo apt install -y rsync

# Create development directory structure
echo "Setting up development directories..."
mkdir -p "$USER_HOME/calendar-app-dev"
mkdir -p "$USER_HOME/calendar-app-backup"

# Create sync script for easy updates
cat > "$USER_HOME/sync-from-dev.sh" << EOF
#!/bin/bash
# Sync script to update production calendar app from development version

echo "Syncing calendar app from development to production..."

# Stop the calendar service
sudo systemctl stop calendar-app.service

# Backup current production version
cp -r $INSTALL_DIR $USER_HOME/calendar-app-backup/backup-\$(date +%Y%m%d_%H%M%S)

# Sync files from development to production
rsync -av --exclude='*.json' --exclude='__pycache__' $USER_HOME/calendar-app-dev/ $INSTALL_DIR/

# Set correct permissions
chmod +x $INSTALL_DIR/start_calendar.sh

# Start the calendar service
sudo systemctl start calendar-app.service

echo "Sync complete! Calendar app updated."
echo "Check status with: sudo systemctl status calendar-app.service"
EOF

chmod +x "$USER_HOME/sync-from-dev.sh"

# Create reverse sync script (production to dev)
cat > "$USER_HOME/sync-to-dev.sh" << EOF
#!/bin/bash
# Sync script to copy production calendar app to development version

echo "Syncing calendar app from production to development..."

# Sync files from production to development
rsync -av $INSTALL_DIR/ $USER_HOME/calendar-app-dev/

echo "Sync complete! Development version updated with production files."
EOF

chmod +x "$USER_HOME/sync-to-dev.sh"

# Install Git for version control (optional)
echo "Installing Git..."
sudo apt install -y git

# Set up Git repository (optional)
cd "$USER_HOME/calendar-app-dev"
if [ ! -d ".git" ]; then
    git init
    git config user.name "$CURRENT_USER"
    git config user.email "$CURRENT_USER@raspberry.local"
    
    # Create initial commit
    git add .
    git commit -m "Initial calendar app commit"
    echo "Git repository initialized in $USER_HOME/calendar-app-dev"
fi

# Create remote development tools
cat > "$USER_HOME/dev-tools.sh" << EOF
#!/bin/bash
# Development tools menu

echo "Calendar App Development Tools"
echo "============================="
echo "1. Start calendar app in development mode"
echo "2. Sync dev to production"
echo "3. Sync production to dev"
echo "4. View production logs"
echo "5. Restart production service"
echo "6. Stop production service"
echo "7. Edit main app file"
echo "8. Git status"
echo "9. Exit"
echo ""
read -p "Select option (1-9): " choice

case $choice in
    1)
        echo "Starting calendar app in development mode..."
        cd $USER_HOME/calendar-app-dev
        python3 calendar_app.py
        ;;
    2)
        echo "Syncing development to production..."
        $USER_HOME/sync-from-dev.sh
        ;;
    3)
        echo "Syncing production to development..."
        $USER_HOME/sync-to-dev.sh
        ;;
    4)
        echo "Viewing production service logs..."
        sudo journalctl -u calendar-app.service -f
        ;;
    5)
        echo "Restarting production service..."
        sudo systemctl restart calendar-app.service
        sudo systemctl status calendar-app.service
        ;;
    6)
        echo "Stopping production service..."
        sudo systemctl stop calendar-app.service
        ;;
    7)
        echo "Opening main app file in nano..."
        nano $USER_HOME/calendar-app-dev/calendar_app.py
        ;;
    8)
        echo "Git status:"
        cd $USER_HOME/calendar-app-dev
        git status
        ;;
    9)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid option"
        ;;
esac
EOF

chmod +x "$USER_HOME/dev-tools.sh"

# Get network information
echo ""
echo "Network Information:"
echo "==================="
echo "IP Address: $(hostname -I | awk '{print $1}')"
echo "Hostname: $(hostname)"
echo ""

# Display connection information
echo "Remote Access Setup Complete!"
echo "============================="
echo ""
echo "SSH Access:"
echo "  ssh $CURRENT_USER@$(hostname -I | awk '{print $1}')"
echo "  (Use your user password)"
echo ""
echo "VNC Access:"
echo "  Connect to: $(hostname -I | awk '{print $1}'):5900"
echo "  (Use your user password)"
echo ""
echo "File Sharing (Windows):"
echo "  \\\\$(hostname -I | awk '{print $1}')\\calendar-app"
echo "  \\\\$(hostname -I | awk '{print $1}')\\${CURRENT_USER}-home"
echo "  (Use username: $CURRENT_USER, password: set above)"
echo ""
echo "Development Commands:"
echo "  $USER_HOME/dev-tools.sh  - Development menu"
echo "  $USER_HOME/sync-from-dev.sh - Update production from dev"
echo "  $USER_HOME/sync-to-dev.sh - Copy production to dev"
echo ""
echo "Directories:"
echo "  Production: $INSTALL_DIR"
echo "  Development: $USER_HOME/calendar-app-dev"
echo "  Backups: $USER_HOME/calendar-app-backup"
echo ""

# Copy current production to development
if [ -d "$INSTALL_DIR" ]; then
    echo "Copying current production version to development directory..."
    $USER_HOME/sync-to-dev.sh
fi

echo "Setup complete! You can now connect remotely to develop and update your calendar app."
