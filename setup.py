from setuptools import find_packages
from setuptools import setup
from pip._internal.req import parse_requirements
import os

with open("README.md", "r") as fh:
    long_description = fh.read()


# Pulls pip packages with versions from the requirements file
install_requires = parse_requirements("requirements.txt", session="snowchange")
test_requires = parse_requirements("requirements.txt", session="snowchnage")

setup(
    name="snowchange",
    version="2.5.0",
    author="jamesweakley/jeremiahhansen/zeitgeistf",
    description="A Database Change Management tool for Snowflake",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Snowflake-Labs/snowchange",
    packages=find_packages(),
    package_dir={"snowchange": "snowchange"},
    setup_requires=[],
    python_requires=">=3.7",
    install_requires=[str(ir.requirement) for ir in install_requires],
    tests_require=[str(tr.requirement) for tr in test_requires],
    entry_points={"console_scripts": ["snowchange=snowchange.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    dependency_links=[],
    include_package_data=True,
)
