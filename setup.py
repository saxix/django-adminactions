#!/usr/bin/env python
from __future__ import absolute_import
import os
from setuptools import setup, find_packages
import sys
ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
SOURCE=os.path.join(ROOT, 'src')
sys.path.append(SOURCE)
from adminactions import NAME, VERSION, get_version

rel = lambda fname: os.path.join(os.path.dirname(__file__),
                                 'src',
                                 'adminactions',
                                 'requirements', fname)

if sys.version_info[0] == 2:
    reqs = 'install.py2.pip'
elif sys.version_info[0] == 3:
    reqs = 'install.py3.pip'


def fread(fname):
    return open(rel('install.any.pip')).read() + open(rel(fname)).read()


tests_require = fread('testing.pip')
dev_require = fread('develop.pip')

setup(
    name=NAME,
    version=get_version(),
    url='https://github.com/saxix/django-adminactions',
    download_url='https://github.com/saxix/django-adminactions',
    author='sax',
    author_email='s.apostolico@gmail.com',
    description="Collections of useful actions to use with django.contrib.admin.ModelAdmin",
    license='BSD',

    package_dir={'': 'src'},
    packages=find_packages('src'),

    include_package_data=True,
    install_requires=fread(reqs),
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev': dev_require + tests_require,
    },
    test_suite='conftest.runtests',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Intended Audience :: Developers'],
    long_description=open('README.rst').read()
)
