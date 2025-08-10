#!/usr/bin/env python3
"""
Query script for the SmartMeter SQLite database
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta

def connect_database(database_file="/ram/smartmeter.db"):
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
        earliest = history[0]
        print(f"Time range: {earliest['timestamp']} to {latest['timestamp']}")
        print(f"Latest energy consumption: {latest['wirkenergie_bezug']} Wh")
        print(f"Latest energy production: {latest['wirkenergie_lieferung']} Wh")
        
        if len(history) >= 2:
            # Calculate total energy change over the period
            total_consumption_change = latest['wirkenergie_bezug'] - earliest['wirkenergie_bezug']
            total_production_change = latest['wirkenergie_lieferung'] - earliest['wirkenergie_lieferung']
            
            # Calculate time span
            start_time = datetime.fromisoformat(earliest['timestamp'])
            end_time = datetime.fromisoformat(latest['timestamp'])
            time_span_hours = (end_time - start_time).total_seconds() / 3600
            
            if time_span_hours > 0:
                avg_consumption_power = total_consumption_change / time_span_hours
                avg_production_power = total_production_change / time_span_hours
                print(f"Average consumption over period: {avg_consumption_power:.2f} W")
                print(f"Average production over period: {avg_production_power:.2f} W")
                print(f"Total consumption change: {total_consumption_change:.2f} Wh")
                print(f"Total production change: {total_production_change:.2f} Wh")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 query_database.py <command> [options]")
        print("Commands:")
        print("  current         - Show current reading summary")
        print("  history [hours] - Show history summary (default: 24 hours)")
        print("  raw-current     - Show raw current data")
        print("  raw-history [hours] - Show raw history data (default: 24 hours)")
        return
    
    command = sys.argv[1]
    
    if command == "current":
        print_current_summary()
    
    elif command == "history":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        print_history_summary(hours)
    
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
