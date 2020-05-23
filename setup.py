# -*- coding: utf-8 -*-
#
# This file is part of the multigauge project
#
# Copyright (c) 2020 Tiago Coutinho
# Distributed under the MIT license. See LICENSE for more info.

"""The setup script."""

import sys
from setuptools import setup, find_packages


def get_readme(name='README.md'):
    """Get readme file contents"""
    with open(name) as f:
        return f.read()


readme = get_readme()


requirements = []


extras_requirements = {
    "simulator": ["sinstruments"],
}


test_requirements = ['pytest', 'pytest-cov']


setup_requirements = []


needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
if needs_pytest:
    setup_requirements.append('pytest-runner')


setup(
    author="Jose Tiago Macara Coutinho",
    author_email='coutinhotiago@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="multigauge protocol",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='vacuum,multigauge,variandual',
    name='vazio',
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    extras_require=extras_requirements,
    python_requires='>=3.5',
    url='https://gitlab.com/tiagocoutinho/vacuum',
    version="0.2.0",
    zip_safe=True,
)
