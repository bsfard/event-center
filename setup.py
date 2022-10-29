from setuptools import setup, find_packages

setup(
    name='eventcenter',
    version='0.0.1',
    author='Ben Sfard',
    author_email='bsfard@gmail.com',
    url='https://github.com/bsfard/event-center',
    packages=find_packages(),

    install_requires=[
        'requests==2.28.1',
        'Flask==2.2.2',
        'eventdispatch @ git+ssh://git@github.com/bsfard/event-dispatch.git@v0.0.1'
    ]
)
