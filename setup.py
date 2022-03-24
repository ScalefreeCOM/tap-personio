#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-personio",
    version="0.1.0",
    description="Singer.io tap for extracting data",
    author="Scalefree International GmbH",
    url="https://scalefree.com",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_personio"],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        "singer-python==5.12.2",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-personio=tap_personio:main
    """,
    packages=["tap_personio"],
    package_data = {
        "schemas": ["tap_personio/schemas/*.json"]
    },
    include_package_data=True,
)
