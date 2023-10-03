from setuptools import setup, find_packages

setup(
    name='eventcenter',
    version='0.0.6',
    author='Ben Sfard',
    author_email='bsfard@gmail.com',
    url='https://github.com/bsfard/event-center',
    packages=find_packages(),

    install_requires=[
        'requests==2.31.0',
        'Flask==2.3.3',
        'gunicorn==21.2.0',
        'eventdispatch @ git+https://github.com/bsfard/event-dispatch.git'
    ]
)
