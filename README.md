# Raspberry Pi Touch Calendar

A full-featured calendar application designed specifically for Raspberry Pi with touchscreen displays. Perfect for use as a dedicated calendar kiosk or family organizer.

## Features

### Core Calendar Features
- **Monthly Calendar View**: Clean, touch-friendly monthly calendar display
- **Event Management**: Create, edit, and delete events with detailed information
- **Event Storage**: Persistent storage using JSON files with automatic backups
- **Touch Optimized**: Large buttons and touch-friendly interface
- **Full-Screen Mode**: Designed to run in kiosk mode as the only application

### Event Features
- **Event Creation**: Add events with title, date, time, duration, and description
- **Event Editing**: Modify existing events with full editing capabilities
- **Event Deletion**: Remove events with confirmation dialogs
- **Event List View**: View all events or filter by specific dates
- **Visual Indicators**: Days with events are highlighted in the calendar

### Student Task Management
- **Class-Based Organization**: Create separate task lists for each class/subject
- **Daily Recurring Tasks**: Set up templates that repeat daily automatically
- **Task Completion Tracking**: Check off completed tasks with visual feedback
- **Priority Levels**: Mark tasks as low, medium, or high priority
- **Flexible Task Management**: Add one-time tasks or modify daily templates
- **Progress Visualization**: See task completion status at a glance

### Display Features
- **Auto-Scaling**: Automatically adjusts to different screen sizes
- **Touch-Friendly**: Large buttons optimized for finger touch
- **Color Coding**: Today, selected dates, and event days are color-coded
- **Fullscreen Support**: Runs in fullscreen mode by default

### Settings & Configuration
- **Week Start**: Choose between Monday or Sunday week start
- **Automatic Backups**: Optional automatic backup of event data
- **Default Duration**: Configurable default event duration
- **Persistent Settings**: Settings are saved and restored between sessions

## Requirements

### Hardware
- Raspberry Pi 4B (recommended) or Raspberry Pi 3B+
- Official 7" Raspberry Pi Touchscreen or compatible touch display
- MicroSD card (16GB or larger recommended)
- Power supply appropriate for your Pi model

### Software
- Raspberry Pi OS (Bullseye or newer recommended)
- Python 3.7+
- tkinter (usually included with Python)
- X11 desktop environment

## Installation

### Quick Install
1. Download or clone this repository to your Raspberry Pi
2. Navigate to the project directory
3. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

### Manual Installation

#### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-tk python3-pip xinput unclutter
```

#### 2. Copy Application Files
```bash
# Create application directory
sudo mkdir -p /home/pi/calendar-app
sudo chown pi:pi /home/pi/calendar-app

# Copy files
cp calendar_app.py /home/pi/calendar-app/
cp start_calendar.sh /home/pi/calendar-app/
chmod +x /home/pi/calendar-app/start_calendar.sh
```

#### 3. Configure Auto-Start (Optional)
```bash
# Copy systemd service
sudo cp calendar-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable calendar-app.service
```

#### 4. Configure Auto-Login (Optional)
```bash
sudo raspi-config nonint do_boot_behaviour B4
```

## Usage

### Starting the Application

#### Manual Start
```bash
cd /home/pi/calendar-app
./start_calendar.sh
```

#### Service Control
```bash
# Start service
sudo systemctl start calendar-app.service

# Stop service
sudo systemctl stop calendar-app.service

# Check service status
sudo systemctl status calendar-app.service
```

### Navigation
- **Arrow Buttons**: Navigate between months
- **Today Button**: Jump to current month and date
- **Date Buttons**: Click any date to select it
- **ESC Key**: Exit fullscreen mode (for development/testing)

### Creating Events
1. Click "New Event" button or select a date
2. Fill in event details:
   - **Title**: Event name (required)
   - **Date**: Event date (YYYY-MM-DD format)
   - **Time**: Start time (HH:MM format)
   - **Duration**: Length in minutes
   - **Description**: Additional details
3. Click "Save" to create the event

### Managing Events
- **View Events**: Click "View Events" to see all events or events for a specific date
- **Edit Events**: Double-click an event in the list or select and click "Edit"
- **Delete Events**: Select an event and click "Delete" or use the delete button in edit mode

### Settings
Click "Settings" to configure:
- **Week Start**: Monday or Sunday
- **Automatic Backups**: Enable/disable backup creation
- **Default Duration**: Default event length in minutes

### Creating Daily Tasks
1. Click "Manage Classes" to set up your subjects
2. Add tasks that should repeat daily for each class
3. Use "Daily Tasks" button to view and check off today's tasks
4. Tasks automatically appear each day based on your templates
5. Add one-time tasks for specific days as needed

### Managing Classes
1. Click "Manage Classes" to open the class manager
2. Add your subjects (Math, Science, English, etc.)
3. For each class, create template tasks that repeat daily
4. Set priority levels (High, Medium, Low) for each task
5. Add descriptions for detailed task information
6. Use "Import Example Classes" for quick setup

### Task Workflow
- **Daily Reset**: Each day gets fresh tasks from your templates
- **Completion Tracking**: Check off tasks as you complete them
- **Visual Feedback**: Completed tasks stay checked, uncompleted reset daily
- **Flexible Scheduling**: Add extra tasks for specific days
- **Priority Management**: High priority tasks show with red exclamation marks

## File Structure

```
calendar-app/
├── calendar_app.py          # Main application file
├── start_calendar.sh        # Startup script
├── calendar-app.service     # Systemd service file
├── install.sh              # Installation script
├── README.md               # This file
├── .gitignore              # Git ignore file
├── calendar_events.json    # Event data (created automatically)
├── calendar_tasks.json     # Task templates and daily tasks (created automatically)
├── calendar_config.json    # Settings (created automatically)
├── calendar_events_backup_*.json  # Automatic event backups
└── calendar_tasks_backup_*.json   # Automatic task backups
```

## Configuration Files

### calendar_config.json
```json
{
  "theme": "light",
  "start_week_monday": true,
  "show_week_numbers": false,
  "default_event_duration": 60,
  "backup_enabled": true
}
```

### calendar_events.json
Events are stored in ISO date format with full event details:
```json
{
  "2025-09-15": [
    {
      "title": "Meeting with Team",
      "date": "2025-09-15T14:30:00",
      "duration": 60,
      "description": "Weekly team standup meeting"
    }
  ]
}
```

### calendar_tasks.json
Task templates and daily task completion data:
```json
{
  "class_templates": {
    "Mathematics": [
      {
        "title": "Review previous lesson notes",
        "description": "Go through yesterday's notes and examples",
        "priority": "medium"
      },
      {
        "title": "Complete homework assignment", 
        "description": "Solve all assigned problems",
        "priority": "high"
      }
    ]
  },
  "daily_tasks": {
    "2025-09-15": {
      "Mathematics": [
        {
          "title": "Review previous lesson notes",
          "description": "Go through yesterday's notes and examples", 
          "priority": "medium",
          "completed": true,
          "date_created": "2025-09-15"
        }
      ]
    }
  }
}
```

## Touchscreen Calibration

If your touchscreen input isn't accurate, you may need to calibrate it:

```bash
# Install calibration tool
sudo apt install xinput-calibrator

# Run calibration
xinput_calibrator

# Follow on-screen instructions and save the output
```

## Customization

### Screen Resolution Optimization
The app automatically detects screen size and adjusts:
- **800x480** (7" official touchscreen): Compact layout
- **1024x768** and higher: Larger fonts and buttons

### Modifying Appearance
Edit the `calendar_app.py` file to customize:
- Colors: Search for color definitions (e.g., `bg='lightblue'`)
- Fonts: Modify font definitions in `setup_window()`
- Button sizes: Adjust `button_size` property

### Adding Features
The modular design makes it easy to add features:
- New event fields: Modify the `EventDialog` class
- Different views: Add new view classes
- Import/Export: Extend the data persistence methods

## Troubleshooting

### Application Won't Start
1. Check Python installation: `python3 --version`
2. Verify tkinter: `python3 -c "import tkinter"`
3. Check file permissions: `ls -la calendar_app.py`
4. Run manually for error messages: `python3 calendar_app.py`

### Touch Input Not Working
1. Check if touchscreen is detected: `xinput list`
2. Test touch input: `evtest` (install with `sudo apt install evtest`)
3. Calibrate touchscreen: Use `xinput_calibrator`
4. Check X11 configuration: `/var/log/Xorg.0.log`

### Service Issues
```bash
# Check service logs
sudo journalctl -u calendar-app.service -f

# Restart service
sudo systemctl restart calendar-app.service

# Disable service
sudo systemctl disable calendar-app.service
```

### Display Issues
```bash
# Check display environment
echo $DISPLAY

# Test X11 access
xhost

# Check screen resolution
xrandr

# Test GUI
python3 -c "import tkinter; tkinter.Tk().mainloop()"
```

### Data Recovery
If event data becomes corrupted:
1. Check for backup files: `ls calendar_events_backup_*.json`
2. Copy a backup: `cp calendar_events_backup_YYYYMMDD_HHMMSS.json calendar_events.json`
3. Restart the application

## Development

### Testing on Desktop
The application can be run on a desktop computer for development:
```bash
python3 calendar_app.py
```
Use ESC or F11 to toggle fullscreen mode.

### Adding Debug Output
Add debug prints to troubleshoot:
```python
print(f"Debug: {variable_name}")
```

### Code Structure
- `TouchCalendar`: Main application class
- `EventDialog`: Event creation/editing interface
- `EventListDialog`: Event browsing interface
- `SettingsDialog`: Configuration interface

## Performance Tips

### For Raspberry Pi 3B+
- Reduce button font sizes in `setup_window()`
- Disable automatic backups to reduce I/O
- Consider using a faster SD card (Class 10 or better)

### Memory Optimization
- Close unused applications
- Increase GPU memory split: `sudo raspi-config` → Advanced Options → Memory Split → 128

### Storage Management
Backup files accumulate over time. Clean them periodically:
```bash
# Keep only last 10 backups
ls -t calendar_events_backup_*.json | tail -n +11 | xargs rm -f
```

## Contributing

Contributions are welcome! Areas for improvement:
- Additional calendar views (week, day)
- Import/export functionality (iCal, CSV)
- Recurring events
- Multiple calendar support
- Reminder notifications
- Themes and color schemes

## License

This project is released under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review system logs
3. Test with minimal configuration
4. Create detailed issue reports with system information

## Remote Development

For easy updates from your Windows computer, see [`REMOTE_DEVELOPMENT.md`](REMOTE_DEVELOPMENT.md) for detailed instructions on:
- SSH, VNC, and file sharing setup
- Remote development workflow
- Windows tools and scripts for easy connectivity

**Quick Remote Setup:**
1. Run `setup_remote_access.sh` on your Pi
2. Use `pi_manager.ps1` (PowerShell) or `connect_to_pi.bat` (Command Prompt) on Windows
3. Edit files remotely and sync to production easily

## Changelog

### v1.0.0 (Initial Release)
- Full-featured calendar application
- Touch-optimized interface
- Event management system
- Student task management with class-based organization
- Daily recurring task templates
- Task completion tracking with priorities
- Automatic installation script
- Systemd service integration
- Configuration system
- Automatic backups
- Remote development tools
