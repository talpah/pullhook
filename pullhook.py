#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
    Github hook for deployment
        Feel free to bind the server to any ip and port you desire
        just make sure it's accessible by GitHub
"""
import os
import pwd

import bottle
from tendo import singleton

from lib import logger, run_application, update_project, \
    get_matching_projects, config

__author__ = 'talpah@gmail.com'

bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024

"""
Run as different user
http://stackoverflow.com/a/1499386
"""
if config.runas:
    try:
        uid = pwd.getpwnam(config.runas)[2]
        os.setuid(uid)
        logger.info('Running as: {}'.format(config.runas))
    except OSError as e:
        logger.warning('Cannot run as {}: {}'.format(config.runas, e.strerror))
        username = pwd.getpwuid(os.getuid()).pw_name
        logger.info('Running as: {}'.format(username))


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
        pushed_branch = data['ref'].split('/', 2)[-1]

        logger.debug("Received push event from repo %s in branch %s" % (pushed_repo, pushed_branch))

        matching_projects = get_matching_projects(pushed_repo, pushed_branch)

        if not matching_projects:
            logger.debug('Push for "%s/%s" did not match anything. Skipping.' % (pushed_repo, pushed_branch))
            bottle.abort(404, 'Not configured: %s/%s' % (pushed_repo, pushed_branch))

        for m in matching_projects:
            update_project(m)


if __name__ == '__main__':
    """
        Single instance
        Hide warnings to prevent cron mails
    """
    import logging

    tmp = logging.getLogger().level
    logging.getLogger().setLevel(logging.CRITICAL)
    _myinstance_ = singleton.SingleInstance()
    logging.getLogger().setLevel(tmp)

    run_application()
