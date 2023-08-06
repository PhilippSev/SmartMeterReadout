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

#######################################
# Configuration

history_keep_hours = 24
hostory_update_minutes = 1
directory = "/ram/www"
history_file = "/ram/www/history.json"
current_file = "/ram/www/current.json"
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

def updateJsonCurrent(json_current):
    # Serializing json
    json_object = json.dumps(json_current, indent=2, default=str)

    # Writing current values to file
    with open(current_file, "w") as outfile:
        outfile.write(json_object)

def updateJsonHistory(json_current):
    # update history
    try:
        with open(history_file, "r") as file:
            json_history = json.load(file)

        # only update history every minute
        time_difference = json_current["Datum"]["value"] - datetime.fromisoformat(json_history["Datum"])
        if time_difference < timedelta(minutes=hostory_update_minutes):
            return

        # remove old entries from history json
        current_time = datetime.now()
        threshold_time = current_time - timedelta(hours=history_keep_hours)
        filtered_data = [pair for pair in json_history["data"] if datetime.fromisoformat(pair['Datum']) >= threshold_time]

        # read old Wirkenenergie A+ and A- values
        wirkenergie_bezug_old = json_history["Wirkenergie A+ last"]
        wirkenergie_lieferung_old = json_history["Wirkenergie A- last"]

        # get current values
        wirkenergie_bezug_new = json_current["Wirkenergie A+"]["value"]
        wirkenergie_lieferung_new = json_current["Wirkenergie A-"]["value"]

        # calculate watts from difference
        time_difference_hours = time_difference.total_seconds() / 3600
        wirkenergie_bezug_difference = (wirkenergie_bezug_new - wirkenergie_bezug_old) / time_difference_hours
        wirkenergie_lieferung_difference = (wirkenergie_lieferung_new - wirkenergie_lieferung_old) / time_difference_hours
    except:
        filtered_data = []
        wirkenergie_bezug_difference = 0
        wirkenergie_lieferung_difference = 0

    # create new entry
    json_history_entry = {}
    json_history_entry["Datum"] = json_current["Datum"]["value"]
    json_history_entry["Wirkenergie Bezug Diff"] = round(wirkenergie_bezug_difference, 2)
    json_history_entry["Wirkenergie Lieferung Diff"] = round(wirkenergie_lieferung_difference, 2)

    filtered_data.append(json_history_entry)

    json_history = {}
    json_history["Wirkenergie A+ last"] = json_current["Wirkenergie A+"]["value"]
    json_history["Wirkenergie A- last"] = json_current["Wirkenergie A-"]["value"]
    json_history["Datum"] = json_current["Datum"]["value"]
    json_history["data"] = filtered_data

    # write history to file
    with open(history_file, 'w') as file:
        json.dump(json_history, file, indent=2, default=str)

#######################################
# Main

key = readKey()
synchronizeSerial()

while True:
    #print("Reading data...")
    data = readPacket()
    plaintext = decrypt(data, key)
    json_current = getJsonCurrent(plaintext)
    updateJsonCurrent(json_current)
    updateJsonHistory(json_current)
