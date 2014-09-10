pullhook
========

Pull a repo on push, via Github webhook

## Requirements
- GitPython
- bottle
- tendo

Install via `pip`:
```pip install -r requirements.txt```


## Usage

`python pullhook.py`

By default it listens on all interfaces on port 7878. 

You need to create a webhook in Github for the repo you want and point the payload url to the ip and port where the script is running. No secret is required. Yet.

When a "push" event is received and the "push" branch corresponds to the active branch of the BASE_DIR (default is the script's directory), a "git pull" is initiated.

## Configuration
Create a `config.ini` by copying `config.ini.sample` and edit it to suit your needs.
Omitted/Commented out options are ignored and the default values in `pullhook.py` are used instead.
