from setuptools import setup, find_packages

setup(
    name="ai-code-documenter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "docgen=src.cli:main",
        ],
    },
)
