from setuptools import setup

setup(
    name='virtual-patient',
    packages=['cognitiveSQL'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)