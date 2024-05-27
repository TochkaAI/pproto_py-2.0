from setuptools import setup, find_packages


setup(
    name='pproto-py',
    version='2.0.1',
    description='pproto_py is Python implementation of "Point Of View" communication protocol',
    url="https://github.com/TochkaAI/pproto_py",
    packages=find_packages(),
    python_requires='>=3.10',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)