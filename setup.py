try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='SimpactPurple',
    version='1.1.0',
    author='S. Lucio Tolentino',
    author_email='sean-tolentino@uiowa.edu',
    packages=['simpactpurple','simpactpurple/distributed'],
    url='http://pypi.python.org/pypi/SimpactPurple/',
    license='LICENSE.txt',
    description='Agent-based HIV modeling tool.',
    long_description=open('README.md').read(),
    install_requires=[
        "networkx >= 0.1.4",
    ],
)
