from distutils.core import setup

setup(
    name='SimpactPurple',
    version='0.1.1',
    author='S. Lucio Tolentino',
    author_email='sean-tolentino@uiowa.edu',
    packages=['simpactpurple'],
    url='http://pypi.python.org/pypi/SimpactPurple/',
    license='LICENSE.txt',
    description='Agent-based HIV modeling tool.',
    long_description=open('README.txt').read(),
    install_requires=[
        "numpy >= 1.1.1",
        "networkx >= 0.1.4",
    ],
)
