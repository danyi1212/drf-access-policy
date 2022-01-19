#!/usr/bin/env python
from pathlib import Path

from setuptools import setup


classifiers = [
    # Pick your license as you wish (should match "license" above)
    "License :: OSI Approved :: MIT License",
    "Framework :: Django",
    "Framework :: Django :: 2.2",
    "Framework :: Django :: 3.0",
    "Framework :: Django :: 3.1",
    "Framework :: Django :: 3.2",
    "Framework :: Django :: 4.0",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]
setup(
    name="drf-access-policy",
    version="1.1.0",
    description="Declarative access policies / permissions modeled after AWS' IAM policies.",
    author="Robert Singer",
    author_email="robertgsinger@gmail.com",
    packages=["rest_access_policy"],
    url="https://github.com/rsinger86/drf-access-policy",
    license="MIT",
    keywords="django restframework drf access policy authorization declarative",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    classifiers=classifiers,
    long_description_content_type="text/markdown",
    install_requires=["pyparsing", "djangorestframework"],
)
