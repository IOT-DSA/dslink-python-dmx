from setuptools import setup

setup(
    name="dslink-python-dmx",
    version="0.1.0",
    description="DSLink for Dmx-512",
    url="http://github.com/IOT-DSA/dslink-python-dmx",
    author="Daniel Shapiro",
    author_email="d.shapiro@dglogik.com",
    license="GPL 3",
    install_requires=[
        "txaio",
        "dslink == 0.6.16",
        "pysimpledmx"
    ]
)
