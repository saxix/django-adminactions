import datetime
import os
import subprocess

VERSION = __version__ = (1, 5, 0, 'final', 0)
NAME = 'django-adminactions'


def get_version(version=None):
    """Derives a PEP386-compliant version number from VERSION."""
    if version is None:
        version = VERSION
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        git_changeset = get_git_changeset()
        if git_changeset:
            sub = '.a%s' % git_changeset

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])
    elif version[3] == 'final' and version[4] != 0:
        sub = '-%s' % version[4]

    return main + sub


def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.

The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
This value isn't guaranteed to be unique, but collisions are very unlikely,
so it's sufficient for generating the development version numbers.
"""
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    git_log = subprocess.Popen('git log --pretty=format:%ct --quiet -1 HEAD',
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               shell=True, cwd=repo_dir, universal_newlines=True)
    value = git_log.communicate()[0]
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(value))
    except ValueError:
        return None
    return timestamp.strftime('%Y%m%d%H%M%S')
