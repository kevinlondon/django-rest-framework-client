#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'requests>=2.4.3',
    'python-dateutil>=2.4.0'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='djangorestclient',
    version='0.1.0',
    description="A helper library for Django Rest Framework Client Generator.",
    long_description=readme + '\n\n' + history,
    author="Kevin London",
    author_email='kevin@wiredrive.com',
    url='https://github.com/kevinlondon/django-rest-framework-client',
    packages=[
        'drf_client',
    ],
    package_dir={'drf_client': 'drf_client'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='drf_client',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
