#!/bin/bash

cp smartmeterreadout.service /etc/systemd/user/smartmeterreadout.service
systemctl --user daemon-reload 
systemctl enable smartmeterreadout.service
systemctl start smartmeterreadout.service
