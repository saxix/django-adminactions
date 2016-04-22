#!/usr/bin/env python
# pylint: disable=W,I,C
from __future__ import absolute_import

import imp
import os
import sys
from distutils import log
from distutils.command.clean import clean as CleanCommand
from distutils.dir_util import remove_tree

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
init = os.path.join(ROOT, 'src', 'adminactions', '__init__.py')

if sys.version_info[0] == 2:
    reqs = 'install.py2.pip'
    app = imp.load_source('adminactions', init)
elif sys.version_info[0] == 3:
    reqs = 'install.py3.pip'
    if sys.version_info[1] in [3,4]:
        from importlib.machinery import SourceFileLoader
        app = SourceFileLoader("adminactions", init).load_module()
    elif sys.version_info[1] in [5]:
        import importlib.util
        spec = importlib.util.spec_from_file_location("adminactions", init)
        app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app)

rel = lambda fname: os.path.join(os.path.dirname(__file__),
                                 'src',
                                 'requirements', fname)


class Clean(CleanCommand):
    user_options = CleanCommand.user_options + [
        ('build-coverage=', 'c',
         "build directory for coverage output (default: 'build/coverage')"),
        ('build-tox=', 't',
         "build directory for tox (default: '.tox')"),
    ]

    def initialize_options(self):
        self.build_coverage = None
        self.build_help = None
        self.build_tox = None
        CleanCommand.initialize_options(self)

    def run(self):
        if self.all:
            for directory in (os.path.join(self.build_base, 'coverage'),
                              os.path.join('dist'),
                              os.path.join('.tox'),
                              os.path.join(self.build_base, 'help')):
                if os.path.exists(directory):
                    remove_tree(directory, dry_run=self.dry_run)
                else:
                    log.warn("'%s' does not exist -- can't clean it",
                             directory)
        if self.build_coverage:
            remove_tree(self.build_coverage, dry_run=self.dry_run)
        if self.build_help:
            remove_tree(self.build_help, dry_run=self.dry_run)
        if self.build_tox:
            remove_tree(self.build_tox, dry_run=self.dry_run)
        CleanCommand.run(self)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['tests']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def fread(fname):
    return open(rel('install.any.pip')).read() + open(rel(fname)).read()


tests_require = fread('testing.pip')
dev_require = fread('develop.pip')

setup(
    name=app.NAME,
    version=app.get_version(),
    url='https://github.com/saxix/django-adminactions',
    download_url='https://github.com/saxix/django-adminactions',
    author='sax',
    author_email='s.apostolico@gmail.com',
    description="Collections of useful actions to use with django.contrib.admin.ModelAdmin",
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    cmdclass={'test': PyTest,
              'clean': Clean},
    include_package_data=True,
    install_requires=fread(reqs),
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev': dev_require + tests_require,
    },
    zip_safe=False,
    platforms=['any'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Framework :: Django :: 1.4',
        'Framework :: Django :: 1.5',
        'Framework :: Django :: 1.6',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Intended Audience :: Developers'],
    long_description=open('README.rst').read()
)
