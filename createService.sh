#!/bin/bash

cp smartmeterreadout.service /lib/systemd/system
systemctl daemon-reload 
systemctl enable smartmeterreadout.service
systemctl start smartmeterreadout.service
systemctl status smartmeterreadout.service
