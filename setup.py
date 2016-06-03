import os
from setuptools import setup

setup(
    name = 'logparser',
    author = 'Bin Cui',
    version = '1.0.0',
    author_email = 'bin_cui@apple.com',
    packages = ['logparser'],
    scripts=[os.path.join('scripts', 'logparser')],
    include_package_data = True,
    install_requires = ['pyparsing'],
    license = 'Copyright 2016 Apple',
    url = 'https://github.com/bcui6611/logparser',
    keywords = 'analysis logs couchbase',
    description = 'log analysis tool for Couchbase',
    classifiers = [
        'Development Status :: 1 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: Other/Proprietary License',
        'Topic :: Database',
        'Topic :: Internet :: Log Analysis',
        'Programming Language :: Python :: 2',
    ],
    zip_safe=False,
)

