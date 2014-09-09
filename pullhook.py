#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Github hook for deployment
"""
from ConfigParser import SafeConfigParser

__author__ = 'talpah@gmail.com'

from bottle import route, request, run
import git
import os

"""
 DEFAULT CONFIG VALUES begin
 Use config.ini to override
"""
DEFAULT_CONFIG = {
    'basedir': os.path.dirname(os.path.realpath(__file__)),  # Default path for git pull
    'listen_host': '0.0.0.0',  # IP to listen on; Defaults to all interfaces
    'listen_port': '7878',  # Port to listen to
}

CONFIG = {}


def init():
    """
    Read config file

    """
    parser = SafeConfigParser(DEFAULT_CONFIG)
    parser.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    global CONFIG
    CONFIG = dict(parser.items('pullhook'))


@route('/', method=['POST'])
def handle_payload():
    """
    Handles hook requests

    """
    data = request.json
    event = request.get_header('X-GitHub-Event')
    print "Received event: %s" % event
    if event == 'push':
        """ Parse branch name from push data ref """
        pushed_branch = data['ref'].split('/')[-1]
        print "Received push event in branch %s" % pushed_branch
        """ Use GitPython """
        g = git.Git(CONFIG['basedir'])
        """ Get active branch """
        branch = g.rev_parse('--abbrev-ref', 'HEAD')
        print "We're on branch %s" % branch
        if pushed_branch == branch:
            print "Pulling repo in %s" % CONFIG['basedir']
            g.pull()


if __name__ == '__main__':
    """
    Feel free to bind the server to any ip and port you desire
    just make sure it's accessible by GitHub
    """
    init()
    run(host=CONFIG['listen_host'], port=CONFIG['listen_port'], debug=True)
