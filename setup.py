#!python3
# setup.py is traditionally used to downlaod adn define packages and dependencies
# Newer projects use pyproject.toml. only one of the two is needed
from setuptools import setup, find_packages

setup(
    name="your_package_name",
    version="0.1.0",
    description="A short description of your package",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=["requests", "numpy"],  # List your dependencies
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
