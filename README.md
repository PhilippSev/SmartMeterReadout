# SmartMeter Readout

Smart Meter Readout is a small Python script that periodically reads the values from a KAIFA CL101 Smartmeter from VKW using the MBUS customer interface.
It is was tested on a RaspberryPi Zero W with an MBus adapter.
The received values are then saved as json files that can be used by a Webserver.

## Detailed Description and required Hardware
A detailed description of the project and the required hardware can be found on [my blog](https://projekte.philippseverin.at/2023/08/04/smartmeter-mit-raspberrypi-auslesen/).

## Setup
The setup uses **pypy** to execute the script.

### Key

The SmartMeter requires a key to accesss.
This key is stored in the file ```key.txt``` wich is excluded from the repository.

### Install python requirements
In order for the systemd service to be able to execute the script the requirements must be installed for all users on the system.

```
sudo pypy3 -mpip install -r requirements.txt
```

### Setup as Systemd Service

The Setup as systemd service is done by executing the createService script. 
This script expects the required files to be placed in ```/home/pi/readout```
```
sudo createSercive.sh
```

## Disk Usage
Because this script does a lot of periodic writing to files, it is best to store the files in a ```tmpfs``` mounted directory.
Therefore, the files are stored in the ```\ram``` directory created, for this purpose.
