# coding=utf-8
"""
Lib
"""
import logging
from subprocess import CalledProcessError, STDOUT

from git.repo import Repo
import os
import bottle
from slugify import slugify
import sys
import yaml

REPOS = {}
AUTO_REPOS = {}


class Config(dict):
    """
    Config file as class attributes
    """

    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            value = Config(value)
        return value


logger = logging.getLogger("pullhook")
logger.addHandler(logging.StreamHandler())

CONFIG_FILE = os.path.realpath(os.path.join(os.path.dirname(__file__), 'config.yml'))
if not os.path.exists(CONFIG_FILE):
    logger.fatal("Can't find a config file. Copy 'config.yml.sample' as 'config.yml' and start editing.")
    sys.exit(10)
with open(CONFIG_FILE) as fp:
    parsed_config = yaml.load(fp)
try:
    config = Config(parsed_config)
except TypeError:
    logger.fatal("Invalid config.yml. Use 'config.yml.sample' as guide.")
    sys.exit(20)

if 'debug' in config and config.debug:
    logger.setLevel(logging.DEBUG)


def run_application():
    """
        Pre-flight checks and run_application
    """

    try:
        """ Bottle arguments """
        bottle_params = {
            'host': config.listen.ip,
            'port': config.listen.port,
            'quiet': True
        }
    except KeyError:
        logger.fatal("Config is missing something in the 'listen' section. Use 'config.yml.sample' as guide.")
        sys.exit(40)

    if 'paths' not in config or not config.paths:
        logger.fatal("No paths found in config. Use 'config.yml.sample' as guide.")
        sys.exit(30)
    for app in config.paths:
        for app_path, app_config in app.items():
            if 'auto' not in app_config or not app_config['auto']:
                if not os.path.isdir(app_path):
                    logger.warning("Static path '%s' is not a directory. Ignoring." % app_path)
                    continue
                if len(app_config['repo']) == 0:
                    logger.warning("Static path '%s' has no repo configured. Ignoring." % app_path)
                    continue
                repo_key = app_config['repo']
                try:
                    repo_key += ":" + app_config['branch']
                except KeyError:
                    pass

                app_config['basedir'] = app_path
                REPOS[repo_key] = app_config
            else:
                repo_key = app_path
                app_config['basedir'] = app_path
                AUTO_REPOS[repo_key] = app_config

    logger.debug('Found %d static projects and %d auto.' % (len(REPOS), len(AUTO_REPOS)))

    """ DEBUG """
    if 'debug' in config and config.debug:
        bottle_params['quiet'] = False
        bottle_params['debug'] = True
    """ Start listener """
    bottle.run(**bottle_params)


def get_matching_projects(pushed_repo, pushed_branch):
    """
    Return a list containing paths matching the pushed repo and branch
    :param pushed_repo:
    :param pushed_branch:
    :return:
    """
    pushed_fullname = '%s:%s' % (pushed_repo, pushed_branch)
    matched = []
    if pushed_fullname in REPOS and check_match(REPOS[pushed_fullname], pushed_repo, pushed_branch):
        matched.append(REPOS[pushed_fullname])
    if pushed_repo in REPOS and check_match(REPOS[pushed_repo], pushed_repo, pushed_branch):
        matched.append(REPOS[pushed_repo])

    matched += get_matching_in_auto_mode(pushed_repo, pushed_branch)
    return matched


def get_matching_in_auto_mode(repo, branch):
    """
    Try to guess project dir by using repo and branch names
    Paths tested:
    - repo/
    - repo/branch/
    - repo_branch/
    - repo-branch/
    - branch/

    :param repo:
    :param branch:
    :return:
    """
    repo_config = {
        "repo": repo,
        "auto": True,
        "branch": branch,
        "basedir": "",
    }

    try:
        path_possibilities = config.path_possibilities
    except KeyError:
        path_possibilities = ['{repo}', '{reposlug}-{branchslug}', '{branchslug}', '{repo}/{branch}', '{repo}_{branch}',
                              '{repo}-{branch}', '{branch}']
    path_possibilities = [c.format(repo=repo, branch=branch, reposlug=slugify(repo), branchslug=slugify(branch))
                          for c in path_possibilities]

    matches = []
    for auto_path, auto_config in AUTO_REPOS.items():
        for path in path_possibilities:
            if os.path.isdir(os.path.join(auto_path, path)):
                repocheck = repo_config.copy()
                repocheck.update(auto_config)
                repocheck['basedir'] = os.path.join(auto_path, path)
                if check_match(repocheck, repo, branch):
                    matches.append(repocheck)
    return matches


def check_match(configured_repo, pushed_repo, pushed_branch):
    """
    Checks if the repo and branch match the configuration

    :param configured_repo:
    :param pushed_repo:
    :param pushed_branch:
    :return:
    """
    try:
        r = Repo(configured_repo['basedir'])
        repo_url = r.remotes.origin.config_reader.get('url')
        repo_name = repo_url.split('/')[-1]
        if '.git' in repo_name:
            repo_name = repo_name[:-4]
        if repo_name != pushed_repo:
            logger.debug("Repo name mismatch: %s and %s" % (pushed_repo, repo_name))
            return False
        """ Get active branch """
        branch_name = r.active_branch.name
        if pushed_branch == branch_name:
            logger.debug("Matching %s" % configured_repo['basedir'])
            return True
        else:
            raise Exception(
                'Branches are not corresponding: "%s" (local) and "%s" (remote). Skipping.' % (
                    branch_name, pushed_branch))

    except Exception as e:
        logger.debug("Check match exception for '%s': %s" % (configured_repo['basedir'], str(e)))
        return False


def update_project(configured_repo):
    """
    Updates the given paths

    :param configured_repo:
    :return:
    """
    logger.debug("Updating %s" % configured_repo['basedir'])
    r = Repo(configured_repo['basedir'])

    try:
        execute_command(configured_repo['run_before'], configured_repo)
    except Exception:
        pass
    r.remotes.origin.pull()
    try:
        execute_command(configured_repo['run_after'], configured_repo)
    except Exception:
        pass


def execute_command(command, app_config):
    """
    Used for running app pre/post commands
    :param command: the command to run
    """
    if isinstance(command, str):
        command = command.format(**app_config)
        command = command.split(' ')
    from subprocess import check_output

    logger.debug('Executing %s' % ' '.join(command))
    try:
        out = check_output(command, stderr=STDOUT)
        logger.debug('Output: %s' % out)
    except CalledProcessError as e:
        logger.debug('Error executing %s: %s' % (' '.join(command), e.output))
