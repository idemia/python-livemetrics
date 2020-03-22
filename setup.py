#!/usr/bin/env python

import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

about = {}
with open('livemetrics/__init__.py', 'r') as f:
    exec(f.read(), about)

setuptools.setup(
    name = 'livemetrics',
    version = about['__version__'],
    author = about['__author__'],
    author_email = "olivier.heurtier@idemia.com",
    license = about['__license__'],
    description = 'LiveMetrics collector and publisher for Python applications',
    long_description = long_description,
    url="https://github.com/idemia/python-livemetrics",
    packages = ['livemetrics','livemetrics.publishers','livemetrics.dashboard'],
    package_data={'livemetrics.dashboard': ['dashboard.html']},
    test_suite = 'tests',
    extras_require = {
        'aiohttp': [
            'aiohttp >= 3.6',
        ],
        'django': [
            'django >= 2.2',
        ],
        'flask': [
            'flask >= 1.0.0',
        ],
        'dashboard': [
            'jinja2 >=2.10.0',
            'PyYAML >= 5.0.0',
        ],
    },
    tests_require = [
        'requests',
        'aiohttp >= 3.6',
        'django >= 2.2',
        'flask >= 1.0.0',
        'jinja2 >=2.10.0',
        'PyYAML >= 5.0.0',
    ],
    entry_points = {
        'console_scripts': ['livemetrics-dashboard=livemetrics.dashboard.dashboard:main'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: CeCILL-C Free Software License Agreement (CECILL-C)",
        "Operating System :: OS Independent",
    ],
)
