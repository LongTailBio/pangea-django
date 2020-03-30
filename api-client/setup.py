#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

setuptools
setuptools.setup(
    name='pangea_api',
    version='0.1.1',
    author="David C. Danko",
    author_email='dcdanko@gmail.com',
    packages=setuptools.find_packages(),
    package_dir={'pangea_api': 'pangea_api'},
    install_requires=[
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
