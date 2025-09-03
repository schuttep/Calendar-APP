# Remote Development Guide for Raspberry Pi Calendar App

This guide helps you set up remote connectivity between your Windows computer and Raspberry Pi for easy calendar app development and updates.

## Quick Setup

1. **On your Raspberry Pi**, run the remote access setup:
```bash
chmod +x setup_remote_access.sh
./setup_remote_access.sh
```

2. **Follow the prompts** to set passwords and configure services

3. **Note the IP address** displayed at the end

## Connection Methods

### 1. SSH (Command Line Access)

**Windows PowerShell/Command Prompt:**
```cmd
ssh pi@[PI_IP_ADDRESS]
```

**Using PuTTY (Windows):**
- Download PuTTY from https://putty.org
- Host Name: Your Pi's IP address
- Port: 22
- Connection Type: SSH

### 2. VNC (Remote Desktop)

**VNC Viewer (Recommended):**
- Download from https://www.realvnc.com/en/connect/download/viewer/
- Connect to: `[PI_IP_ADDRESS]:5900`
- Use your Pi's username and password

**Built-in Windows:**
- Windows 10/11 has built-in VNC support
- Remote Desktop Connection → `[PI_IP_ADDRESS]:5900`

### 3. File Sharing (SMB/CIFS)

**Windows File Explorer:**
```
\\[PI_IP_ADDRESS]\calendar-app     (Development files)
\\[PI_IP_ADDRESS]\pi-home          (Full home directory)
```

**Map Network Drive:**
1. Open File Explorer
2. Right-click "This PC" → "Map network drive"
3. Drive: Choose a letter (e.g., Z:)
4. Folder: `\\[PI_IP_ADDRESS]\calendar-app`
5. Check "Connect using different credentials"
6. Username: `pi`, Password: (set during setup)

## Development Workflow

### Method 1: Direct File Editing

1. **Map the network drive** to your Windows computer
2. **Edit files directly** using your favorite editor (VS Code, Notepad++, etc.)
3. **Test changes** by SSH'ing to Pi and running:
   ```bash
   /home/pi/sync-from-dev.sh
   ```

### Method 2: Git-Based Development

1. **Initialize Git repository** (done automatically during setup)
2. **Clone to your Windows machine:**
   ```cmd
   git clone pi@[PI_IP_ADDRESS]:/home/pi/calendar-app-dev calendar-app
   ```
3. **Make changes locally** on Windows
4. **Push changes** back to Pi
5. **SSH to Pi** and sync to production

### Method 3: VS Code Remote Development

**Install VS Code Extensions:**
- Remote - SSH
- Remote - SSH: Editing Configuration Files

**Connect to Pi:**
1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type "Remote-SSH: Connect to Host"
4. Enter: `pi@[PI_IP_ADDRESS]`
5. Open folder: `/home/pi/calendar-app-dev`

## File Structure

```
/home/pi/
├── calendar-app/           # Production (running version)
├── calendar-app-dev/       # Development (your workspace)
├── calendar-app-backup/    # Automatic backups
├── sync-from-dev.sh       # Update production from dev
├── sync-to-dev.sh         # Copy production to dev
└── dev-tools.sh           # Development menu
```

## Development Commands

### On Raspberry Pi:

```bash
# Development menu
/home/pi/dev-tools.sh

# Update production from development
/home/pi/sync-from-dev.sh

# Copy production to development  
/home/pi/sync-to-dev.sh

# Test app without affecting production
cd /home/pi/calendar-app-dev
python3 calendar_app.py

# View production logs
sudo journalctl -u calendar-app.service -f

# Service control
sudo systemctl restart calendar-app.service
sudo systemctl stop calendar-app.service
sudo systemctl start calendar-app.service
```

## Common Development Tasks

### 1. Making Code Changes

**Option A: Direct Network Edit**
1. Open `\\[PI_IP_ADDRESS]\calendar-app\calendar_app.py` in your editor
2. Make changes and save
3. SSH to Pi: `/home/pi/sync-from-dev.sh`

**Option B: VS Code Remote**
1. Connect via Remote-SSH
2. Edit `/home/pi/calendar-app-dev/calendar_app.py`
3. Use terminal in VS Code: `./sync-from-dev.sh`

### 2. Testing Changes

```bash
# SSH to Pi
ssh pi@[PI_IP_ADDRESS]

# Test in development mode (windowed)
cd /home/pi/calendar-app-dev
python3 calendar_app.py

# Update production and restart service
/home/pi/sync-from-dev.sh
```

### 3. Debugging Issues

```bash
# View real-time logs
sudo journalctl -u calendar-app.service -f

# Check service status
sudo systemctl status calendar-app.service

# Run with debug output
cd /home/pi/calendar-app-dev
python3 -u calendar_app.py
```

### 4. Backup and Restore

```bash
# Backups are automatic, but manual backup:
cp -r /home/pi/calendar-app /home/pi/calendar-app-backup/manual-$(date +%Y%m%d_%H%M%S)

# Restore from backup:
sudo systemctl stop calendar-app.service
cp -r /home/pi/calendar-app-backup/backup-YYYYMMDD_HHMMSS /home/pi/calendar-app
sudo systemctl start calendar-app.service
```

## Security Considerations

### SSH Security
```bash
# Change default SSH port (optional)
sudo nano /etc/ssh/sshd_config
# Change: Port 2222
sudo systemctl restart ssh

# Use key-based authentication (recommended)
ssh-keygen -t rsa -b 4096
ssh-copy-id pi@[PI_IP_ADDRESS]
```

### Firewall Setup
```bash
# Install UFW firewall
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow VNC
sudo ufw allow 5900/tcp

# Allow Samba
sudo ufw allow 445/tcp
sudo ufw allow 139/tcp

# Enable firewall
sudo ufw enable
```

## Troubleshooting

### Connection Issues

**SSH Connection Refused:**
```bash
# On Pi:
sudo systemctl status ssh
sudo systemctl start ssh
```

**VNC Not Working:**
```bash
# On Pi:
sudo raspi-config
# Navigate to: Interface Options → VNC → Enable
```

**File Sharing Issues:**
```bash
# On Pi:
sudo systemctl status smbd
sudo testparm  # Test Samba configuration
```

### Development Issues

**Sync Script Fails:**
```bash
# Check permissions
ls -la /home/pi/sync-from-dev.sh
chmod +x /home/pi/sync-from-dev.sh
```

**Service Won't Start:**
```bash
# Check logs
sudo journalctl -u calendar-app.service --no-pager

# Test manually
cd /home/pi/calendar-app
python3 calendar_app.py
```

## Windows Tools Recommendations

### Editors
- **VS Code** (with Remote-SSH extension) - Best option
- **Notepad++** - Lightweight
- **Sublime Text** - Fast and powerful

### SSH Clients  
- **Built-in Windows SSH** - Available in PowerShell
- **PuTTY** - Classic choice
- **Windows Terminal** - Modern terminal

### File Transfer
- **WinSCP** - GUI SFTP client
- **FileZilla** - FTP/SFTP client
- **Built-in Windows SMB** - File Explorer

This setup gives you multiple ways to connect and develop remotely, making it easy to update your calendar app from your Windows computer!
