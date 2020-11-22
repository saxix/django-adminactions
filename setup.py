#!/usr/bin/env python
import ast
import codecs
import os

import re
from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
init = os.path.join(ROOT, 'src', 'adminactions', '__init__.py')


def read(*parts):
    with codecs.open(os.path.join(ROOT, 'src', 'requirements', *parts), 'r') as fp:
        return fp.read()


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open(init, 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

requirements = read("install.pip")
tests_require = read('testing.pip')
dev_require = read('develop.pip')

setup(
    name='django-adminactions',
    version=version,
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
        'test': requirements + tests_require,
        'dev': dev_require + tests_require,
    },
    zip_safe=False,
    platforms=['any'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Intended Audience :: Developers'],
    long_description=open('README.rst').read()
)
