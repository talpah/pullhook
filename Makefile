export LOCALNAME = $(shell basename $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

setup:
	virtualenv $(WORKON_HOME)/$(LOCALNAME)
	$(WORKON_HOME)/$(LOCALNAME)/bin/pip install -r requirements.txt

.PHONY: setup
