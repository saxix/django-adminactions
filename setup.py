#!/usr/bin/env python
import os
from setuptools import setup, find_packages
import sys
import adminactions as app

NAME = app.NAME
RELEASE = app.get_version()

if sys.version_info[0] == 2:
    reqs = 'adminactions/requirements/install2.pip'
elif sys.version_info[0] == 3:
    reqs = 'adminactions/requirements/install3.pip'


def fread(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


tests_require = fread('adminactions/requirements/testing.pip')

setup(
    name=NAME,
    version=RELEASE,
    url='https://github.com/saxix/django-adminactions',
    download_url='https://github.com/saxix/django-adminactions',
    author='sax',
    author_email='s.apostolico@gmail.com',
    description="Collections of useful actions to use with django.contrib.admin.ModelAdmin",
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    install_requires=fread(reqs),
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
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
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Intended Audience :: Developers'],
    long_description=open('README.rst').read()
)
