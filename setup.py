from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='smartRM',
    version='1.0',
    author='Andrew Denisevich',
    author_email='andrew.denisevich@gmail.com',
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README')).read()
    }
)