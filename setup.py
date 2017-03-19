#!/usr/bin/env python
import os
from setuptools import setup

readme = 'README.md'
if os.path.exists('README.rst'):
    readme = 'README.rst'
with open(readme) as f:
    long_description = f.read()

setup(
    name='sanic_gunicorn',
    version='0.1.0',
    author='messense',
    author_email='messense@icloud.com',
    url='https://github.com/messense/sanic_gunicorn',
    keywords='sanic, gunicorn',
    description='Gunicorn worker for Sanic',
    long_description=long_description,
    py_modules=['sanic_gunicorn'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
)
