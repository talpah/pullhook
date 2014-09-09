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

from bottle import route, request, run, abort
import git
import os


MYDIR = os.path.dirname(os.path.abspath(__file__))

"""
 DEFAULT CONFIG VALUES begin
 Use config.ini to override
"""
DEFAULT_CONFIG = {
    'listen_host': '0.0.0.0',  # IP to listen on; Defaults to all interfaces
    'listen_port': '7878',  # Port to listen to
}

MAIN_CONFIG = {}
REPOS_CONFIG = {}


def init():
    """
    Read config file

    """
    global MAIN_CONFIG
    config_file = os.path.join(MYDIR, 'config.ini')
    if not os.path.isfile(config_file):
        raise Exception('Config file "%s" not found. Exiting.' % config_file)
    else:
        parser = SafeConfigParser()
        parser.read(config_file)
        MAIN_CONFIG = dict(DEFAULT_CONFIG.items() + dict(parser.items('pullhook')).items())
        sections = parser.sections()
        if len(sections) < 2:
            raise Exception('No applications defined. See "config.ini.sample" for howto.')
        global REPOS_CONFIG
        for repo in sections:
            if repo != 'pullhook':
                REPOS_CONFIG[repo] = dict(parser.items(repo))
        logging.debug('Found %d repos in config.' % len(REPOS_CONFIG))


@route('/', method=['POST'])
def handle_payload():
    """
    Handles hook requests

    """
    data = request.json
    event = request.get_header('X-GitHub-Event')
    logging.debug("Received event: %s" % event)
    if event == 'push':
        """ Parse repo name from push data ref """
        pushed_repo = data['repository']['name']
        """ Parse branch name from push data ref """
        pushed_branch = data['ref'].split('/')[-1]
        logging.debug("Received push event from repo %s in branch %s" % (pushed_repo, pushed_branch))

        if pushed_repo not in REPOS_CONFIG:
            logging.warning('Repo "%s" is not configured on our end. Skipping.' % pushed_repo)
            abort(404, 'Not configured: %s' % pushed_repo)
        configured_repo = REPOS_CONFIG[pushed_repo]

        """ Use GitPython """
        g = git.Git(configured_repo['basedir'])
        """ Get active branch """
        branch = g.rev_parse('--abbrev-ref', 'HEAD')
        logging.debug("Repo \"%s\", branch \"%s\"" % (configured_repo['basedir'], branch))
        if pushed_branch == branch:
            logging.debug("Pulling new commits.")
            g.pull()
        else:
            logging.debug('Branches are not corresponding: "%s" (local) and "%s" (remote). Skipping.' % (branch, pushed_branch))
            # no abort here


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)  # Uncomment this for debug
    init()
    run(host=MAIN_CONFIG['listen_host'], port=MAIN_CONFIG['listen_port'], debug=True)
