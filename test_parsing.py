#!/usr/bin/env python3
"""
Test script for ICS import debugging
"""

# Test the class name parsing with your Fall 2025 titles
test_titles = [
    "Intro to Algs & Models of Comp ECE 374 BYA",
    "Applied Parallel Programming ECE 408 AL1", 
    "Ice Skating HK 104 A3",
    "Principles of Safe Autonomy ECE 484 AL1"
]

def parse_class_name(event_title):
    """Parse class name from various ICS event title formats"""
    if not event_title:
        return None
        
    title = event_title.strip()
    print(f"Parsing title: '{title}'")
    
    # Clean up HTML entities
    title = title.replace('&amp;', '&')
    
    import re
    
    # Pattern 1: Subject Name + Course Code + Section
    pattern1 = r'^(.+?)\s+([A-Z]{2,4}\s+\d{3})\s+[A-Z]{1,3}\d*$'
    match1 = re.match(pattern1, title)
    if match1:
        subject = match1.group(1).strip()
        course_code = match1.group(2).strip()
        result = f"{course_code} - {subject}"
        print(f"Pattern 1 match: '{result}'")
        return result
    
    print(f"No pattern matched for: '{title}'")
    return None

print("Testing class name parsing:")
print("=" * 50)

for title in test_titles:
    result = parse_class_name(title)
    print(f"'{title}' -> '{result}'")
    print()
