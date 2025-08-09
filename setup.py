#!/usr/bin/env python
"""Setup script for FFPSA Pipeline package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="ffpsa-pipeline",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="RAG pipeline for analyzing Title IV-E Prevention Services state plans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ffpsa-pipeline",
    packages=find_packages(exclude=["tests", "tests.*", "Archive", "Archive.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.2.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ffpsa=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["Prompts/**/*.md"],
    },
    zip_safe=False,
)