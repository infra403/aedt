"""Setup script for AEDT"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

setup(
    name="aedt",
    version="0.1.0",
    description="AI-Enhanced Delivery Toolkit - 智能 AI 开发编排引擎",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AEDT Team",
    author_email="dev@aedt.io",
    url="https://github.com/aedt/aedt",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "click>=8.0.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aedt=aedt.cli.main:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
