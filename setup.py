#!/usr/bin/env python3
"""
RelationOS Setup - MBSE Relation Analysis System
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="relationos",
    version="2.0.0",
    author="RelationOS Team",
    author_email="contact@relationos.org",
    description="ML-powered MBSE relation analysis and classification system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AlotfyDev/RelationOS",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "gpu": ["torch[cuda]>=2.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "relationos=analyzer.commands.cli:main",
            "relationos-harvest=scripts.harvest:main",
        ],
    },
    include_package_data=True,
    package_data={
        "analyzer": [
            "config/*.json",
            "config/*.md",
        ],
    },
    keywords="mbse, sysml, uml, relation, analysis, classification, ml, transformer",
    project_urls={
        "Bug Reports": "https://github.com/AlotfyDev/RelationOS/issues",
        "Source": "https://github.com/AlotfyDev/RelationOS",
        "Documentation": "https://github.com/AlotfyDev/RelationOS#readme",
    },
)