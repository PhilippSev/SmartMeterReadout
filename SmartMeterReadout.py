#######################################
#
# SmartMeterReadout.py
#
# This script reads out the smart meter and stores it to json files that can be used by the webserver.
# More details can be found in my blog post: 
# https://projekte.philippseverin.at/2023/08/04/smartmeter-mit-raspberrypi-auslesen/
#
# Inspired by and based on:
# https://github.com/micronano0/RaspberryPi-Kaifa-SmartMeter-Reader/blob/main/kaifa_kundenschnittstelle_auslesen.py
#
#######################################

import serial
from Crypto.Cipher import AES
from enum import Enum
from datetime import datetime, timedelta
import json
import os
import sqlite3

#######################################
# Configuration

history_keep_hours = 24
hostory_update_minutes = 1
directory = "/home/pi/smartmeter_data"
database_file = "/home/pi/smartmeter_data/smartmeter.db"
serial_packet_bytes = 376

#######################################
# Enums and constants

units = {
    # byte  : unit
    0x1b : "W",
    0x1e : "Wh",
    0x20 : "varh",
    0x21 : "A",
    0x23 : "V",
}

class Type(Enum):
    Date = 0
    UInt16 = 1
    UInt32 = 2
    OctetString = 3

valueTuples = [
    # octetString,              , type,             name
    (b'\x00\x00\x01\x00\x00\xFF', Type.Date,        "Datum"),
    (b'\x00\x00\x60\x01\x00\xFF', Type.OctetString, "Zaehlernummer"),
    (b'\x00\x00\x2A\x00\x00\xFF', Type.OctetString, "Logical Device Name"),
    (b'\x01\x00\x01\x08\x00\xFF', Type.UInt32,      "Wirkenergie A+"), # Bezug
    (b'\x01\x00\x02\x08\x00\xFF', Type.UInt32,      "Wirkenergie A-"), # Lieferung
    (b'\x01\x00\x01\x07\x00\xFF', Type.UInt32,      "Wirkleistung P+"), # Bezug
    (b'\x01\x00\x02\x07\x00\xFF', Type.UInt32,      "Wirkleistung P-"), # Lieferung
    (b'\x01\x00\x03\x08\x00\xFF', Type.UInt32,      "Blindenergie Q+"), # Bezug
    (b'\x01\x00\x04\x08\x00\xFF', Type.UInt32,      "Blindenergie Q-"), # Lieferung
    (b'\x01\x00\x20\x07\x00\xFF', Type.UInt16,      "Spannung L1"),
    (b'\x01\x00\x34\x07\x00\xFF', Type.UInt16,      "Spannung L2"),
    (b'\x01\x00\x48\x07\x00\xFF', Type.UInt16,      "Spannung L3"),
    (b'\x01\x00\x1F\x07\x00\xFF', Type.UInt16,      "Strom L1"),
    (b'\x01\x00\x33\x07\x00\xFF', Type.UInt16,      "Strom L2"),
    (b'\x01\x00\x47\x07\x00\xFF', Type.UInt16,      "Strom L3"),
    (b'\x01\x00\x0D\x07\x00\xFF', Type.UInt16,      "Leistungsfaktor"),
]

mbus_start_bytes = b'\x68\xfa\xfa\x68'
mbus_stop_byte = b'\x16'
obis_offset =  6 + 1 # 6 bytes octetString id + 1 byte something unknown

#######################################
# Initialization

ser = serial.Serial("/dev/ttyS0", 
                    baudrate=2400, 
                    parity=serial.PARITY_NONE, 
                    stopbits=serial.STOPBITS_ONE, 
                    bytesize=serial.EIGHTBITS)

if not os.path.exists(directory):
    os.mkdir(directory, 0o777)

# Initialize database
def init_database():
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
    
    # Create history table - stores absolute energy values over time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            wirkenergie_bezug REAL,
            wirkenergie_lieferung REAL,
            UNIQUE(timestamp)
        )
    ''')
    
    # Remove the last_values table as it's no longer needed
    # cursor.execute('DROP TABLE IF EXISTS last_values')
    
    # Create index on timestamp for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)')
    
    conn.commit()
    conn.close()

init_database()

#######################################
# Functions

def synchronizeSerial():
    # recieve data
    # synchronization is done by trying to read data for a timeout of
    # 1 second. When nothing is read before the timeout is reached, 
    # the read happened during the wait time of the SmartMeter is
    # which only transmits data every 5 seconds.
    # after this is detected, the data frame can be read fully.
    ser.timeout = 1
    while True:
        data = ser.read(size=1)
        if len(data) == 0:
            ser.timeout = None
            break

def readPacket():
    while True:
        data = ser.read(size=serial_packet_bytes)

        # check if data is valid
        if len(data) != serial_packet_bytes:
            #raise Exception("Invalid data length")
            synchronizeSerial()
            continue
        elif data[0:4] != mbus_start_bytes:
            #raise Exception("Invalid start bytes")
            synchronizeSerial()
            continue
        elif data[-1:] != mbus_stop_byte:
            synchronizeSerial()
            continue
        return data

def readKey():
    # read key from file
    key_file = open("key.txt", "r")
    key_string = key_file.readline().strip()
    key_file.close()
    return bytes.fromhex(key_string)

def decrypt(data, key):
    msglen1 = int(hex(data[1]),16) # 1. FA - 250 Byte

    header1 = 27
    header2 = 9

    systitle = data[11:19] # System Title - 8 Bytes
    framecounter = data[23:27] # Frame Counter - 4 Bytes
    nonce = systitle + framecounter # iv ist 12 Bytes

    msg1 = data[header1:(6 + msglen1 - 2)]
    msglen2 = int(hex(data[msglen1 + 7]), 16)
    msg2 = data[msglen1 + 6 + header2:(msglen1 + 5 + 5 + msglen2)]

    cyphertext = msg1 + msg2

    cyphertext_bytes = bytes.fromhex(cyphertext.hex())
    cipher = AES.new(key, AES.MODE_GCM,  nonce)
    return cipher.decrypt(cyphertext_bytes)

def getValueLength(type, value_pos, bytes):
    if type == Type.UInt16:
        return (0, 2)
    elif type == Type.UInt32:
        return (0, 4)
    elif type == Type.OctetString:
        return (1, bytes[value_pos + obis_offset])
    elif type == Type.Date:
        return (1, bytes[value_pos + obis_offset])
    else:
        raise Exception("Unknown type")
    
def getValueConverted(type, bytes, value_pos, length):
    # read obis value bytes
    value_start = value_pos + obis_offset + length[0]
    value_end = value_pos + obis_offset + length[0] + length[1]
    value_bytes = bytes[value_start:value_end]

    value_converted = None
    value_unit = None

    if type == Type.UInt16 or type == Type.UInt32:
        # convert bytes to int
        value_int = int.from_bytes(value_bytes, byteorder='big', signed=False)
        # get scaling value
        value_scaling_raw = bytes[value_end + 3:value_end + 4]
        value_scaling = int.from_bytes(value_scaling_raw, byteorder='big', signed=True)
        # apply scaling
        value_converted = float(value_int) * pow(10.0, value_scaling)
        value_converted = round(value_converted, 2)
        # get unit if known
        value_unit_enum = bytes[value_end + 5]
        if value_unit_enum in units:
            value_unit = units[value_unit_enum]

    elif type == Type.OctetString:
        # convert bytes to string
        value_converted = value_bytes.decode("ascii")

    elif type == Type.Date:
        # convert bytes to datetime
        year = int.from_bytes(value_bytes[:2], byteorder='big', signed=False)
        month = int.from_bytes(value_bytes[2:3], byteorder='big', signed=False)
        day = int.from_bytes(value_bytes[3:4], byteorder='big', signed=False)
        hour = int.from_bytes(value_bytes[5:6], byteorder='big', signed=False)
        minute = int.from_bytes(value_bytes[6:7], byteorder='big', signed=False)
        second = int.from_bytes(value_bytes[7:8], byteorder='big', signed=False)
        value_converted = datetime(year,month,day,hour,minute,second)
    else:
        raise Exception("Unknown type")
    return (value_converted, value_unit)

def getJsonCurrent(plaintext):
    json_current = {}

    # read values from plaintext
    for value in valueTuples:
        value_pos = plaintext.find(value[0])
        if value_pos == -1: 
            # skipp value if not found
            continue 

        # get size of data type
        length = getValueLength(value[1], value_pos, plaintext)

        # convert obis value to usable value
        value_converted = getValueConverted(value[1], plaintext, value_pos, length)
        #print(value[2], value_converted)

        # store value as json
        json_inner = {}
        json_inner["value"] = value_converted[0]
        if value_converted[1] != None:
            json_inner["unit"] = value_converted[1]
        json_current[value[2]] = json_inner
    return json_current

def updateCurrentReading(json_current):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    # Clear previous current reading (keep only the latest)
    cursor.execute('DELETE FROM current_readings')
    
    # Insert new current reading
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
        json_current.get("Datum", {}).get("value"),
        json_current.get("Zaehlernummer", {}).get("value"),
        json_current.get("Logical Device Name", {}).get("value"),
        json_current.get("Wirkenergie A+", {}).get("value"),
        json_current.get("Wirkenergie A-", {}).get("value"),
        json_current.get("Wirkleistung P+", {}).get("value"),
        json_current.get("Wirkleistung P-", {}).get("value"),
        json_current.get("Blindenergie Q+", {}).get("value"),
        json_current.get("Blindenergie Q-", {}).get("value"),
        json_current.get("Spannung L1", {}).get("value"),
        json_current.get("Spannung L2", {}).get("value"),
        json_current.get("Spannung L3", {}).get("value"),
        json_current.get("Strom L1", {}).get("value"),
        json_current.get("Strom L2", {}).get("value"),
        json_current.get("Strom L3", {}).get("value"),
        json_current.get("Leistungsfaktor", {}).get("value")
    ))
    
    conn.commit()
    conn.close()

def updateHistory(json_current):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    current_timestamp = json_current["Datum"]["value"]
    
    try:
        # Check if we should add a new history entry (every minute)
        cursor.execute('''
            SELECT timestamp FROM history 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        last_entry = cursor.fetchone()
        
        if last_entry:
            last_timestamp = datetime.fromisoformat(last_entry[0])
            time_difference = current_timestamp - last_timestamp
            
            # Only update history every minute
            if time_difference < timedelta(minutes=hostory_update_minutes):
                conn.close()
                return
        
        # Insert new history entry with absolute energy values
        cursor.execute('''
            INSERT OR REPLACE INTO history (
                timestamp, 
                wirkenergie_bezug, 
                wirkenergie_lieferung
            ) VALUES (?, ?, ?)
        ''', (
            current_timestamp,
            json_current.get("Wirkenergie A+", {}).get("value"),
            json_current.get("Wirkenergie A-", {}).get("value")
        ))
        
        # Remove old entries from history
        threshold_time = datetime.now() - timedelta(hours=history_keep_hours)
        cursor.execute('DELETE FROM history WHERE timestamp < ?', (threshold_time,))
        
        conn.commit()
        
    except Exception as e:
        print(f"Error updating history: {e}")
    finally:
        conn.close()

def getCurrentReading():
    """Get the current/latest reading from the database"""
    conn = sqlite3.connect(database_file)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM current_readings ORDER BY timestamp DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

def getHistory(hours=24):
    """Get historical data for the specified number of hours"""
    conn = sqlite3.connect(database_file)
    conn.row_factory = sqlite3.Row
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

def getHistoryAsJson(hours=24):
    """Get historical data in the original JSON format (backwards compatibility)"""
    current = getCurrentReading()
    history_data = getHistory(hours)
    
    if not current or len(history_data) < 2:
        return None
    
    # Calculate differences for backwards compatibility
    calculated_data = []
    for i in range(1, len(history_data)):
        prev_entry = history_data[i-1]
        curr_entry = history_data[i]
        
        # Calculate time difference
        prev_time = datetime.fromisoformat(prev_entry["timestamp"])
        curr_time = datetime.fromisoformat(curr_entry["timestamp"])
        time_diff_hours = (curr_time - prev_time).total_seconds() / 3600
        
        if time_diff_hours > 0:
            # Calculate energy differences
            energy_bezug_diff = curr_entry["wirkenergie_bezug"] - prev_entry["wirkenergie_bezug"]
            energy_lieferung_diff = curr_entry["wirkenergie_lieferung"] - prev_entry["wirkenergie_lieferung"]
            
            # Convert to average power
            power_bezug_diff = energy_bezug_diff / time_diff_hours
            power_lieferung_diff = energy_lieferung_diff / time_diff_hours
            
            calculated_data.append({
                "Datum": curr_entry["timestamp"],
                "Wirkenergie Bezug Diff": round(power_bezug_diff, 2),
                "Wirkenergie Lieferung Diff": round(power_lieferung_diff, 2)
            })
    
    json_history = {
        "Wirkenergie A+ last": current["wirkenergie_bezug"],
        "Wirkenergie A- last": current["wirkenergie_lieferung"], 
        "Datum": current["timestamp"],
        "data": calculated_data
    }
    
    return json_history

def getCurrentAsJson():
    """Get current reading in the same format as the original JSON file"""
    current = getCurrentReading()
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

#######################################
# Main

key = readKey()
synchronizeSerial()

while True:
    #print("Reading data...")
    data = readPacket()
    plaintext = decrypt(data, key)
    json_current = getJsonCurrent(plaintext)
    updateCurrentReading(json_current)
    updateHistory(json_current)
