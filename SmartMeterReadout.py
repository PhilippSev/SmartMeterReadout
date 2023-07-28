#######################################
#
# SmartMeterReadout.py
#
# This script reads out the smart meter and stores it to json files that can be used by the webserver.
#
# Inspired by and based on:
# https://github.com/micronano0/RaspberryPi-Kaifa-SmartMeter-Reader/blob/main/kaifa_kundenschnittstelle_auslesen.py
# https://www.michaelreitbauer.at/kaifa-ma309-auslesen-smart-meter-evn/?utm_source=pocket_saves
#
#######################################

import serial
import time
from Crypto.Cipher import AES
from enum import Enum
import datetime 

units = {
    # byte  : unit
    0x1b : "W",
    0x1e : "Wh",
    0x20 : "var",
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
    (b'\x01\x00\x03\x08\x00\xFF', Type.UInt32,      "Blindleistung Q+"), # Bezug
    (b'\x01\x00\x04\x08\x00\xFF', Type.UInt32,      "Blindleistung Q-"), # Lieferung
    (b'\x01\x00\x20\x07\x00\xFF', Type.UInt16,      "Spannung L1"),
    (b'\x01\x00\x34\x07\x00\xFF', Type.UInt16,      "Spannung L2"),
    (b'\x01\x00\x48\x07\x00\xFF', Type.UInt16,      "Spannung L3"),
    (b'\x01\x00\x1F\x07\x00\xFF', Type.UInt16,      "Strom L1"),
    (b'\x01\x00\x33\x07\x00\xFF', Type.UInt16,      "Strom L2"),
    (b'\x01\x00\x47\x07\x00\xFF', Type.UInt16,      "Strom L3"),
    (b'\x01\x00\x0D\x07\x00\xFF', Type.UInt16,      "Leistungsfaktor"),
]

#ser = serial.Serial("/dev/ttyS0", baudrate=2400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=10)

mbus_start_bytes = b'\x68\xfa\xfa\x68'
mbus_stop_bytes = b'\x16'
obis_offset =  6 + 1 # 6 bytes octetString id + 1 byte

# read key from file
key_file = open("key.txt", "r")
key_string = key_file.readline().strip()
key_file.close()
key = bytes.fromhex(key_string)


data_file = open("reference/capture_vkw.txt", "r")
data_string = data_file.readline().strip()
data_file.close()
data = bytes.fromhex(data_string)

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
plaintext_bytes = cipher.decrypt(cyphertext_bytes)


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
    
def getValueConverted(type, bytes, length):
    # read obis value bytes
    value_start = value_pos + obis_offset + length[0]
    value_end = value_pos + obis_offset + length[0] + length[1]
    value_bytes = bytes[value_start:value_end]

    value_converted = None
    value_unit = None

    if type == Type.UInt16 or type == Type.UInt32:
        # convert bytes to int
        value_int = int.from_bytes(value_bytes)
        # get scaling value
        value_scaling_raw = bytes[value_end + 3]
        value_scaling = byte_to_signed_integer(value_scaling_raw)
        # apply scaling
        value_converted = float(value_int) * pow(10.0, value_scaling)
        # get unit if known
        value_unit_enum = bytes[value_end + 5]
        if value_unit_enum in units:
            value_unit = units[value_unit_enum]

    elif type == Type.OctetString:
        # convert bytes to string
        value_converted = value_bytes.decode("ascii")

    elif type == Type.Date:
        # convert bytes to datetime
        jear = int.from_bytes(value_bytes[:2])
        month = int.from_bytes(value_bytes[2:3])
        day = int.from_bytes(value_bytes[3:4])
        hour = int.from_bytes(value_bytes[5:6])
        minute = int.from_bytes(value_bytes[6:7])
        second = int.from_bytes(value_bytes[7:8])
        value_converted = datetime.datetime(jear,month,day,hour,minute,second)
    else:
        raise Exception("Unknown type")
    
    return (value_converted, value_unit)
    
def byte_to_signed_integer(byte):
    if byte & 0x80:
        # 2's complement
        return -((~byte & 0xFF) + 1) 
    return byte

# read values from plaintext
for value in valueTuples:
    value_pos = plaintext_bytes.find(value[0])
    if value_pos == -1: 
        # skipp value if not found
        continue 

    # get size of data type
    length = getValueLength(value[1], value_pos, plaintext_bytes)

    # convert obis value to usable value
    value_converted = getValueConverted(value[1], plaintext_bytes, length)


    print(value[2], value_converted)

