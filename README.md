# SmartMeter Readout

Smart Meter Readout is a small python script that periodically reads the values from the KAIFA SmartMeter using the MBUS customer interface.
The read values are then saved as json files that can be used by e.g. a Webserver.

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
