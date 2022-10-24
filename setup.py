from setuptools import setup, find_packages

setup(
    name='event-center',
    version='0.0.1',
    packages=find_packages(include=['core', 'properties', 'network', 'router', 'service', 'event_center_adapter'])
)
