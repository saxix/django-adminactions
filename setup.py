#!/usr/bin/env python
# pylint: disable=W,I,C
from __future__ import absolute_import

import imp
import os
import sys

from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
init = os.path.join(ROOT, 'src', 'adminactions', '__init__.py')
app = imp.load_source('adminactions', init)


reqs = "install.py{}.pip".format(sys.version_info[0])

rel = lambda fname: os.path.join(os.path.dirname(__file__),
                                 'src',
                                 'requirements', fname)

def fread(fname):
    return open(rel('install.any.pip')).read() + open(rel(fname)).read()


requirements = fread(reqs)
tests_require = fread('testing.pip')
dev_require = fread('develop.pip')

setup(
    name='django-adminactions',
    version=app.get_version(),
    url='https://github.com/saxix/django-adminactions',
    download_url='https://github.com/saxix/django-adminactions',
    author='sax',
    author_email='s.apostolico@gmail.com',
    description="Collections of useful actions to use with django.contrib.admin.ModelAdmin",
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=requirements,
    tests_require=tests_require,
    extras_require={
        'test': requirements+tests_require,
        'dev': dev_require + tests_require,
    },
    zip_safe=False,
    platforms=['any'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers'],
    long_description=open('README.rst').read()
)
