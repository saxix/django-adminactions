#!/usr/bin/env python
import os
from setuptools import setup, find_packages
import adminactions as app

NAME = app.NAME
RELEASE = app.get_version()


def fread(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

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
    install_requires=fread('adminactions/requirements.pip').split('\n'),
    zip_safe=False,
    platforms=['any'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Intended Audience :: Developers'],
    long_description=open('README.rst').read()
)
