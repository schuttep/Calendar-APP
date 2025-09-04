# Calendar App - Class Management System

## Overview

The calendar app now uses a text-based class management system that makes it easy to update your classes and daily tasks via GitHub.

## How It Works

### Class Templates (`classes.txt`)
- All your classes and their default daily tasks are defined in `classes.txt`
- This file is version-controlled with Git, so you can easily update it from anywhere
- The app loads class templates from this file on startup
- Use the "Reload Classes" button to refresh after updating the file

### Daily Task Progress (`calendar_tasks.json`)
- Your daily task completion status is saved locally in JSON format
- This file tracks which tasks you've completed on which days
- This file is NOT synced to GitHub (it's personal progress data)

## File Format for `classes.txt`

```
# Class name (no indentation)
CLASS_NAME
  [priority] Task Title - Task Description
  [priority] Another Task - Another Description

# Another class
ANOTHER_CLASS
  [high] Important Task - This is urgent
  [medium] Regular Task - This is normal priority
  [low] Optional Task - This can wait
```

### Priority Levels
- `[high]` - Red/urgent tasks
- `[medium]` - Normal priority (default)
- `[low]` - Low priority tasks

### Example
```
MATH
  [high] Complete homework assignment - Finish problems 1-20 from chapter 5
  [medium] Review notes from today's lesson - Go over derivative rules
  [low] Organize math binder - File handouts and clean up notes

SCIENCE  
  [high] Lab report due Friday - Write conclusion for chemistry experiment
  [medium] Read textbook chapter 8 - Study cellular respiration
```

## Updating Your Classes

### Method 1: Direct Edit on Pi
1. SSH into your Pi: `ssh payto@<pi-ip-address>`
2. Edit the file: `nano ~/calendar-app/classes.txt`
3. Save and exit (Ctrl+X, Y, Enter)
4. In the calendar app, click "Reload Classes"

### Method 2: Update via GitHub
1. Edit `classes.txt` on your computer
2. Commit and push changes to GitHub
3. On Pi, pull the changes: `cd ~/calendar-app && git pull`
4. In the calendar app, click "Reload Classes"

### Method 3: Remote Update from Windows
1. Edit `classes.txt` on your computer
2. Run: `.\update_pi.ps1 -PiAddress <your-pi-ip>`
3. In the calendar app, click "Reload Classes"

## UI Changes

- **"Manage Classes" button** → **"Reload Classes" button**
- No more complex class management dialog
- Simple text file editing instead of GUI forms
- Easier to backup and version control your class lists

## Benefits

✅ **Easy Updates**: Edit a simple text file instead of using complex dialogs
✅ **Version Control**: Track changes to your class lists over time
✅ **Remote Updates**: Update from any computer via GitHub or SCP
✅ **Backup Friendly**: Text file is easy to backup and restore
✅ **Collaboration**: Share class templates with others easily

## Migration Notes

If you had existing classes in the old system, you'll need to recreate them in the `classes.txt` file format. The app will automatically start using the text file system and ignore old JSON class templates.

## Files

- `classes.txt` - Class templates and default tasks (synced to GitHub)
- `calendar_tasks.json` - Daily task completion tracking (local only)
- `calendar_events.json` - Calendar events (local only)
- `calendar_config.json` - App settings (local only)
