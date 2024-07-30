from setuptools import setup, find_packages


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="pproto-py",
    version="2.0.5",
    description='pproto_py is Python implementation of "Point Of View" communication protocol',
    url="https://github.com/TochkaAI/pproto_py-2.0",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
