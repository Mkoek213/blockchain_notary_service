"""
Setup configuration for blockchain_core library.
Biblioteka core dla systemu blockchain notarialnego.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="blockchain-core",
    version="0.3.0",
    author="Notary Service Team",
    author_email="team@notary-service.local",
    description=(
        "Blockchain Core library for Notary Service - " "moduł bazowy dla systemu notarialnego"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/notary-service/blockchain-core",
    packages=find_packages(exclude=["examples", "tests"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Brak zewnętrznych zależności - czysta implementacja Python
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Tutaj można dodać CLI gdy będzie potrzebne
        ],
    },
)
