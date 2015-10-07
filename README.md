pullhook
========

Pull a repo on push, via Github webhook

## Requirements
- GitPython
- PyYaml
- tendo
- bottle
- awesome-slugify


Install them via `pip`:
```pip install -r requirements.txt```


## Simple mode 

`python pullhook.py`

## Always on mode
Add a cronjob to run each minute the `pulhook.py` script. Tendo is used to ensure we only run a single instance.

## Configuration
Copy `config.yml.sample` as `config.yml` and edit it to suit your needs. Explanations are included in comments in the sample config file.

-----

You need to create a webhook in Github (https://github.com/`user`/`repo`/settings/hooks/new) for the repo you want 
and point the payload url to the ip and port where the script is running. No secret is required. Yet.

When a "push" event is received, the received repository and branch names are checked against directories matched from the configured settings.

