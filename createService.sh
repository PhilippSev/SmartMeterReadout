#!/bin/bash

# Ensure the service directory exists and has correct permissions
mkdir -p /home/pi/readout
chown pi:pi /home/pi/readout

# Ensure the persistent data directory exists and has correct permissions  
mkdir -p /home/pi/smartmeter_data
chown pi:pi /home/pi/smartmeter_data

# Ensure tmpfs directory exists and has correct permissions
mkdir -p /ram
chmod a+rw /ram

# Copy service file and reload systemd
cp smartmeterreadout.service /lib/systemd/system
systemctl daemon-reload 
systemctl enable smartmeterreadout.service
systemctl start smartmeterreadout.service
systemctl status smartmeterreadout.service
