from setuptools import setup, find_packages

setup(
    name='eventcenter',
    version='0.0.7',
    author='Ben Sfard',
    author_email='bsfard@gmail.com',
    url='https://github.com/bsfard/event-center',
    packages=find_packages(),

    install_requires=[
        'requests==2.31.0',
        'Flask==3.0.3',
        'Werkzeug==3.0.3',
        'gunicorn==21.2.0',
        'wrapt==1.16.0',
        'eventdispatch @ git+https://github.com/bsfard/event-dispatch.git'
    ]
)
