from setuptools import find_packages
from setuptools import setup
from pip._internal.req import parse_requirements
import os

with open("README.md", "r") as fh:
    long_description = fh.read()


# Pulls pip packages with versions from the requirements file
install_requires = parse_requirements("requirements.txt", session="schemachange")
test_requires = parse_requirements("requirements.txt", session="schemachange")

setup(
    name="schemachange",
    version="2.9.2",
    author="jamesweakley/jeremiahhansen",
    description="A Database Change Management tool for Snowflake",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Snowflake-Labs/schemachange",
    packages=find_packages(),
    package_dir={"schemachange": "schemachange"},
    setup_requires=[],
    python_requires=">=3.7",
    install_requires=[str(ir.requirement) for ir in install_requires],
    tests_require=[str(tr.requirement) for tr in test_requires],
    entry_points={"console_scripts": ["schemachange=schemachange.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    dependency_links=[],
    include_package_data=True,
)
