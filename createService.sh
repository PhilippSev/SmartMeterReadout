#!/bin/bash

# Ensure the service directory exists and has correct permissions
mkdir -p /home/pi/readout
chown pi:pi /home/pi/readout

# Ensure the data directory exists and has correct permissions  
mkdir -p /home/pi/smartmeter_data
chown pi:pi /home/pi/smartmeter_data

# Copy service file and reload systemd
cp smartmeterreadout.service /lib/systemd/system
systemctl daemon-reload 
systemctl enable smartmeterreadout.service
systemctl start smartmeterreadout.service
systemctl status smartmeterreadout.service
