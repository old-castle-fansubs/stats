from setuptools import setup, find_packages

setup(
    name='nyaa_si',
    version='1.0.0',
    author='rr-',
    author_email='rr-@sakuya.pl',
    description='nyaa.si API',
    packages=find_packages(),
    install_requires=[
        'humanfriendly',
        'lxml',
        'requests',
        'dataclasses'
    ],
)
