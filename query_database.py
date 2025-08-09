#!/usr/bin/env python3
"""
Query script for the SmartMeter SQLite database
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta

def connect_database(database_file="/home/pi/smartmeter_data/smartmeter.db"):
    """Connect to the database and return connection"""
    try:
        conn = sqlite3.connect(database_file)
        conn.row_factory = sqlite3.Row  # This allows column access by name
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_current_reading():
    """Get the current/latest reading"""
    conn = connect_database()
    if not conn:
        return None
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM current_readings ORDER BY timestamp DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

def get_history(hours=24):
    """Get historical data for the specified number of hours"""
    conn = connect_database()
    if not conn:
        return []
    
    cursor = conn.cursor()
    threshold_time = datetime.now() - timedelta(hours=hours)
    cursor.execute('''
        SELECT * FROM history 
        WHERE timestamp >= ? 
        ORDER BY timestamp ASC
    ''', (threshold_time,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def export_current_as_json():
    """Export current reading in original JSON format"""
    current = get_current_reading()
    if not current:
        return None
    
    json_current = {
        "Datum": {"value": current["timestamp"]},
        "Zaehlernummer": {"value": current["meter_number"]},
        "Logical Device Name": {"value": current["logical_device_name"]},
        "Wirkenergie A+": {"value": current["wirkenergie_bezug"], "unit": "Wh"},
        "Wirkenergie A-": {"value": current["wirkenergie_lieferung"], "unit": "Wh"},
        "Wirkleistung P+": {"value": current["wirkleistung_bezug"], "unit": "W"},
        "Wirkleistung P-": {"value": current["wirkleistung_lieferung"], "unit": "W"},
        "Blindenergie Q+": {"value": current["blindenergie_bezug"], "unit": "varh"},
        "Blindenergie Q-": {"value": current["blindenergie_lieferung"], "unit": "varh"},
        "Spannung L1": {"value": current["spannung_l1"], "unit": "V"},
        "Spannung L2": {"value": current["spannung_l2"], "unit": "V"},
        "Spannung L3": {"value": current["spannung_l3"], "unit": "V"},
        "Strom L1": {"value": current["strom_l1"], "unit": "A"},
        "Strom L2": {"value": current["strom_l2"], "unit": "A"},
        "Strom L3": {"value": current["strom_l3"], "unit": "A"},
        "Leistungsfaktor": {"value": current["leistungsfaktor"]}
    }
    
    return json_current

def export_history_as_json(hours=24):
    """Export historical data in original JSON format"""
    current = get_current_reading()
    history_data = get_history(hours)
    
    if not current:
        return None
    
    json_history = {
        "Wirkenergie A+ last": current["wirkenergie_bezug"],
        "Wirkenergie A- last": current["wirkenergie_lieferung"], 
        "Datum": current["timestamp"],
        "data": []
    }
    
    for entry in history_data:
        json_history["data"].append({
            "Datum": entry["timestamp"],
            "Wirkenergie Bezug Diff": entry["wirkenergie_bezug_diff"],
            "Wirkenergie Lieferung Diff": entry["wirkenergie_lieferung_diff"]
        })
    
    return json_history

def print_current_summary():
    """Print a summary of current readings"""
    current = get_current_reading()
    if not current:
        print("No current reading found in database")
        return
    
    print("=== Current Smart Meter Reading ===")
    print(f"Timestamp: {current['timestamp']}")
    print(f"Meter Number: {current['meter_number']}")
    print(f"Energy Consumption (A+): {current['wirkenergie_bezug']} Wh")
    print(f"Energy Production (A-): {current['wirkenergie_lieferung']} Wh")
    print(f"Current Power Consumption: {current['wirkleistung_bezug']} W")
    print(f"Current Power Production: {current['wirkleistung_lieferung']} W")
    print(f"Voltage L1/L2/L3: {current['spannung_l1']}/{current['spannung_l2']}/{current['spannung_l3']} V")
    print(f"Current L1/L2/L3: {current['strom_l1']}/{current['strom_l2']}/{current['strom_l3']} A")
    print(f"Power Factor: {current['leistungsfaktor']}")

def print_history_summary(hours=24):
    """Print a summary of historical data"""
    history = get_history(hours)
    if not history:
        print(f"No history data found for the last {hours} hours")
        return
    
    print(f"=== History Summary (Last {hours} hours) ===")
    print(f"Number of entries: {len(history)}")
    
    if history:
        latest = history[-1]
        print(f"Latest entry: {latest['timestamp']}")
        print(f"Latest consumption diff: {latest['wirkenergie_bezug_diff']} W")
        print(f"Latest production diff: {latest['wirkenergie_lieferung_diff']} W")
        
        # Calculate averages
        avg_consumption = sum(entry['wirkenergie_bezug_diff'] or 0 for entry in history) / len(history)
        avg_production = sum(entry['wirkenergie_lieferung_diff'] or 0 for entry in history) / len(history)
        print(f"Average consumption: {avg_consumption:.2f} W")
        print(f"Average production: {avg_production:.2f} W")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 query_database.py <command> [options]")
        print("Commands:")
        print("  current         - Show current reading summary")
        print("  history [hours] - Show history summary (default: 24 hours)")
        print("  export-current  - Export current reading as JSON")
        print("  export-history [hours] - Export history as JSON (default: 24 hours)")
        print("  raw-current     - Show raw current data")
        print("  raw-history [hours] - Show raw history data (default: 24 hours)")
        return
    
    command = sys.argv[1]
    
    if command == "current":
        print_current_summary()
    
    elif command == "history":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        print_history_summary(hours)
    
    elif command == "export-current":
        data = export_current_as_json()
        if data:
            print(json.dumps(data, indent=2, default=str))
        else:
            print("No current data found")
    
    elif command == "export-history":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        data = export_history_as_json(hours)
        if data:
            print(json.dumps(data, indent=2, default=str))
        else:
            print("No history data found")
    
    elif command == "raw-current":
        data = get_current_reading()
        if data:
            print(json.dumps(data, indent=2, default=str))
        else:
            print("No current data found")
    
    elif command == "raw-history":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        data = get_history(hours)
        if data:
            print(json.dumps(data, indent=2, default=str))
        else:
            print("No history data found")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
