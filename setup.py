from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '1.0.0'
DESCRIPTION = 'Distributed Systems Framework'
LONG_DESCRIPTION = 'This package provides a ZeroMq (zmq, 0mq) based distributed systems framework.'

# Setting up
setup(
    name="dividere",
    version=VERSION,
    author="Grant Lipelt",
    author_email="<lipeltgm@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['zmq'],
    keywords=['python', 'ZeroMq', 'zmq', '0mq', 'protobuf'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows"
    ]
)
