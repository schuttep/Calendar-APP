# Troubleshooting Guide for Raspberry Pi Calendar App

This guide helps resolve common installation and runtime issues.

## Hostname Resolution Error

**Error Message:**
```
sudo: unable to resolve host [hostname]: Name or service not known
```

**Quick Fix:**
```bash
# Check current hostname
hostname

# Add hostname to /etc/hosts (replace 'raspberrypi' with your actual hostname)
echo "127.0.1.1    $(hostname)" | sudo tee -a /etc/hosts

# Verify the fix
sudo apt update
```

**Alternative Solutions:**

### Method 1: Use the Fixed Installer
```bash
chmod +x install_fixed.sh
./install_fixed.sh
```

### Method 2: Manual Step-by-Step Installation
```bash
chmod +x install_manual.sh
./install_manual.sh
```

### Method 3: Set a Permanent Hostname
```bash
# Set hostname permanently
sudo hostnamectl set-hostname raspberrypi

# Update /etc/hosts
sudo nano /etc/hosts
# Add this line:
# 127.0.1.1    raspberrypi

# Reboot
sudo reboot
```

## Common Installation Issues

### 1. Network/Repository Issues

**Problem:** Package installation fails or times out

**Solutions:**
```bash
# Update package lists with timeout
sudo timeout 300 apt update

# If that fails, try different mirror
sudo sed -i 's/deb.debian.org/mirror.us.leaseweb.net\/debian/' /etc/apt/sources.list
sudo apt update

# Or use local mirror
sudo sed -i 's/deb.debian.org/ftp.us.debian.org/' /etc/apt/sources.list
sudo apt update
```

### 2. Python/Tkinter Issues

**Problem:** `ModuleNotFoundError: No module named 'tkinter'`

**Solutions:**
```bash
# Install tkinter
sudo apt install python3-tk

# Verify installation
python3 -c "import tkinter; print('tkinter OK')"

# Alternative: Install from different source
sudo apt install python3-tkinter
```

### 3. Permission Issues

**Problem:** Permission denied errors

**Solutions:**
```bash
# Fix ownership of calendar directory
sudo chown -R pi:pi /home/pi/calendar-app

# Make scripts executable
chmod +x /home/pi/calendar-app/start_calendar.sh

# Fix service file permissions
sudo chmod 644 /etc/systemd/system/calendar-app.service
```

### 4. Service Start Issues

**Problem:** systemctl service fails to start

**Diagnosis:**
```bash
# Check service status
sudo systemctl status calendar-app.service

# View detailed logs
sudo journalctl -u calendar-app.service -f

# Test manual start
cd /home/pi/calendar-app
python3 calendar_app.py
```

**Common fixes:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Fix service file path
sudo cp /home/pi/calendar-app/calendar-app.service /etc/systemd/system/

# Enable service
sudo systemctl enable calendar-app.service
```

## Alternative Installation Methods

### Minimal Installation (No Service)

If full installation fails, install just the app:

```bash
# Create directory
mkdir -p /home/pi/calendar-app
cd /home/pi/calendar-app

# Copy files (assuming they're in current directory)
cp calendar_app.py /home/pi/calendar-app/
chmod +x /home/pi/calendar-app/calendar_app.py

# Install only essential packages
sudo apt update
sudo apt install python3 python3-tk

# Test the app
python3 calendar_app.py
```

### Manual Dependencies Installation

```bash
# Essential packages only
sudo apt install python3 python3-tk

# Recommended packages
sudo apt install xinput unclutter rsync

# Development packages (optional)
sudo apt install git nano vim htop
```

## Runtime Troubleshooting

### Display Issues

**Problem:** App won't start in GUI mode

**Solutions:**
```bash
# Check display environment
echo $DISPLAY
# Should show :0 or :0.0

# Set display if not set
export DISPLAY=:0

# Test X11 access
xhost
```

### Touchscreen Issues

**Problem:** Touch input not working

**Solutions:**
```bash
# List input devices
xinput list

# Test touch events
sudo apt install evtest
sudo evtest

# Calibrate touchscreen
sudo apt install xinput-calibrator
xinput_calibrator
```

### Performance Issues

**Problem:** App runs slowly

**Solutions:**
```bash
# Check system resources
htop

# Increase GPU memory
sudo raspi-config
# Advanced Options -> Memory Split -> 128

# Check SD card speed
sudo hdparm -t /dev/mmcblk0
```

## Recovery Procedures

### Reset Configuration

```bash
# Remove config files
rm /home/pi/calendar-app/calendar_config.json
rm /home/pi/calendar-app/calendar_events.json
rm /home/pi/calendar-app/calendar_tasks.json

# Restart app
cd /home/pi/calendar-app
python3 calendar_app.py
```

### Complete Reinstallation

```bash
# Stop service
sudo systemctl stop calendar-app.service
sudo systemctl disable calendar-app.service

# Remove files
sudo rm -rf /home/pi/calendar-app
sudo rm /etc/systemd/system/calendar-app.service

# Reload systemd
sudo systemctl daemon-reload

# Start fresh installation
./install_fixed.sh
```

### Backup and Restore Data

**Backup:**
```bash
# Create backup
tar -czf calendar-backup.tar.gz /home/pi/calendar-app/*.json

# Or copy to USB
cp /home/pi/calendar-app/*.json /media/pi/USB_DRIVE/
```

**Restore:**
```bash
# From tar backup
tar -xzf calendar-backup.tar.gz -C /

# From USB
cp /media/pi/USB_DRIVE/*.json /home/pi/calendar-app/
```

## Getting Help

### Collect System Information

```bash
# System info
uname -a
cat /etc/os-release

# Hardware info
cat /proc/cpuinfo | grep Model
cat /proc/meminfo | grep MemTotal

# Python info
python3 --version
python3 -c "import sys; print(sys.path)"

# Display info
echo $DISPLAY
xrandr 2>/dev/null || echo "xrandr not available"

# Service status
sudo systemctl status calendar-app.service --no-pager
```

### Log Files to Check

```bash
# System logs
sudo journalctl -u calendar-app.service --no-pager

# X11 logs
cat /var/log/Xorg.0.log | grep -i error

# Application logs (if any)
ls -la /home/pi/calendar-app/*.log
```

### Common Log Messages and Solutions

**"ModuleNotFoundError"**
- Install missing Python modules: `sudo apt install python3-tk`

**"Permission denied"**
- Fix permissions: `sudo chown -R pi:pi /home/pi/calendar-app`

**"Display not found"**
- Set display: `export DISPLAY=:0`
- Check X11 is running: `ps aux | grep X`

**"Service failed to start"**
- Check service file: `sudo systemctl cat calendar-app.service`
- Reload systemd: `sudo systemctl daemon-reload`

This troubleshooting guide should help resolve most installation and runtime issues. If problems persist, the manual installation script provides step-by-step diagnosis.
