#!/usr/bin/env python3
"""
Migration script to convert existing JSON files to SQLite database
"""

import json
import sqlite3
import os
from datetime import datetime

def migrate_json_to_database():
    # Configuration (adjust paths as needed)
    current_file = "/home/pi/smartmeter_data/current.json"
    history_file = "/home/pi/smartmeter_data/history.json"
    database_file = "/home/pi/smartmeter_data/smartmeter.db"
    
    # Create database and tables
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    # Create current readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_readings (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            meter_number TEXT,
            logical_device_name TEXT,
            wirkenergie_bezug REAL,
            wirkenergie_lieferung REAL,
            wirkleistung_bezug REAL,
            wirkleistung_lieferung REAL,
            blindenergie_bezug REAL,
            blindenergie_lieferung REAL,
            spannung_l1 REAL,
            spannung_l2 REAL,
            spannung_l3 REAL,
            strom_l1 REAL,
            strom_l2 REAL,
            strom_l3 REAL,
            leistungsfaktor REAL
        )
    ''')
    
    # Create history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            wirkenergie_bezug_diff REAL,
            wirkenergie_lieferung_diff REAL,
            UNIQUE(timestamp)
        )
    ''')
    
    # Create index on timestamp for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)')
    
    # Migrate current.json if it exists
    if os.path.exists(current_file):
        print(f"Migrating {current_file}...")
        try:
            with open(current_file, 'r') as f:
                current_data = json.load(f)
            
            # Clear previous current reading
            cursor.execute('DELETE FROM current_readings')
            
            # Insert current reading
            cursor.execute('''
                INSERT INTO current_readings (
                    timestamp, meter_number, logical_device_name,
                    wirkenergie_bezug, wirkenergie_lieferung,
                    wirkleistung_bezug, wirkleistung_lieferung,
                    blindenergie_bezug, blindenergie_lieferung,
                    spannung_l1, spannung_l2, spannung_l3,
                    strom_l1, strom_l2, strom_l3, leistungsfaktor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_data.get("Datum", {}).get("value"),
                current_data.get("Zaehlernummer", {}).get("value"),
                current_data.get("Logical Device Name", {}).get("value"),
                current_data.get("Wirkenergie A+", {}).get("value"),
                current_data.get("Wirkenergie A-", {}).get("value"),
                current_data.get("Wirkleistung P+", {}).get("value"),
                current_data.get("Wirkleistung P-", {}).get("value"),
                current_data.get("Blindenergie Q+", {}).get("value"),
                current_data.get("Blindenergie Q-", {}).get("value"),
                current_data.get("Spannung L1", {}).get("value"),
                current_data.get("Spannung L2", {}).get("value"),
                current_data.get("Spannung L3", {}).get("value"),
                current_data.get("Strom L1", {}).get("value"),
                current_data.get("Strom L2", {}).get("value"),
                current_data.get("Strom L3", {}).get("value"),
                current_data.get("Leistungsfaktor", {}).get("value")
            ))
            print("Current data migrated successfully!")
            
        except Exception as e:
            print(f"Error migrating current.json: {e}")
    
    # Migrate history.json if it exists
    if os.path.exists(history_file):
        print(f"Migrating {history_file}...")
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
            
            # Insert history entries
            for entry in history_data.get("data", []):
                cursor.execute('''
                    INSERT OR REPLACE INTO history (timestamp, wirkenergie_bezug_diff, wirkenergie_lieferung_diff)
                    VALUES (?, ?, ?)
                ''', (
                    entry.get("Datum"),
                    entry.get("Wirkenergie Bezug Diff"),
                    entry.get("Wirkenergie Lieferung Diff")
                ))
            
            print(f"Migrated {len(history_data.get('data', []))} history entries!")
            
        except Exception as e:
            print(f"Error migrating history.json: {e}")
    
    conn.commit()
    conn.close()
    print(f"Migration completed! Database created at: {database_file}")

if __name__ == "__main__":
    migrate_json_to_database()
