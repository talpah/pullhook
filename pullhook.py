#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
    Github hook for deployment
        Feel free to bind the server to any ip and port you desire
        just make sure it's accessible by GitHub
"""
from ConfigParser import SafeConfigParser
import logging

__author__ = 'talpah@gmail.com'

from bottle import route, request, run
import git
import os


MYDIR = os.path.dirname(os.path.abspath(__file__))

"""
 DEFAULT CONFIG VALUES begin
 Use config.ini to override
"""
DEFAULT_CONFIG = {
    'basedir': MYDIR,  # Default path for git pull
    'listen_host': '0.0.0.0',  # IP to listen on; Defaults to all interfaces
    'listen_port': '7878',  # Port to listen to
}

CONFIG = {}


def init():
    """
    Read config file

    """
    global CONFIG
    config_file = os.path.join(MYDIR, 'config.ini')
    if not os.path.isfile(config_file):
        CONFIG = DEFAULT_CONFIG
        logging.info('No config file found at "%s", using defaults' % config_file)
    else:
        parser = SafeConfigParser(DEFAULT_CONFIG)
        parser.read(config_file)
        CONFIG = dict(parser.items('pullhook'))


@route('/', method=['POST'])
def handle_payload():
    """
    Handles hook requests

    """
    data = request.json
    event = request.get_header('X-GitHub-Event')
    logging.debug("Received event: %s" % event)
    if event == 'push':
        """ Parse branch name from push data ref """
        pushed_branch = data['ref'].split('/')[-1]
        logging.debug("Received push event in branch %s" % pushed_branch)
        """ Use GitPython """
        g = git.Git(CONFIG['basedir'])
        """ Get active branch """
        branch = g.rev_parse('--abbrev-ref', 'HEAD')
        logging.debug("We're on branch %s" % branch)
        if pushed_branch == branch:
            logging.debug("Pulling repo in %s" % CONFIG['basedir'])
            g.pull()


if __name__ == '__main__':
    init()
    run(host=CONFIG['listen_host'], port=CONFIG['listen_port'], debug=True)
