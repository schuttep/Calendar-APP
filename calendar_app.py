#!/usr/bin/env python3
"""
Raspberry Pi Touch Calendar Application
A full-featured calendar app optimized for touchscreen displays
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font, filedialog
import calendar
import datetime
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
import copy
from urllib.parse import unquote

class TouchCalendar:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_window()
        self.load_config()
        self.load_events()
        self.load_tasks()
        self.current_date = datetime.date.today()
        self.selected_date = None
        self.view_mode = 'month'  # 'month' or 'week'
        self.create_widgets()
        self.update_calendar()
        
    def setup_window(self):
        """Configure the main window for touchscreen use"""
        self.root.title("Touch Calendar")
        
        # Get screen dimensions first
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # True kiosk mode - hide taskbar but allow dialogs to appear
        self.root.attributes('-fullscreen', True)  # Use fullscreen instead of overrideredirect
        self.root.attributes('-topmost', False)  # Don't force always on top to allow dialogs
        
        # Configure for common Raspberry Pi touchscreen resolutions
        if screen_width <= 800 and screen_height <= 600:
            # 7" touchscreen (800x480)
            self.button_font = ('Arial', 12, 'bold')
            self.header_font = ('Arial', 16, 'bold')
            self.date_font = ('Arial', 10)
            self.button_size = 60
        elif screen_width <= 1024:
            # Larger touchscreens
            self.button_font = ('Arial', 14, 'bold')
            self.header_font = ('Arial', 20, 'bold')
            self.date_font = ('Arial', 12)
            self.button_size = 70
        else:
            # Desktop/larger displays
            self.button_font = ('Arial', 16, 'bold')
            self.header_font = ('Arial', 24, 'bold')
            self.date_font = ('Arial', 14)
            self.button_size = 80
            
        # Bind keys for window management  
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.fullscreen = True  # Start in fullscreen mode
        
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode - especially useful for touchscreen keyboard access"""
        try:
            if self.fullscreen:
                # Exit fullscreen - show taskbar and allow keyboard
                self.root.attributes('-fullscreen', False)
                # Make window smaller to show taskbar
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width}x{screen_height-50}+0+0")
                self.fullscreen = False
            else:
                # Enter fullscreen mode - hide taskbar
                self.root.attributes('-fullscreen', True)
                self.fullscreen = True
        except Exception as e:
            # Fallback for different platforms
            print(f"Fullscreen toggle error: {e}")
            try:
                current = self.root.attributes('-fullscreen')
                self.root.attributes('-fullscreen', not current)
            except:
                pass
        
    def load_config(self):
        """Load configuration settings"""
        # Get script directory for absolute file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(script_dir, "calendar_config.json")
        self.default_config = {
            'theme': 'light',
            'start_week_monday': True,
            'show_week_numbers': False,
            'default_event_duration': 60,
            'backup_enabled': True
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config.copy()
            
    def save_config(self):
        """Save configuration settings"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def load_events(self):
        """Load events from JSON file"""
        # Get script directory for absolute file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.events_file = os.path.join(script_dir, "calendar_events.json")
        self.events = {}  # Format: {date_string: [event_dict, ...]}
        
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    self.events = json.load(f)
        except Exception as e:
            print(f"Error loading events: {e}")
            self.events = {}
            
    def load_tasks(self):
        """Load tasks and checklists from JSON file and classes from text file"""
        # Get script directory for absolute file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.tasks_file = os.path.join(script_dir, "calendar_tasks.json")
        self.classes_file = os.path.join(script_dir, "classes.txt")
        self.class_templates = {}  # Format: {class_name: [task_dict, ...]}
        self.daily_tasks = {}  # Format: {date_string: {class_name: [task_dict, ...]}}
        
        # First load class templates from text file
        self.load_class_templates()
        
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    # Only load daily tasks from JSON, templates come from text file
                    self.daily_tasks = data.get('daily_tasks', {})
        except Exception as e:
            print(f"Error loading tasks: {e}")
            self.daily_tasks = {}
            
    def load_class_templates(self):
        """Load class templates from classes.txt file and auto-generated ICS classes"""
        # Load from manual classes.txt first
        self.load_classes_from_file(self.classes_file)
        
        # Then load auto-generated classes from ICS import
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ics_classes_file = os.path.join(script_dir, "classes_from_ics.txt")
        if os.path.exists(ics_classes_file):
            print(f"Loading auto-generated classes from {ics_classes_file}")
            self.load_classes_from_file(ics_classes_file)
        
    def load_classes_from_file(self, file_path):
        """Load class templates from a specific text file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_class = None
                    for line in f:
                        line = line.rstrip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                            
                        # Class name (not indented)
                        if not line.startswith(' ') and not line.startswith('\t'):
                            current_class = line.strip()
                            if current_class:
                                if current_class not in self.class_templates:
                                    self.class_templates[current_class] = []
                        
                        # Task (indented)
                        elif line.startswith('  ') and current_class:
                            task_line = line.strip()
                            
                            # Parse priority and task
                            priority = "medium"  # default
                            title = task_line
                            description = ""
                            
                            # Check for priority format [priority]
                            if task_line.startswith('[') and ']' in task_line:
                                priority_end = task_line.find(']')
                                priority = task_line[1:priority_end].strip()
                                remaining = task_line[priority_end + 1:].strip()
                                
                                # Split title and description by ' - '
                                if ' - ' in remaining:
                                    title, description = remaining.split(' - ', 1)
                                else:
                                    title = remaining
                            
                            task_dict = {
                                'title': title,
                                'description': description,
                                'priority': priority
                            }
                            self.class_templates[current_class].append(task_dict)
            else:
                print(f"Classes file {file_path} not found.")
                
        except Exception as e:
            print(f"Error loading class templates from {file_path}: {e}")
            self.class_templates = {}
            
    def save_tasks(self):
        """Save daily tasks to JSON file (class templates are loaded from classes.txt)"""
        try:
            data = {
                'daily_tasks': self.daily_tasks
            }
            with open(self.tasks_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Create backup if enabled
            if self.config.get('backup_enabled', True):
                backup_file = f"calendar_tasks_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
            
    def reload_class_templates(self):
        """Reload class templates from classes.txt file"""
        self.load_class_templates()
        messagebox.showinfo("Classes Reloaded", 
            f"Loaded {len(self.class_templates)} classes from classes.txt")
            
    def parse_ics_file(self, file_path):
        """Parse ICS calendar file and import events"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            events = []
            current_event = {}
            in_vevent = False
            
            for line in content.split('\n'):
                line = line.strip()
                
                if line == 'BEGIN:VEVENT':
                    in_vevent = True
                    current_event = {}
                elif line == 'END:VEVENT':
                    if in_vevent and current_event:
                        events.append(current_event.copy())
                    in_vevent = False
                    current_event = {}
                elif in_vevent and ':' in line:
                    # Handle line continuations (lines starting with space)
                    if line.startswith(' ') or line.startswith('\t'):
                        continue
                    
                    key, value = line.split(':', 1)
                    
                    # Handle parameters in key (like DTSTART;TZID=America/Chicago)
                    if ';' in key:
                        key = key.split(';')[0]
                    
                    current_event[key] = value
            
            return events
        except Exception as e:
            print(f"Error parsing ICS file: {e}")
            return []
    
    def parse_ics_datetime(self, dt_string, default_date=None):
        """Parse ICS datetime string"""
        try:
            # Remove timezone info for now (just use local time)
            if 'TZID=' in dt_string:
                dt_string = dt_string.split(':', 1)[1]
            
            # Handle different date formats
            if 'T' in dt_string:
                # Full datetime: 20240826T110000
                if len(dt_string) >= 15:
                    return datetime.datetime.strptime(dt_string[:15], '%Y%m%dT%H%M%S')
            else:
                # Date only: 20240826
                if len(dt_string) >= 8:
                    return datetime.datetime.strptime(dt_string[:8], '%Y%m%d')
                    
        except Exception as e:
            print(f"Error parsing datetime '{dt_string}': {e}")
            return default_date or datetime.datetime.now()
    
    def import_ics_events(self, file_path):
        """Import events from ICS file"""
        print(f"Starting ICS import from: {file_path}")
        events = self.parse_ics_file(file_path)
        print(f"Parsed {len(events)} events from ICS file")
        imported_count = 0
        
        for i, ics_event in enumerate(events):
            try:
                print(f"\nProcessing event {i+1}/{len(events)}")
                
                # Extract basic event info
                summary = ics_event.get('SUMMARY', 'Untitled Event')
                description = ics_event.get('DESCRIPTION', '').replace('\\n', '\n')
                location = ics_event.get('LOCATION', '')
                
                print(f"  Summary: {summary}")
                print(f"  Location: {location}")
                
                # Parse start time
                start_dt = self.parse_ics_datetime(ics_event.get('DTSTART', ''))
                if not start_dt:
                    print(f"  Skipping - no valid start time")
                    continue
                    
                # Parse end time
                end_dt = self.parse_ics_datetime(ics_event.get('DTEND', ''), start_dt)
                
                print(f"  Start: {start_dt}")
                print(f"  End: {end_dt}")
                
                # Create event object
                event = {
                    'title': summary,
                    'description': description,
                    'location': location,
                    'start_time': start_dt.strftime('%H:%M'),
                    'end_time': end_dt.strftime('%H:%M'),
                    'all_day': False,
                    'category': 'imported',
                    'imported_from': 'ics'
                }
                
                # Handle recurring events (RRULE)
                rrule = ics_event.get('RRULE', '')
                print(f"  RRULE: {rrule}")
                
                if rrule and 'FREQ=WEEKLY' in rrule:
                    # Parse weekly recurring events
                    until_match = re.search(r'UNTIL=(\d{8})', rrule)
                    byday_match = re.search(r'BYDAY=([^;]+)', rrule)
                    
                    print(f"  Until match: {until_match.group(1) if until_match else 'None'}")
                    print(f"  Days match: {byday_match.group(1) if byday_match else 'None'}")
                    
                    if byday_match:
                        days = byday_match.group(1).split(',')
                        day_map = {
                            'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6
                        }
                        
                        until_date = datetime.date(2025, 12, 31)  # Default end date
                        if until_match:
                            until_str = until_match.group(1)
                            until_date = datetime.datetime.strptime(until_str, '%Y%m%d').date()
                        
                        print(f"  Creating recurring events until: {until_date}")
                        print(f"  Days: {days}")
                        
                        # Create recurring events
                        current_date = start_dt.date()
                        event_count = 0
                        while current_date <= until_date:
                            weekday = current_date.weekday()
                            if any(day_map.get(day) == weekday for day in days):
                                date_str = current_date.isoformat()
                                if date_str not in self.events:
                                    self.events[date_str] = []
                                
                                # Check if event already exists
                                exists = any(e['title'] == event['title'] and 
                                           e['start_time'] == event['start_time'] 
                                           for e in self.events[date_str])
                                if not exists:
                                    # Create the calendar event
                                    calendar_event = event.copy()
                                    calendar_event['category'] = 'class'  # Mark as class event
                                    self.events[date_str].append(calendar_event)
                                    imported_count += 1
                                    event_count += 1
                            
                            current_date += datetime.timedelta(days=1)
                        
                        print(f"  Created {event_count} recurring events")
                else:
                    # Single event
                    print(f"  Creating single event")
                    date_str = start_dt.date().isoformat()
                    if date_str not in self.events:
                        self.events[date_str] = []
                    
                    # Check if event already exists
                    exists = any(e['title'] == event['title'] and 
                               e['start_time'] == event['start_time'] 
                               for e in self.events[date_str])
                    if not exists:
                        # Create the calendar event
                        calendar_event = event.copy()
                        calendar_event['category'] = 'class'  # Mark as class event
                        self.events[date_str].append(calendar_event)
                        imported_count += 1
                        print(f"  Added single event for {date_str}")
                    else:
                        print(f"  Event already exists for {date_str}")
                        
            except Exception as e:
                print(f"Error importing event: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Total events imported: {imported_count}")
        
        # Save events and update calendar
        self.save_events()
        self.update_calendar()
        
        # Extract class names from imported events and create templates
        self.extract_class_templates_from_events()
        
        return imported_count
        
    def extract_class_templates_from_events(self):
        """Extract class names from imported events and create basic task templates"""
        extracted_classes = {}
        
        for date_str, events in self.events.items():
            for event in events:
                if event.get('imported_from') == 'ics':
                    # Extract class information from event title
                    title = event.get('title', '')
                    
                    # Parse different formats of class titles
                    class_name = self.parse_class_name(title)
                    if class_name and class_name not in extracted_classes:
                        # Create basic task template for this class
                        extracted_classes[class_name] = [
                            {
                                'title': 'Review today\'s material',
                                'description': f'Review notes and materials from {class_name}',
                                'priority': 'medium'
                            },
                            {
                                'title': 'Complete homework/assignments',
                                'description': f'Work on any assignments for {class_name}',
                                'priority': 'high'
                            },
                            {
                                'title': 'Prepare for next class',
                                'description': f'Read ahead and prepare for next {class_name} session',
                                'priority': 'medium'
                            },
                            {
                                'title': 'Study/practice problems',
                                'description': f'Practice problems or study concepts from {class_name}',
                                'priority': 'medium'
                            }
                        ]
        
        # Merge with existing class templates (prioritize ICS-extracted classes)
        if extracted_classes:
            self.class_templates.update(extracted_classes)
            
            # Create a classes_from_ics.txt file to show what was extracted
            try:
                with open('classes_from_ics.txt', 'w', encoding='utf-8') as f:
                    f.write("# Classes extracted from ICS calendar import\n")
                    f.write("# This file was auto-generated from your imported calendar\n\n")
                    
                    for class_name, tasks in extracted_classes.items():
                        f.write(f"{class_name}\n")
                        for task in tasks:
                            priority = task['priority']
                            title = task['title']
                            description = task['description']
                            f.write(f"  [{priority}] {title} - {description}\n")
                        f.write("\n")
                        
                print(f"Created class templates for: {', '.join(extracted_classes.keys())}")
            except Exception as e:
                print(f"Error creating classes_from_ics.txt: {e}")
    
    def parse_class_name(self, event_title):
        """Parse class name from various ICS event title formats"""
        if not event_title:
            return None
            
        title = event_title.strip()
        print(f"Parsing title: '{title}'")  # Debug output
        
        # Clean up HTML entities
        title = title.replace('&amp;', '&')
        
        # Common patterns for university class titles:
        # "Intro to Algs & Models of Comp ECE 374 BYA" -> "ECE 374 - Intro to Algs & Models of Comp"
        # "Applied Parallel Programming ECE 408 AL1" -> "ECE 408 - Applied Parallel Programming"
        # "Principles of Safe Autonomy ECE 484 AL1" -> "ECE 484 - Principles of Safe Autonomy"
        
        import re
        
        # Pattern 1: Subject Name + Course Code + Section (like "Intro to Algs & Models of Comp ECE 374 BYA")
        pattern1 = r'^(.+?)\s+([A-Z]{2,4}\s+\d{3})\s+[A-Z]{1,3}\d*$'
        match1 = re.match(pattern1, title)
        if match1:
            subject = match1.group(1).strip()
            course_code = match1.group(2).strip()
            result = f"{course_code} - {subject}"
            print(f"Pattern 1 match: '{result}'")
            return result
        
        # Pattern 2: Course Code + Subject Name (like "ECE374 Applied Programming")
        pattern2 = r'^([A-Z]{2,4}\s*\d{3})\s+(.+?)(\s+[A-Z]{1,3}\d*)?$'
        match2 = re.match(pattern2, title)
        if match2:
            course_code = match2.group(1).strip()
            subject = match2.group(2).strip()
            # Remove section info from subject
            subject = re.sub(r'\s+(AL\d*|AD\d*|Lab|Discussion|Lecture|BYA|BL\d*|AB\d*).*$', '', subject)
            result = f"{course_code} - {subject}"
            print(f"Pattern 2 match: '{result}'")
            return result
            
        # Pattern 3: Simple course code pattern (like "MATH 101" or "HK 104")
        pattern3 = r'([A-Z]{2,4}\s+\d{3})'
        match3 = re.search(pattern3, title)
        if match3:
            course_code = match3.group(1)
            # Try to get subject name before the code
            remaining = title.replace(course_code, '').strip()
            # Remove section codes
            remaining = re.sub(r'\s+[A-Z]{1,3}\d*$', '', remaining)
            if remaining and len(remaining) > 2:
                result = f"{course_code} - {remaining}"
                print(f"Pattern 3 match: '{result}'")
                return result
            else:
                print(f"Pattern 3 simple match: '{course_code}'")
                return course_code
        
        # Pattern 4: Just return cleaned title if it looks like a class
        if re.search(r'[A-Z]{2,4}\s+\d{2,3}', title):
            # Clean up common suffixes
            cleaned = re.sub(r'\s+[A-Z]{1,3}\d*$', '', title)
            print(f"Pattern 4 fallback: '{cleaned}'")
            return cleaned.strip()
        
        print(f"No pattern matched for: '{title}'")
        return None
            
    def save_events(self):
        """Save events to JSON file"""
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
            
            # Create backup if enabled
            if self.config.get('backup_enabled', True):
                backup_file = f"calendar_events_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w') as f:
                    json.dump(self.events, f, indent=2)
        except Exception as e:
            print(f"Error saving events: {e}")
            
    def create_widgets(self):
        """Create the main UI components"""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header frame with navigation
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Navigation buttons
        self.prev_month_btn = tk.Button(
            self.header_frame, text="◀", font=self.header_font,
            command=self.prev_month, width=3, height=1,
            bg='lightblue', relief='raised', bd=2
        )
        self.prev_month_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.month_year_label = tk.Label(
            self.header_frame, font=self.header_font,
            fg='darkblue'
        )
        self.month_year_label.pack(side=tk.LEFT, expand=True)
        
        self.next_month_btn = tk.Button(
            self.header_frame, text="▶", font=self.header_font,
            command=self.next_month, width=3, height=1,
            bg='lightblue', relief='raised', bd=2
        )
        self.next_month_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # View toggle button
        self.view_toggle_btn = tk.Button(
            self.header_frame, text="Week", font=self.button_font,
            command=self.toggle_view, bg='lightyellow',
            relief='raised', bd=2, width=6
        )
        self.view_toggle_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Today button
        self.today_btn = tk.Button(
            self.header_frame, text="Today", font=self.button_font,
            command=self.go_to_today, bg='lightgreen',
            relief='raised', bd=2
        )
        self.today_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Calendar frame
        self.calendar_frame = ttk.Frame(self.main_frame)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Day labels
        self.day_labels_frame = ttk.Frame(self.calendar_frame)
        self.day_labels_frame.pack(fill=tk.X)
        
        # Calendar grid
        self.calendar_grid_frame = ttk.Frame(self.calendar_frame)
        self.calendar_grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bottom frame with action buttons
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X)
        
        # Action buttons
        self.new_event_btn = tk.Button(
            self.bottom_frame, text="New Event", font=self.button_font,
            command=self.new_event, bg='lightgreen',
            relief='raised', bd=2, height=2
        )
        self.new_event_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.view_events_btn = tk.Button(
            self.bottom_frame, text="View Events", font=self.button_font,
            command=self.view_events, bg='lightblue',
            relief='raised', bd=2, height=2
        )
        self.view_events_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.tasks_btn = tk.Button(
            self.bottom_frame, text="Daily Tasks", font=self.button_font,
            command=self.show_daily_tasks, bg='lightyellow',
            relief='raised', bd=2, height=2
        )
        self.tasks_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.classes_btn = tk.Button(
            self.bottom_frame, text="Reload Classes", font=self.button_font,
            command=self.reload_class_templates, bg='lightcyan',
            relief='raised', bd=2, height=2
        )
        self.classes_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.import_btn = tk.Button(
            self.bottom_frame, text="Import Calendar", font=self.button_font,
            command=self.import_calendar, bg='lightgreen',
            relief='raised', bd=2, height=2
        )
        self.import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add keyboard toggle button for touchscreens
        screen_width = self.root.winfo_screenwidth()
        if screen_width <= 800:
            self.keyboard_btn = tk.Button(
                self.bottom_frame, text="⌨️", font=self.button_font,
                command=self.toggle_virtual_keyboard, bg='lightgray',
                relief='raised', bd=2, height=2, width=3
            )
            self.keyboard_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.settings_btn = tk.Button(
            self.bottom_frame, text="Settings", font=self.button_font,
            command=self.show_settings, bg='lightyellow',
            relief='raised', bd=2, height=2
        )
        self.settings_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.exit_btn = tk.Button(
            self.bottom_frame, text="Exit", font=self.button_font,
            command=self.exit_app, bg='lightcoral',
            relief='raised', bd=2, height=2
        )
        self.exit_btn.pack(side=tk.RIGHT)
        
        # Status label
        self.status_label = tk.Label(
            self.bottom_frame, text="Ready", font=self.date_font,
            relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
    def update_calendar(self):
        """Update the calendar display"""
        if self.view_mode == 'month':
            self.update_month_view()
        else:
            self.update_week_view()
    
    def update_month_view(self):
        """Update the month calendar display"""
        # Update month/year label
        month_name = calendar.month_name[self.current_date.month]
        self.month_year_label.config(
            text=f"{month_name} {self.current_date.year}"
        )
        
        # Clear existing calendar
        for widget in self.day_labels_frame.winfo_children():
            widget.destroy()
        for widget in self.calendar_grid_frame.winfo_children():
            widget.destroy()
            
        # Day labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if not self.config.get('start_week_monday', True):
            days = ['Sun'] + days[:-1]
            
        for i, day in enumerate(days):
            label = tk.Label(
                self.day_labels_frame, text=day, font=self.button_font,
                bg='lightgray', relief='raised', bd=1
            )
            label.grid(row=0, column=i, sticky='nsew', padx=1, pady=1)
            self.day_labels_frame.columnconfigure(i, weight=1)
            
        # Calendar days
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Adjust for Sunday start if configured
        if not self.config.get('start_week_monday', True):
            # Convert from Monday-start to Sunday-start
            for week in cal:
                if week[0] == 0:  # If Monday is 0, move Sunday to front
                    sunday = week.pop()
                    week.insert(0, sunday)
                else:
                    week.insert(0, 0)  # Add empty Sunday
                    week.pop()  # Remove extra day
                    
        today = datetime.date.today()
        
        for week_num, week in enumerate(cal):
            self.calendar_grid_frame.rowconfigure(week_num, weight=1)
            for day_num, day in enumerate(week):
                self.calendar_grid_frame.columnconfigure(day_num, weight=1)
                
                if day == 0:
                    # Empty cell for days outside current month
                    frame = tk.Frame(self.calendar_grid_frame, bg='white')
                    frame.grid(row=week_num, column=day_num, sticky='nsew', padx=1, pady=1)
                else:
                    # Create day button
                    date_obj = datetime.date(self.current_date.year, self.current_date.month, day)
                    date_str = date_obj.isoformat()
                    
                    # Check if this date has events
                    has_events = date_str in self.events and len(self.events[date_str]) > 0
                    has_tasks = date_str in self.daily_tasks and len(self.daily_tasks[date_str]) > 0
                    
                    # Determine button color
                    if date_obj == today:
                        bg_color = 'lightgreen'
                    elif date_obj == self.selected_date:
                        bg_color = 'yellow'
                    elif has_events and has_tasks:
                        bg_color = 'orange'
                    elif has_events:
                        bg_color = 'lightcoral'
                    elif has_tasks:
                        bg_color = 'lightblue'
                    else:
                        bg_color = 'white'
                        
                    btn = tk.Button(
                        self.calendar_grid_frame, text=str(day),
                        font=self.date_font, bg=bg_color,
                        relief='raised', bd=2,
                        command=lambda d=date_obj: self.select_date(d)
                    )
                    btn.grid(row=week_num, column=day_num, sticky='nsew', padx=1, pady=1)
                    
        # Update status
        event_count = sum(len(events) for events in self.events.values())
        task_count = sum(len(class_tasks) for daily_tasks in self.daily_tasks.values() for class_tasks in daily_tasks.values())
        self.status_label.config(text=f"Events: {event_count} | Tasks: {task_count}")
        
    def update_week_view(self):
        """Update the week calendar display"""
        # Get the week containing the current date
        if self.config.get('start_week_monday', True):
            # Monday start - find Monday of current week
            start_of_week = self.current_date - datetime.timedelta(days=self.current_date.weekday())
            days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        else:
            # Sunday start - find Sunday of current week
            days_since_sunday = (self.current_date.weekday() + 1) % 7
            start_of_week = self.current_date - datetime.timedelta(days=days_since_sunday)
            days_order = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            
        week_dates = [start_of_week + datetime.timedelta(days=i) for i in range(7)]
        
        # Update month/year label to show week range
        start_str = start_of_week.strftime('%b %d')
        end_str = week_dates[-1].strftime('%b %d, %Y')
        self.month_year_label.config(text=f"{start_str} - {end_str}")
        
        # Clear existing calendar
        for widget in self.day_labels_frame.winfo_children():
            widget.destroy()
        for widget in self.calendar_grid_frame.winfo_children():
            widget.destroy()
            
        # Day labels
        for i, day in enumerate(days_order):
            label = tk.Label(
                self.day_labels_frame, text=day, font=self.button_font,
                bg='lightgray', relief='raised', bd=1
            )
            label.grid(row=0, column=i, sticky='nsew', padx=1, pady=1)
            self.day_labels_frame.columnconfigure(i, weight=1)
        
        # Week view - show one row with more detail
        today = datetime.date.today()
        self.calendar_grid_frame.rowconfigure(0, weight=1)
        
        for day_num, date_obj in enumerate(week_dates):
            self.calendar_grid_frame.columnconfigure(day_num, weight=1)
            
            date_str = date_obj.isoformat()
            
            # Check if this date has events
            has_events = date_str in self.events and len(self.events[date_str]) > 0
            has_tasks = date_str in self.daily_tasks and len(self.daily_tasks[date_str]) > 0
            
            # Determine background color
            if date_obj == today:
                bg_color = 'lightgreen'
            elif date_obj == self.selected_date:
                bg_color = 'yellow'
            elif has_events and has_tasks:
                bg_color = 'orange'
            elif has_events:
                bg_color = 'lightcoral'
            elif has_tasks:
                bg_color = 'lightblue'
            else:
                bg_color = 'white'
            
            # Create frame for this day
            day_frame = tk.Frame(self.calendar_grid_frame, bg=bg_color, relief='raised', bd=2)
            day_frame.grid(row=0, column=day_num, sticky='nsew', padx=1, pady=1)
            
            # Day number and date button
            day_text = f"{date_obj.day}\n{date_obj.strftime('%m/%d')}"
            day_btn = tk.Button(
                day_frame, text=day_text,
                font=self.button_font, bg=bg_color,
                relief='flat', bd=0,
                command=lambda d=date_obj: self.select_date(d)
            )
            day_btn.pack(fill=tk.X)
            
            # Show events for this day
            if has_events:
                events_for_day = self.events[date_str]
                # Sort events by start time
                events_for_day = sorted(events_for_day, key=lambda x: x.get('start_time', '00:00'))
                
                # Show up to 4 events
                for i, event in enumerate(events_for_day[:4]):
                    event_text = f"{event.get('start_time', '')} {event['title'][:12]}"
                    if len(event['title']) > 12:
                        event_text += "..."
                    
                    # Color code by event type
                    if event.get('category') == 'class':
                        event_bg = 'lightsteelblue'
                        text_color = 'darkblue'
                    else:
                        event_bg = 'mistyrose' 
                        text_color = 'darkred'
                    
                    event_label = tk.Label(
                        day_frame, text=event_text,
                        font=('Arial', 7), bg=event_bg, fg=text_color,
                        wraplength=70, justify=tk.LEFT, relief='solid', bd=1
                    )
                    event_label.pack(fill=tk.X, pady=1, padx=1)
                
                if len(events_for_day) > 4:
                    more_label = tk.Label(
                        day_frame, text=f"+{len(events_for_day) - 4} more",
                        font=('Arial', 6), fg='gray', bg=bg_color
                    )
                    more_label.pack()
            
        # Update status
        week_events = sum(len(self.events.get(date.isoformat(), [])) for date in week_dates)
        week_tasks = sum(len(class_tasks) for date in week_dates 
                        for class_tasks in self.daily_tasks.get(date.isoformat(), {}).values())
        self.status_label.config(text=f"This week - Events: {week_events} | Tasks: {week_tasks}")
        
    def select_date(self, date_obj: datetime.date):
        """Handle date selection"""
        self.selected_date = date_obj
        self.update_calendar()
        
        # Show events for selected date if any exist
        date_str = date_obj.isoformat()
        if date_str in self.events and self.events[date_str]:
            self.view_events_for_date(date_obj)
        elif date_str in self.daily_tasks and self.daily_tasks[date_str]:
            self.show_daily_tasks(date_obj)
            
    def prev_month(self):
        """Navigate to previous month/week"""
        if self.view_mode == 'month':
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        else:  # week view
            self.current_date = self.current_date - datetime.timedelta(weeks=1)
        self.update_calendar()
        
    def next_month(self):
        """Navigate to next month/week"""
        if self.view_mode == 'month':
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        else:  # week view
            self.current_date = self.current_date + datetime.timedelta(weeks=1)
        self.update_calendar()
        
    def toggle_view(self):
        """Toggle between month and week view"""
        if self.view_mode == 'month':
            self.view_mode = 'week'
            self.view_toggle_btn.config(text="Month")
        else:
            self.view_mode = 'month' 
            self.view_toggle_btn.config(text="Week")
        self.update_calendar()
        
    def go_to_today(self):
        """Navigate to current month"""
        today = datetime.date.today()
        self.current_date = today
        self.selected_date = today
        self.update_calendar()
        
    def new_event(self):
        """Create a new event"""
        if self.selected_date:
            default_date = self.selected_date
        else:
            default_date = datetime.date.today()
            
        EventDialog(self.root, self, date=default_date)
        
    def view_events(self):
        """View all events"""
        EventListDialog(self.root, self)
        
    def view_events_for_date(self, date_obj: datetime.date):
        """View events for a specific date"""
        EventListDialog(self.root, self, date=date_obj)
        
    def show_daily_tasks(self, date=None):
        """Show daily tasks dialog"""
        if date is None:
            date = self.selected_date or datetime.date.today()
        DailyTasksDialog(self.root, self, date)
        
    def manage_classes(self):
        """Show class management dialog"""
        ClassManagementDialog(self.root, self)
        
    def get_tasks_for_date(self, date: datetime.date) -> Dict:
        """Get tasks for a specific date, creating from templates if needed"""
        date_str = date.isoformat()
        
        # If no tasks for this date, create from class templates
        if date_str not in self.daily_tasks:
            self.daily_tasks[date_str] = {}
            for class_name, template_tasks in self.class_templates.items():
                self.daily_tasks[date_str][class_name] = []
                for template_task in template_tasks:
                    # Create a copy of the template task with completed=False
                    daily_task = copy.deepcopy(template_task)
                    daily_task['completed'] = False
                    daily_task['date_created'] = date_str
                    self.daily_tasks[date_str][class_name].append(daily_task)
            self.save_tasks()
        
        return self.daily_tasks.get(date_str, {})
        
    def update_task_completion(self, date: datetime.date, class_name: str, task_index: int, completed: bool):
        """Update task completion status"""
        date_str = date.isoformat()
        if (date_str in self.daily_tasks and 
            class_name in self.daily_tasks[date_str] and 
            0 <= task_index < len(self.daily_tasks[date_str][class_name])):
            
            self.daily_tasks[date_str][class_name][task_index]['completed'] = completed
            self.save_tasks()
            self.update_calendar()
            
    def show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self.root, self)
        
    def import_calendar(self):
        """Import calendar from ICS file"""
        # Check for both Fall 2024 and Fall 2025 files
        default_files = [
            "Fall 2025 - Urbana-Champaign.ics",
            "Fall 2024 - Urbana-Champaign.ics"
        ]
        
        file_path = None
        for filename in default_files:
            if os.path.exists(filename):
                if messagebox.askyesno("Import Calendar", 
                    f"Found '{filename}' in the app directory. Import this file?"):
                    file_path = filename
                    break
        
        # If no default file or user declined, show file dialog
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select Calendar File",
                filetypes=[("Calendar files", "*.ics"), ("All files", "*.*")]
            )
        
        if file_path:
            try:
                print(f"Importing from: {file_path}")
                count = self.import_ics_events(file_path)
                class_count = len([cls for cls in self.class_templates.keys() 
                                 if any("Review today's material" in task.get('title', '') 
                                       for task in self.class_templates[cls])])
                
                message = f"Successfully imported {count} events from {os.path.basename(file_path)}"
                if class_count > 0:
                    message += f"\n\nAlso created daily task templates for {class_count} classes."
                    message += "\nCheck 'Daily Tasks' to see your class-based todo lists!"
                    
                messagebox.showinfo("Import Complete", message)
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import calendar: {str(e)}")
                print(f"Import error details: {e}")
                import traceback
                traceback.print_exc()
                
    def toggle_virtual_keyboard(self):
        """Toggle virtual keyboard on touchscreen devices"""
        try:
            # Try to launch the onscreen keyboard
            import subprocess
            subprocess.Popen(['onboard'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except:
            try:
                # Alternative: matchbox-keyboard
                subprocess.Popen(['matchbox-keyboard'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except:
                # Show helpful message if no virtual keyboard is available
                messagebox.showinfo("Virtual Keyboard", 
                    "Virtual keyboard not found.\n\n" +
                    "To install:\n" +
                    "sudo apt install onboard\n" +
                    "or\n" +
                    "sudo apt install matchbox-keyboard\n\n" +
                    "Press Escape to exit fullscreen for easier typing.")
            
    def exit_app(self):
        """Exit the application"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.save_events()
            self.save_tasks()
            self.save_config()
            self.root.quit()
            
    def add_event(self, date: datetime.date, event: Dict):
        """Add an event to the calendar"""
        date_str = date.isoformat()
        if date_str not in self.events:
            self.events[date_str] = []
        self.events[date_str].append(event)
        self.save_events()
        self.update_calendar()
        
    def remove_event(self, date: datetime.date, event_index: int):
        """Remove an event from the calendar"""
        date_str = date.isoformat()
        if date_str in self.events and 0 <= event_index < len(self.events[date_str]):
            self.events[date_str].pop(event_index)
            if not self.events[date_str]:  # Remove empty date entry
                del self.events[date_str]
            self.save_events()
            self.update_calendar()
            
    def update_event(self, date: datetime.date, event_index: int, updated_event: Dict):
        """Update an existing event"""
        date_str = date.isoformat()
        if date_str in self.events and 0 <= event_index < len(self.events[date_str]):
            self.events[date_str][event_index] = updated_event
            self.save_events()
            self.update_calendar()


class EventDialog:
    """Dialog for creating/editing events"""
    def __init__(self, parent, calendar_app, event=None, date=None):
        self.parent = parent
        self.calendar_app = calendar_app
        self.event = event
        self.date = date or datetime.date.today()
        self.result = None
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the event dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Event Details" if not self.event else "Edit Event")
        
        # Get screen dimensions and set appropriate size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Set dialog size based on screen size
        if screen_width <= 800:
            dialog_width = min(380, screen_width - 40)
            dialog_height = min(450, screen_height - 80)
        else:
            dialog_width = 400
            dialog_height = 500
            
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog on screen
        x = (screen_width - dialog_width) // 2
        y = max(10, (screen_height - dialog_height) // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Make dialog resizable and add scrolling if needed
        self.dialog.resizable(True, True)
        self.dialog.minsize(300, 350)
        
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Event title
        ttk.Label(main_frame, text="Event Title:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.title_var = tk.StringVar(value=self.event.get('title', '') if self.event else '')
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, font=('Arial', 12))
        self.title_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Date
        ttk.Label(main_frame, text="Date:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        event_date = datetime.datetime.fromisoformat(self.event.get('date')) if self.event and 'date' in self.event else datetime.datetime.combine(self.date, datetime.time())
        
        self.date_var = tk.StringVar(value=event_date.strftime('%Y-%m-%d'))
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, font=('Arial', 12))
        self.date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Time
        ttk.Label(main_frame, text="Start Time:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.time_var = tk.StringVar(value=event_date.strftime('%H:%M') if self.event else '09:00')
        self.time_entry = ttk.Entry(time_frame, textvariable=self.time_var, font=('Arial', 12))
        self.time_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Duration
        ttk.Label(main_frame, text="Duration (minutes):", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.duration_var = tk.StringVar(value=str(self.event.get('duration', 60)) if self.event else '60')
        self.duration_entry = ttk.Entry(main_frame, textvariable=self.duration_var, font=('Arial', 12))
        self.duration_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Description
        ttk.Label(main_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.description_text = tk.Text(main_frame, height=6, font=('Arial', 11))
        self.description_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        if self.event and 'description' in self.event:
            self.description_text.insert('1.0', self.event['description'])
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", command=self.save_event).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        
        if self.event:
            ttk.Button(button_frame, text="Delete", command=self.delete_event).pack(side=tk.RIGHT)
        
        # Focus on title entry
        self.title_entry.focus()
        
    def save_event(self):
        """Save the event"""
        try:
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Error", "Please enter a title for the event")
                return
                
            date_str = self.date_var.get()
            time_str = self.time_var.get()
            duration_str = self.duration_var.get()
            description = self.description_text.get('1.0', tk.END).strip()
            
            # Validate inputs
            event_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            event_time = datetime.datetime.strptime(time_str, '%H:%M').time()
            duration = int(duration_str)
            
            # Create event dictionary
            event_dict = {
                'title': title,
                'date': datetime.datetime.combine(event_date, event_time).isoformat(),
                'duration': duration,
                'description': description
            }
            
            if self.event:
                # Update existing event
                # Find the event in the calendar
                old_date = datetime.datetime.fromisoformat(self.event['date']).date()
                for i, stored_event in enumerate(self.calendar_app.events.get(old_date.isoformat(), [])):
                    if stored_event == self.event:
                        # Remove from old date if date changed
                        if old_date != event_date:
                            self.calendar_app.remove_event(old_date, i)
                            self.calendar_app.add_event(event_date, event_dict)
                        else:
                            self.calendar_app.update_event(old_date, i, event_dict)
                        break
            else:
                # Add new event
                self.calendar_app.add_event(event_date, event_dict)
                
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save event: {str(e)}")
            
    def delete_event(self):
        """Delete the current event"""
        if messagebox.askyesno("Delete Event", "Are you sure you want to delete this event?"):
            event_date = datetime.datetime.fromisoformat(self.event['date']).date()
            for i, stored_event in enumerate(self.calendar_app.events.get(event_date.isoformat(), [])):
                if stored_event == self.event:
                    self.calendar_app.remove_event(event_date, i)
                    break
            self.dialog.destroy()
            
    def cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()


class EventListDialog:
    """Dialog for listing events"""
    def __init__(self, parent, calendar_app, date=None):
        self.parent = parent
        self.calendar_app = calendar_app
        self.filter_date = date
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the event list dialog"""
        self.dialog = tk.Toplevel(self.parent)
        title = f"Events for {self.filter_date.strftime('%B %d, %Y')}" if self.filter_date else "All Events"
        self.dialog.title(title)
        
        # Get screen dimensions and set appropriate size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Set dialog size based on screen size
        if screen_width <= 800:
            dialog_width = min(580, screen_width - 40)
            dialog_height = min(400, screen_height - 80)
        else:
            dialog_width = 600
            dialog_height = 500
            
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog on screen
        x = (screen_width - dialog_width) // 2
        y = max(10, (screen_height - dialog_height) // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        self.dialog.minsize(400, 300)
        
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for events
        self.tree = ttk.Treeview(main_frame, columns=('Date', 'Time', 'Duration', 'Description'), show='tree headings')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure columns
        self.tree.heading('#0', text='Title')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Time', text='Time')
        self.tree.heading('Duration', text='Duration')
        self.tree.heading('Description', text='Description')
        
        self.tree.column('#0', width=200)
        self.tree.column('Date', width=100)
        self.tree.column('Time', width=80)
        self.tree.column('Duration', width=80)
        self.tree.column('Description', width=200)
        
        # Populate events
        self.populate_events()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Edit", command=self.edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', lambda e: self.edit_selected())
        
    def populate_events(self):
        """Populate the events list"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get events to display
        events_to_show = []
        for date_str, events in self.calendar_app.events.items():
            event_date = datetime.datetime.fromisoformat(date_str).date()
            if not self.filter_date or event_date == self.filter_date:
                for event in events:
                    events_to_show.append((date_str, event))
                    
        # Sort by date and time
        events_to_show.sort(key=lambda x: x[1]['date'])
        
        # Add to treeview
        for date_str, event in events_to_show:
            event_datetime = datetime.datetime.fromisoformat(event['date'])
            date_display = event_datetime.strftime('%Y-%m-%d')
            time_display = event_datetime.strftime('%H:%M')
            duration_display = f"{event['duration']} min"
            description = event['description'][:50] + "..." if len(event['description']) > 50 else event['description']
            
            item_id = self.tree.insert('', 'end', text=event['title'], 
                                     values=(date_display, time_display, duration_display, description))
            
            # Store the original event data for editing
            self.tree.set(item_id, 'event_data', f"{date_str}|{self.calendar_app.events[date_str].index(event)}")
            
    def edit_selected(self):
        """Edit the selected event"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an event to edit")
            return
            
        item = selected[0]
        event_data = self.tree.set(item, 'event_data')
        date_str, event_index = event_data.split('|')
        event_index = int(event_index)
        
        event = self.calendar_app.events[date_str][event_index]
        event_date = datetime.datetime.fromisoformat(event['date']).date()
        
        EventDialog(self.dialog, self.calendar_app, event=event, date=event_date)
        
        # Refresh the list after potential changes
        self.dialog.after(100, self.populate_events)
        
    def delete_selected(self):
        """Delete the selected event"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an event to delete")
            return
            
        if not messagebox.askyesno("Delete Event", "Are you sure you want to delete the selected event?"):
            return
            
        item = selected[0]
        event_data = self.tree.set(item, 'event_data')
        date_str, event_index = event_data.split('|')
        event_index = int(event_index)
        
        event_date = datetime.datetime.fromisoformat(date_str).date()
        self.calendar_app.remove_event(event_date, event_index)
        
        # Refresh the list
        self.populate_events()


class SettingsDialog:
    """Settings configuration dialog"""
    def __init__(self, parent, calendar_app):
        self.parent = parent
        self.calendar_app = calendar_app
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the settings dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        
        # Get screen dimensions and set appropriate size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Set dialog size based on screen size
        if screen_width <= 800:
            dialog_width = min(380, screen_width - 40)
            dialog_height = min(280, screen_height - 80)
        else:
            dialog_width = 400
            dialog_height = 300
            
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog on screen
        x = (screen_width - dialog_width) // 2
        y = max(10, (screen_height - dialog_height) // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        self.dialog.minsize(350, 250)
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Week start setting
        self.start_monday_var = tk.BooleanVar(value=self.calendar_app.config.get('start_week_monday', True))
        ttk.Checkbutton(main_frame, text="Start week on Monday", 
                       variable=self.start_monday_var).pack(anchor=tk.W, pady=5)
        
        # Backup setting
        self.backup_var = tk.BooleanVar(value=self.calendar_app.config.get('backup_enabled', True))
        ttk.Checkbutton(main_frame, text="Enable automatic backups", 
                       variable=self.backup_var).pack(anchor=tk.W, pady=5)
        
        # Default event duration
        ttk.Label(main_frame, text="Default event duration (minutes):").pack(anchor=tk.W, pady=(10, 0))
        self.duration_var = tk.StringVar(value=str(self.calendar_app.config.get('default_event_duration', 60)))
        ttk.Entry(main_frame, textvariable=self.duration_var).pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_defaults).pack(side=tk.RIGHT)
        
    def save_settings(self):
        """Save the settings"""
        try:
            self.calendar_app.config['start_week_monday'] = self.start_monday_var.get()
            self.calendar_app.config['backup_enabled'] = self.backup_var.get()
            self.calendar_app.config['default_event_duration'] = int(self.duration_var.get())
            
            self.calendar_app.save_config()
            self.calendar_app.update_calendar()
            
            messagebox.showinfo("Settings", "Settings saved successfully!")
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid duration value. Please enter a number.")
            
    def reset_defaults(self):
        """Reset to default settings"""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            self.calendar_app.config = self.calendar_app.default_config.copy()
            self.calendar_app.save_config()
            self.calendar_app.update_calendar()
            
            messagebox.showinfo("Settings", "Settings reset to defaults!")
            self.dialog.destroy()


class DailyTasksDialog:
    """Dialog for managing daily tasks and checklists"""
    def __init__(self, parent, calendar_app, date):
        self.parent = parent
        self.calendar_app = calendar_app
        self.date = date
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the daily tasks dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Daily Tasks - {self.date.strftime('%A, %B %d, %Y')}")
        
        # Get screen dimensions and set appropriate size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Set dialog size based on screen size
        if screen_width <= 800:
            dialog_width = min(580, screen_width - 40)
            dialog_height = min(450, screen_height - 80)
        else:
            dialog_width = 700
            dialog_height = 600
            
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog on screen
        x = (screen_width - dialog_width) // 2
        y = max(10, (screen_height - dialog_height) // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        self.dialog.minsize(400, 350)
        
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = tk.Label(
            main_frame, 
            text=f"Tasks for {self.date.strftime('%A, %B %d, %Y')}", 
            font=('Arial', 14, 'bold')
        )
        header_label.pack(pady=(0, 10))
        
        # Get tasks for this date
        daily_tasks = self.calendar_app.get_tasks_for_date(self.date)
        
        # Create notebook for different classes
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.class_frames = {}
        self.task_vars = {}
        
        # If no classes exist, show message
        if not self.calendar_app.class_templates:
            no_classes_frame = ttk.Frame(self.notebook)
            self.notebook.add(no_classes_frame, text="No Classes")
            
            message_label = tk.Label(
                no_classes_frame,
                text="No classes found in classes.txt file.\nAdd your classes to the classes.txt file and click 'Reload Classes' on the main screen.",
                font=('Arial', 12),
                justify=tk.CENTER
            )
            message_label.pack(expand=True)
        else:
            # Create tab for each class
            for class_name in sorted(self.calendar_app.class_templates.keys()):
                self.create_class_tab(class_name, daily_tasks.get(class_name, []))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame, 
            text="Reload Classes", 
            command=self.reload_classes
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame, 
            text="Reset Today's Tasks", 
            command=self.reset_tasks
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame, 
            text="Close", 
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
    def create_class_tab(self, class_name, tasks):
        """Create a tab for a specific class"""
        # Create frame for this class
        class_frame = ttk.Frame(self.notebook)
        self.notebook.add(class_frame, text=class_name)
        
        # Create scrollable frame
        canvas = tk.Canvas(class_frame)
        scrollbar = ttk.Scrollbar(class_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.class_frames[class_name] = scrollable_frame
        self.task_vars[class_name] = []
        
        # Add tasks for this class
        for i, task in enumerate(tasks):
            self.create_task_widget(class_name, i, task, scrollable_frame)
        
        # Add button to add new task
        add_task_btn = tk.Button(
            scrollable_frame,
            text="+ Add Task for Today",
            command=lambda cn=class_name: self.add_daily_task(cn),
            bg='lightgreen',
            font=('Arial', 10)
        )
        add_task_btn.pack(fill=tk.X, pady=(10, 0))
        
    def create_task_widget(self, class_name, task_index, task, parent):
        """Create a widget for a single task"""
        task_frame = ttk.Frame(parent)
        task_frame.pack(fill=tk.X, pady=2)
        
        # Checkbox for completion
        var = tk.BooleanVar(value=task.get('completed', False))
        self.task_vars[class_name].append(var)
        
        checkbox = tk.Checkbutton(
            task_frame,
            text=task['title'],
            variable=var,
            font=('Arial', 11),
            command=lambda: self.toggle_task_completion(class_name, task_index, var.get())
        )
        checkbox.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor='w')
        
        # Priority indicator
        if task.get('priority', 'medium') == 'high':
            priority_label = tk.Label(task_frame, text="!", fg='red', font=('Arial', 12, 'bold'))
            priority_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Description tooltip (if exists)
        if task.get('description'):
            def show_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = tk.Label(
                    tooltip, 
                    text=task['description'], 
                    background='lightyellow',
                    relief='solid',
                    borderwidth=1,
                    font=('Arial', 9)
                )
                label.pack()
                
                def hide_tooltip():
                    tooltip.destroy()
                
                tooltip.after(3000, hide_tooltip)  # Hide after 3 seconds
            
            checkbox.bind("<Enter>", show_tooltip)
            
    def toggle_task_completion(self, class_name, task_index, completed):
        """Toggle task completion status"""
        self.calendar_app.update_task_completion(self.date, class_name, task_index, completed)
        
    def add_daily_task(self, class_name):
        """Add a new task for today only"""
        title = simpledialog.askstring("New Task", f"Enter task title for {class_name}:")
        if title:
            description = simpledialog.askstring("Task Description", "Enter description (optional):", initialvalue="")
            
            new_task = {
                'title': title,
                'description': description or '',
                'priority': 'medium',
                'completed': False,
                'date_created': self.date.isoformat(),
                'is_daily_only': True  # Mark as daily-only task
            }
            
            # Add to today's tasks
            date_str = self.date.isoformat()
            if date_str not in self.calendar_app.daily_tasks:
                self.calendar_app.daily_tasks[date_str] = {}
            if class_name not in self.calendar_app.daily_tasks[date_str]:
                self.calendar_app.daily_tasks[date_str][class_name] = []
                
            self.calendar_app.daily_tasks[date_str][class_name].append(new_task)
            self.calendar_app.save_tasks()
            
            # Refresh dialog
            self.dialog.destroy()
            DailyTasksDialog(self.parent, self.calendar_app, self.date)
            
    def reset_tasks(self):
        """Reset all tasks for today"""
        if messagebox.askyesno("Reset Tasks", "Reset all tasks for today? This will mark all tasks as incomplete."):
            date_str = self.date.isoformat()
            if date_str in self.calendar_app.daily_tasks:
                for class_name in self.calendar_app.daily_tasks[date_str]:
                    for task in self.calendar_app.daily_tasks[date_str][class_name]:
                        task['completed'] = False
                        
                self.calendar_app.save_tasks()
                self.calendar_app.update_calendar()
                
                # Refresh dialog
                self.dialog.destroy()
                DailyTasksDialog(self.parent, self.calendar_app, self.date)
                
    def reload_classes(self):
        """Reload classes from classes.txt file"""
        self.calendar_app.reload_class_templates()
        # Refresh dialog to show new classes
        self.dialog.destroy()
        DailyTasksDialog(self.parent, self.calendar_app, self.date)


class ClassManagementDialog:
    """Dialog for managing class templates and tasks"""
    def __init__(self, parent, calendar_app):
        self.parent = parent
        self.calendar_app = calendar_app
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the class management dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Manage Classes and Tasks")
        
        # Get screen dimensions and set appropriate size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Set dialog size based on screen size
        if screen_width <= 800:
            dialog_width = min(580, screen_width - 40)
            dialog_height = min(500, screen_height - 80)
        else:
            dialog_width = 800
            dialog_height = 700
            
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog on screen
        x = (screen_width - dialog_width) // 2
        y = max(10, (screen_height - dialog_height) // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        self.dialog.minsize(500, 400)
        
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = tk.Label(
            main_frame, 
            text="Class Management", 
            font=('Arial', 14, 'bold')
        )
        header_label.pack(pady=(0, 10))
        
        # Create paned window for classes and tasks
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left frame: Classes
        classes_frame = ttk.LabelFrame(paned_window, text="Classes", padding="10")
        paned_window.add(classes_frame, weight=1)
        
        # Class listbox
        self.classes_listbox = tk.Listbox(classes_frame, font=('Arial', 11))
        self.classes_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.classes_listbox.bind('<<ListboxSelect>>', self.on_class_select)
        
        # Class buttons
        class_buttons_frame = ttk.Frame(classes_frame)
        class_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            class_buttons_frame, 
            text="Add Class", 
            command=self.add_class
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            class_buttons_frame, 
            text="Remove Class", 
            command=self.remove_class
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            class_buttons_frame, 
            text="Rename Class", 
            command=self.rename_class
        ).pack(side=tk.LEFT)
        
        # Right frame: Tasks for selected class
        tasks_frame = ttk.LabelFrame(paned_window, text="Default Tasks", padding="10")
        paned_window.add(tasks_frame, weight=2)
        
        # Tasks listbox with scrollbar
        tasks_list_frame = ttk.Frame(tasks_frame)
        tasks_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tasks_listbox = tk.Listbox(tasks_list_frame, font=('Arial', 10))
        tasks_scrollbar = ttk.Scrollbar(tasks_list_frame, orient="vertical", command=self.tasks_listbox.yview)
        self.tasks_listbox.configure(yscrollcommand=tasks_scrollbar.set)
        
        self.tasks_listbox.pack(side="left", fill="both", expand=True)
        tasks_scrollbar.pack(side="right", fill="y")
        
        # Task buttons
        task_buttons_frame = ttk.Frame(tasks_frame)
        task_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            task_buttons_frame, 
            text="Add Task", 
            command=self.add_task
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            task_buttons_frame, 
            text="Edit Task", 
            command=self.edit_task
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            task_buttons_frame, 
            text="Remove Task", 
            command=self.remove_task
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            task_buttons_frame, 
            text="Move Up", 
            command=lambda: self.move_task(-1)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            task_buttons_frame, 
            text="Move Down", 
            command=lambda: self.move_task(1)
        ).pack(side=tk.LEFT)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(
            bottom_frame, 
            text="Import Example Classes", 
            command=self.import_examples
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            bottom_frame, 
            text="Save & Close", 
            command=self.save_and_close
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            bottom_frame, 
            text="Cancel", 
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
        # Load classes
        self.refresh_classes()
        
    def refresh_classes(self):
        """Refresh the classes listbox"""
        self.classes_listbox.delete(0, tk.END)
        for class_name in sorted(self.calendar_app.class_templates.keys()):
            self.classes_listbox.insert(tk.END, class_name)
            
    def refresh_tasks(self, class_name):
        """Refresh the tasks listbox for selected class"""
        self.tasks_listbox.delete(0, tk.END)
        if class_name in self.calendar_app.class_templates:
            for task in self.calendar_app.class_templates[class_name]:
                priority_indicator = "! " if task.get('priority') == 'high' else ""
                task_text = f"{priority_indicator}{task['title']}"
                if task.get('description'):
                    task_text += f" - {task['description'][:30]}..."
                self.tasks_listbox.insert(tk.END, task_text)
                
    def on_class_select(self, event):
        """Handle class selection"""
        selection = self.classes_listbox.curselection()
        if selection:
            class_name = self.classes_listbox.get(selection[0])
            self.refresh_tasks(class_name)
            
    def add_class(self):
        """Add a new class"""
        class_name = simpledialog.askstring("New Class", "Enter class name:")
        if class_name and class_name not in self.calendar_app.class_templates:
            self.calendar_app.class_templates[class_name] = []
            self.refresh_classes()
            # Select the new class
            items = self.classes_listbox.get(0, tk.END)
            if class_name in items:
                self.classes_listbox.selection_set(items.index(class_name))
                self.refresh_tasks(class_name)
        elif class_name in self.calendar_app.class_templates:
            messagebox.showwarning("Duplicate Class", "A class with this name already exists.")
            
    def remove_class(self):
        """Remove selected class"""
        selection = self.classes_listbox.curselection()
        if selection:
            class_name = self.classes_listbox.get(selection[0])
            if messagebox.askyesno("Remove Class", f"Remove class '{class_name}' and all its tasks?"):
                del self.calendar_app.class_templates[class_name]
                # Also remove from daily tasks
                for date_str in list(self.calendar_app.daily_tasks.keys()):
                    if class_name in self.calendar_app.daily_tasks[date_str]:
                        del self.calendar_app.daily_tasks[date_str][class_name]
                        # Remove date entry if no classes left
                        if not self.calendar_app.daily_tasks[date_str]:
                            del self.calendar_app.daily_tasks[date_str]
                            
                self.refresh_classes()
                self.tasks_listbox.delete(0, tk.END)
        else:
            messagebox.showwarning("No Selection", "Please select a class to remove.")
            
    def rename_class(self):
        """Rename selected class"""
        selection = self.classes_listbox.curselection()
        if selection:
            old_name = self.classes_listbox.get(selection[0])
            new_name = simpledialog.askstring("Rename Class", f"Enter new name for '{old_name}':", initialvalue=old_name)
            
            if new_name and new_name != old_name:
                if new_name not in self.calendar_app.class_templates:
                    # Update class templates
                    self.calendar_app.class_templates[new_name] = self.calendar_app.class_templates[old_name]
                    del self.calendar_app.class_templates[old_name]
                    
                    # Update daily tasks
                    for date_str in self.calendar_app.daily_tasks:
                        if old_name in self.calendar_app.daily_tasks[date_str]:
                            self.calendar_app.daily_tasks[date_str][new_name] = self.calendar_app.daily_tasks[date_str][old_name]
                            del self.calendar_app.daily_tasks[date_str][old_name]
                    
                    self.refresh_classes()
                    # Select the renamed class
                    items = self.classes_listbox.get(0, tk.END)
                    if new_name in items:
                        self.classes_listbox.selection_set(items.index(new_name))
                        self.refresh_tasks(new_name)
                else:
                    messagebox.showwarning("Duplicate Name", "A class with this name already exists.")
        else:
            messagebox.showwarning("No Selection", "Please select a class to rename.")
            
    def add_task(self):
        """Add a new task to selected class"""
        selection = self.classes_listbox.curselection()
        if selection:
            class_name = self.classes_listbox.get(selection[0])
            TaskEditDialog(self.dialog, self.calendar_app, class_name, callback=self.on_task_modified)
        else:
            messagebox.showwarning("No Selection", "Please select a class first.")
            
    def edit_task(self):
        """Edit selected task"""
        class_selection = self.classes_listbox.curselection()
        task_selection = self.tasks_listbox.curselection()
        
        if class_selection and task_selection:
            class_name = self.classes_listbox.get(class_selection[0])
            task_index = task_selection[0]
            TaskEditDialog(
                self.dialog, 
                self.calendar_app, 
                class_name, 
                task_index=task_index, 
                callback=self.on_task_modified
            )
        else:
            messagebox.showwarning("No Selection", "Please select a class and task to edit.")
            
    def remove_task(self):
        """Remove selected task"""
        class_selection = self.classes_listbox.curselection()
        task_selection = self.tasks_listbox.curselection()
        
        if class_selection and task_selection:
            class_name = self.classes_listbox.get(class_selection[0])
            task_index = task_selection[0]
            
            task_title = self.calendar_app.class_templates[class_name][task_index]['title']
            if messagebox.askyesno("Remove Task", f"Remove task '{task_title}'?"):
                del self.calendar_app.class_templates[class_name][task_index]
                self.refresh_tasks(class_name)
        else:
            messagebox.showwarning("No Selection", "Please select a task to remove.")
            
    def move_task(self, direction):
        """Move selected task up or down"""
        class_selection = self.classes_listbox.curselection()
        task_selection = self.tasks_listbox.curselection()
        
        if class_selection and task_selection:
            class_name = self.classes_listbox.get(class_selection[0])
            task_index = task_selection[0]
            tasks = self.calendar_app.class_templates[class_name]
            
            new_index = task_index + direction
            if 0 <= new_index < len(tasks):
                # Swap tasks
                tasks[task_index], tasks[new_index] = tasks[new_index], tasks[task_index]
                self.refresh_tasks(class_name)
                self.tasks_listbox.selection_set(new_index)
        else:
            messagebox.showwarning("No Selection", "Please select a task to move.")
            
    def on_task_modified(self):
        """Callback when a task is modified"""
        class_selection = self.classes_listbox.curselection()
        if class_selection:
            class_name = self.classes_listbox.get(class_selection[0])
            self.refresh_tasks(class_name)
            
    def import_examples(self):
        """Import example classes and tasks"""
        if messagebox.askyesno("Import Examples", "Import example classes? This will add sample classes and tasks."):
            examples = {
                "Mathematics": [
                    {"title": "Review previous lesson notes", "description": "Go through yesterday's notes and examples", "priority": "medium"},
                    {"title": "Complete homework assignment", "description": "Solve all assigned problems", "priority": "high"},
                    {"title": "Practice problems", "description": "Extra practice from textbook", "priority": "low"},
                    {"title": "Prepare for next class", "description": "Read upcoming chapter", "priority": "medium"}
                ],
                "Science": [
                    {"title": "Review lab results", "description": "Analyze data from last experiment", "priority": "medium"},
                    {"title": "Read assigned chapter", "description": "Read and take notes on new material", "priority": "high"},
                    {"title": "Complete lab report", "description": "Write up experiment findings", "priority": "high"},
                    {"title": "Study for quiz", "description": "Review notes and practice questions", "priority": "medium"}
                ],
                "English": [
                    {"title": "Read assigned pages", "description": "Read daily reading assignment", "priority": "high"},
                    {"title": "Vocabulary practice", "description": "Review and practice new words", "priority": "medium"},
                    {"title": "Work on essay", "description": "Continue writing current assignment", "priority": "medium"},
                    {"title": "Journal entry", "description": "Write daily reflection", "priority": "low"}
                ],
                "History": [
                    {"title": "Read textbook chapter", "description": "Read assigned history material", "priority": "high"},
                    {"title": "Review timeline notes", "description": "Go over important dates and events", "priority": "medium"},
                    {"title": "Watch documentary", "description": "Educational video on current topic", "priority": "low"},
                    {"title": "Research project work", "description": "Continue research for term project", "priority": "medium"}
                ]
            }
            
            # Add examples that don't already exist
            for class_name, tasks in examples.items():
                if class_name not in self.calendar_app.class_templates:
                    self.calendar_app.class_templates[class_name] = tasks
                    
            self.refresh_classes()
            messagebox.showinfo("Import Complete", "Example classes have been imported!")
            
    def save_and_close(self):
        """Save changes and close dialog"""
        self.calendar_app.save_tasks()
        self.dialog.destroy()


class TaskEditDialog:
    """Dialog for editing individual tasks"""
    def __init__(self, parent, calendar_app, class_name, task_index=None, callback=None):
        self.parent = parent
        self.calendar_app = calendar_app
        self.class_name = class_name
        self.task_index = task_index
        self.callback = callback
        
        self.is_edit = task_index is not None
        self.task = (self.calendar_app.class_templates[class_name][task_index] 
                    if self.is_edit else 
                    {"title": "", "description": "", "priority": "medium"})
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create the task edit dialog"""
        self.dialog = tk.Toplevel(self.parent)
        title = f"Edit Task" if self.is_edit else f"New Task for {self.class_name}"
        self.dialog.title(title)
        
        # Get screen dimensions and set appropriate size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Set dialog size based on screen size
        if screen_width <= 800:
            dialog_width = min(380, screen_width - 40)
            dialog_height = min(280, screen_height - 80)
        else:
            dialog_width = 400
            dialog_height = 300
            
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog on screen
        x = (screen_width - dialog_width) // 2
        y = max(10, (screen_height - dialog_height) // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        self.dialog.minsize(350, 250)
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Task title
        ttk.Label(main_frame, text="Task Title:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.title_var = tk.StringVar(value=self.task.get('title', ''))
        title_entry = ttk.Entry(main_frame, textvariable=self.title_var, font=('Arial', 12))
        title_entry.pack(fill=tk.X, pady=(0, 10))
        title_entry.focus()
        
        # Task description
        ttk.Label(main_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.description_text = tk.Text(main_frame, height=4, font=('Arial', 11))
        self.description_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.description_text.insert('1.0', self.task.get('description', ''))
        
        # Priority
        ttk.Label(main_frame, text="Priority:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.priority_var = tk.StringVar(value=self.task.get('priority', 'medium'))
        priority_frame = ttk.Frame(main_frame)
        priority_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(priority_frame, text="Low", variable=self.priority_var, value="low").pack(side=tk.LEFT)
        ttk.Radiobutton(priority_frame, text="Medium", variable=self.priority_var, value="medium").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(priority_frame, text="High", variable=self.priority_var, value="high").pack(side=tk.LEFT, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", command=self.save_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
        
    def save_task(self):
        """Save the task"""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Please enter a task title")
            return
            
        description = self.description_text.get('1.0', tk.END).strip()
        priority = self.priority_var.get()
        
        task_data = {
            'title': title,
            'description': description,
            'priority': priority
        }
        
        if self.is_edit:
            # Update existing task
            self.calendar_app.class_templates[self.class_name][self.task_index] = task_data
        else:
            # Add new task
            self.calendar_app.class_templates[self.class_name].append(task_data)
            
        if self.callback:
            self.callback()
            
        self.dialog.destroy()


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = TouchCalendar(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.save_events()
        app.save_tasks()
        app.save_config()
        

if __name__ == "__main__":
    main()
