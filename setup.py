#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# https://python-packaging.readthedocs.io/en/latest/index.html

import io
import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


requirements = [
    'requests       >=2, <3',
    'beautifulsoup4 >=4, <5',
]


dev_requirements = [
    # Publishing
    'bumpversion',

    # Testing
    'tox',
    'pytest',
    'responses      >=0, <1',

    # Helpers
    'ipython',
    'isort',
    'pdbpp',
]


setup(
    name='mal-scraper',
    version='0.4.0',
    license='MIT',
    description='MyAnimeList web scraper',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    author='Qasim K',
    author_email='QasimK@users.noreply.github.com',
    url='https://github.com/QasimK/mal-scraper',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Framework :: Pytest',
        'Framework :: Sphinx',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    keywords=[
        'web', 'scraper', 'library', 'anime', 'data', 'collector'
    ],
    install_requires=requirements,
    extras_require={
        'develop': dev_requirements,
    },
)
