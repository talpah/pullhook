#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Github hook for deployment
"""
__author__ = 'talpah@gmail.com'

from bottle import route, request, run
import git
import os

""" Override BASE_DIR for different clone path """
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


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
        g = git.Git(BASE_DIR)
        """ Get active branch """
        branch = g.rev_parse('--abbrev-ref', 'HEAD')
        print "We're on branch %s" % branch
        if pushed_branch == branch:
            print "Pulling repo in %s" % BASE_DIR
            g.pull()


if __name__ == '__main__':
        """ 
        Feel free to bind the server to any ip and port you desire 
        just make sure it's accessible by GitHub
        """
        run(host='0.0.0.0', port=7878, debug=True)
