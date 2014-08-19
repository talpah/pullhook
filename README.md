pullhook
========

Pull a repo on push, via Github webhook

## Requirements
- GitPython
- bottle

Install via `pip`:
```pip install -r requirements.txt```


## Usage

`python pullhook.py`

By default it listens on all interfaces on port 7878. 

You need to create a webhook in Github for the repo you want and point the payload url to the ip and port where the script is running. No secret is required. Yet.

When a "push" event is received and the "push" branch corresponds to the active branch of the BASE_DIR (default is the script's directory), a "git pull" is initiated.

## Configuration
  - `BASE_DIR` Holds the path to the clone which will be updated
  - `host='0.0.0.0'` Interface to bind to
  - `port=7878` Port to listen to
