#!/usr/bin/env python3
"""PyODHeaN

Optimization of District Heating Networks.
"""

from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyodhean',
    version='0.0',
    description='Optimization of District Heating Networks',
    long_description=long_description,
    # url='https://github.com/Nobatek/pyodhean',
    author='Nobatek',
    author_email='jlafrechoux@nobatek.com',
    # license='To be defined',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        # 'License :: ,
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords=[
        'District',
        'Heating',
        'Network',
        'Optimization',
    ],
    packages=find_packages(),
    install_requires=[
        'Pyomo>=5.6',
    ],
)
