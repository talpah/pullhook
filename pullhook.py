#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
    Github hook for deployment
        Feel free to bind the server to any ip and port you desire
        just make sure it's accessible by GitHub
"""
__author__ = 'talpah@gmail.com'

from ConfigParser import SafeConfigParser
import logging
import bottle
from tendo import singleton
import git
import os


MYDIR = os.path.dirname(os.path.abspath(__file__))

"""
 DEFAULT CONFIG VALUES begin
 Use config.ini to override
"""
DEFAULT_CONFIG = {
    'debug': 'false',  # Single instance
    'listen_host': '0.0.0.0',  # IP to listen on; Defaults to all interfaces
    'listen_port': '7878',  # Port to listen to
}

MAIN_CONFIG = {}
REPOS_CONFIG = {}

"""
    Single instance
    Hide warning to prevent cron mails
"""
tmp = logging.getLogger().level
logging.getLogger().setLevel(logging.CRITICAL)
_myinstance_ = singleton.SingleInstance()
logging.getLogger().setLevel(tmp)

""" Logging """
logger = logging.getLogger("pullhook")
logger.addHandler(logging.StreamHandler())

""" Code below """


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
        if MAIN_CONFIG['debug'].lower() in ['true', 'yes', '1', 'on']:
            logger.setLevel(logging.DEBUG)
        sections = parser.sections()
        if len(sections) < 2:
            raise Exception(
                'Configuration error: No applications defined. Create "config.ini". See "config.ini.sample" for howto.')
        global REPOS_CONFIG
        for app_name in sections:
            if app_name != 'pullhook':
                config = dict(parser.items(app_name))
                if 'basedir' not in config:
                    raise Exception(
                        'Configuration error: "%s" application is missing the "basedir" key.' % app_name)
                REPOS_CONFIG[app_name] = config
        logger.debug('Found %d repos in config.' % len(REPOS_CONFIG))


def run_command(command):
    if isinstance(command, str):
        command = command.split(' ')
    from subprocess import check_output

    logger.debug('Running %s' % ' '.join(command))
    out = check_output(command)
    logger.debug('Output: %s' % out)


@bottle.route('/', method=['POST'])
def handle_payload():
    """
    Handles hook requests

    """
    data = bottle.request.json
    event = bottle.request.get_header('X-GitHub-Event')
    logger.debug("Received event: %s" % event)
    if event == 'push':
        """ Parse repo name from push data ref """
        pushed_repo = data['repository']['name']
        """ Parse branch name from push data ref """
        pushed_branch = data['ref'].split('/')[-1]

        pushed_w_branch = '%s:%s' % (pushed_repo, pushed_branch)
        logger.debug("Received push event from repo %s in branch %s" % (pushed_repo, pushed_branch))

        if pushed_w_branch in REPOS_CONFIG:
            configured_repo = REPOS_CONFIG[pushed_w_branch]
        elif pushed_repo in REPOS_CONFIG:
            configured_repo = REPOS_CONFIG[pushed_repo]
        else:
            logger.warning('Repo "%s" is not configured on our end. Skipping.' % pushed_repo)
            bottle.abort(404, 'Not configured: %s' % pushed_repo)
            return

        """ Use GitPython """
        g = git.Git(configured_repo['basedir'])
        """ Get active branch """
        branch = g.rev_parse('--abbrev-ref', 'HEAD')
        logger.debug("Repo \"%s\", branch \"%s\"" % (configured_repo['basedir'], branch))
        if pushed_branch == branch:
            logger.debug("Pulling new commits.")
            g.pull()
            if 'run' in configured_repo:
                try:
                    run_command(configured_repo['run'])
                except Exception:
                    pass
        else:
            logger.debug(
                'Branches are not corresponding: "%s" (local) and "%s" (remote). Skipping.' % (branch, pushed_branch))
            # no abort here


if __name__ == '__main__':
    init()

    """ Bottle arguments """
    bottle_params = {
        'host': MAIN_CONFIG['listen_host'],
        'port': MAIN_CONFIG['listen_port'],
        'quiet': True
    }

    """ DEBUG """
    if MAIN_CONFIG['debug'].lower() in ['true', 'yes', '1', 'on']:
        bottle_params['quiet'] = False
        bottle_params['debug'] = True

    bottle.run(**bottle_params)
