#!/usr/bin/env python3

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="biql",
    version="0.3.0",
    author="Ashley Stewart",
    description="BIDS Query Language - A powerful SQL-like query language for BIDS neuroimaging datasets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/astewartau/biql",
    project_urls={
        "Bug Reports": "https://github.com/astewartau/biql/issues",
        "Source": "https://github.com/astewartau/biql",
        "Documentation": "https://astewartau.github.io/biql/",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="bids neuroimaging query language sql medical-imaging neuroscience",
    python_requires=">=3.8",
    install_requires=["psutil", "pandas", "tabulate"],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "isort",
            "flake8",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov",
        ],
    },
    entry_points={
        "console_scripts": [
            "biql=biql.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
