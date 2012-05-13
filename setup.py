#!/usr/bin/python2
"""
A web interface to ttabler
"""
from setuptools import setup, find_packages, findall

setup(
    name='ttabler-web',
    version='0.1',
    url='http://github.com/aababilov/ttabler-web/',
    license='GNU GPL 3.0',
    author='Alessio Ababilov',
    author_email='ilovegnulinux@gmail.com',
    description='A web interface to ttabler',
    long_description=__doc__,
    packages=find_packages(exclude=["bin", "tests"]),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy'
    ],
    package_data={
        "ttabler_web": [
            "../" + s for s in
                findall("ttabler_web/static") +
                findall("ttabler_web/templates")
        ]
    },
    data_files=[
        ('/etc/ttabler-web', [
            'etc/flask_settings.py',
            'etc/options.properties',
        ]),
    ],
    entry_points={
        'console_scripts': [
            'ttabler-web = ttabler_web.run:main',
            'ttm2html = ttabler_web.ttm2html:main',
            'html2ttm = ttabler_web.html2ttm:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU GPL 3.0',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
