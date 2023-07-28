# SmartMeter Readout

Smart Meter Readout is a small python script that periodically reads the values from the KAIFA SmartMeter using the MBUS customer interface. The read values are then saved as json files that can be used by e.g. a Webserver.

## Setup

### Key

The SmartMeter requires a key to accesss. This key is stored in the file ```key.txt``` wich is excluded from the repository.

### Install python requirements

```
pip install -r requirements.txt
```

### Setup as Systemd Service

The Setup as systemd service is done by executing the createService script.
```
createSercive.sh
```
