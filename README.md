# SmartMeter Readout

Smart Meter Readout is a Python script that periodically reads values from a KAIFA CL101 Smartmeter from VKW using the MBUS customer interface.
It was tested on a RaspberryPi Zero W with an MBus adapter.
The received values are stored in a local SQLite database for efficient querying and data management.

## Detailed Description and required Hardware
A detailed description of the project and the required hardware can be found on [my blog](https://projekte.philippseverin.at/2023/08/04/smartmeter-mit-raspberrypi-auslesen/).

## Setup
The setup uses **pypy** to execute the script for better performance.

### Prerequisites

First, install the required system packages:

```bash
# Update package list
sudo apt update

# Install PyPy3 and pip
sudo apt install pypy3 pypy3-dev pypy3-venv

# Install pip for PyPy3 if not already available
sudo apt install pypy3-pip

# Install git to clone the repository
sudo apt install git
```

### Installation

1. **Clone the repository**:
   ```bash
   cd /home/pi
   git clone https://github.com/PhilippSev/SmartMeterReadout.git
   cd SmartMeterReadout
   ```

2. **Create the data directory**:
   ```bash
   sudo mkdir -p /home/pi/smartmeter_data
   sudo chown pi:pi /home/pi/smartmeter_data
   ```

3. **Create the service directory**:
   ```bash
   sudo mkdir -p /home/pi/readout
   sudo chown pi:pi /home/pi/readout
   ```

4. **Copy files to service directory**:
   ```bash
   cp SmartMeterReadout.py /home/pi/readout/
   cp query_database.py /home/pi/readout/
   cp requirements.txt /home/pi/readout/
   cp smartmeterreadout.service /home/pi/readout/
   cp createService.sh /home/pi/readout/
   ```

### Key

The SmartMeter requires a key to access.
This key is stored in the file ```key.txt``` which is excluded from the repository.

**Create the key file**:
```bash
# Create the key file in the service directory
echo "YOUR_SMARTMETER_KEY_HERE" > /home/pi/readout/key.txt
# Replace YOUR_SMARTMETER_KEY_HERE with your actual 32-character hex key
```

### Install python requirements
In order for the systemd service to be able to execute the script the requirements must be installed for all users on the system.

```
sudo pypy3 -mpip install -r requirements.txt
```

### Setup as Systemd Service

The Setup as systemd service is done by executing the createService script. 
This script expects the required files to be placed in ```/home/pi/readout```

```bash
cd /home/pi/readout
sudo ./createService.sh
```

After setting up the service, you can control it with:

```bash
# Start the service
sudo systemctl start smartmeterreadout

# Enable autostart on boot
sudo systemctl enable smartmeterreadout

# Check service status
sudo systemctl status smartmeterreadout

# View service logs
sudo journalctl -u smartmeterreadout -f
```

### Hardware Setup

Make sure your hardware is properly configured:

1. **Serial Interface**: Enable the serial interface on your Raspberry Pi
   ```bash
   sudo raspi-config
   # Go to Interfacing Options > Serial > Enable
   ```

2. **MBus Connection**: Connect your MBus adapter to the Raspberry Pi's serial pins
   - The script uses `/dev/ttyS0` by default
   - Make sure the pi user has access to the serial port:
     ```bash
     sudo usermod -a -G dialout pi
     ```

3. **Test Connection**: You can test if the smart meter is responding:
   ```bash
   # Check if the serial device exists
   ls -l /dev/ttyS0
   
   # Test basic serial communication (optional)
   sudo cat /dev/ttyS0
   ```

### Troubleshooting

**Permission Issues**:
```bash
# Make sure all scripts are executable
chmod +x /home/pi/readout/*.py
chmod +x /home/pi/readout/createService.sh

# Check serial port permissions
ls -l /dev/ttyS0
sudo usermod -a -G dialout pi
# Logout and login again for group changes to take effect
```

**Service Issues**:
```bash
# Check if service is running
sudo systemctl status smartmeterreadout

# Restart service
sudo systemctl restart smartmeterreadout

# Check logs for errors
sudo journalctl -u smartmeterreadout --no-pager -l
```

**Database Issues**:
```bash
# Check if database directory exists and is writable
ls -la /home/pi/smartmeter_data/

# Test database connection
cd /home/pi/readout
python3 query_database.py current
```

## Using the Database

### Direct Database Access

You can query the database directly using the included query script:

```bash
# Show current reading summary
python3 query_database.py current

# Show history for last 24 hours
python3 query_database.py history

# Show history for last 48 hours  
python3 query_database.py history 48

# Export current reading as JSON
python3 query_database.py export-current

# Export history as JSON
python3 query_database.py export-history 24
```

### Database Schema

The SQLite database contains two main tables:

**current_readings**: Stores the latest meter readings
- timestamp, meter_number, logical_device_name
- wirkenergie_bezug/lieferung (energy consumption/production)
- wirkleistung_bezug/lieferung (power consumption/production)  
- spannung_l1/l2/l3 (voltage for each phase)
- strom_l1/l2/l3 (current for each phase)
- blindenergie_bezug/lieferung (reactive energy)
- leistungsfaktor (power factor)

**history**: Stores calculated differences over time
- timestamp
- wirkenergie_bezug_diff/wirkenergie_lieferung_diff (power differences in W)

## Disk Usage
The SQLite database is stored persistently in `/home/pi/smartmeter_data/` to preserve historical data across reboots.
