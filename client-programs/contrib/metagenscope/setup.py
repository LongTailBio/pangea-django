#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

setuptools
setuptools.setup(
    name='metagenscope',
    version='0.1.1',
    author="David C. Danko",
    author_email='dcdanko@gmail.com',
    packages=setuptools.find_packages(),
    package_dir={'metagenscope': 'metagenscope'},
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'pmgs=metagenscope.cli:main'
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
