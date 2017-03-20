#!/usr/bin/env python
import os
from setuptools import setup

readme = 'README.md'
if os.path.exists('README.rst'):
    readme = 'README.rst'
with open(readme) as f:
    long_description = f.read()

setup(
    name='sanic-gunicorn',
    version='0.1.2',
    author='messense',
    author_email='messense@icloud.com',
    url='https://github.com/messense/sanic-gunicorn',
    keywords='sanic, gunicorn',
    description='Gunicorn worker for Sanic',
    long_description=long_description,
    py_modules=['sanic_gunicorn'],
    install_requires=[
        'sanic>=0.4.1',
        'gunicorn',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
