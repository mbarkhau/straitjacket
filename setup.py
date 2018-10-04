# This file is part of the straitjacket project
# https://github.com/mbarkhau/straitjacket
#
# (C) 2018 Manuel Barkhau (mbarkhau@gmail.com)
# SPDX-License-Identifier: MIT

import pathlib
import setuptools


def project_path(filename):
    return (pathlib.Path(__file__).parent / filename).absolute()


def read(filename):
    with project_path(filename).open(mode="r") as fh:
        return fh.read()


long_description = "\n\n".join((read("README.md"), read("CONTRIBUTING.md"), read("CHANGELOG.md")))


setuptools.setup(
    name="straitjacket",
    license="MIT",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    url="https://github.com/mbarkhau/straitjacket",
    version="201809.2a0",
    keywords="formatter yapf black pyfmt gofmt",
    description="Another uncompromising code formatter.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["straitjacket"],
    package_dir={"": "src"},
    install_requires=["black[d]>=18.9b0"],
    entry_points="""
        [console_scripts]
        sjfmt=straitjacket.sjfmt:main
        sjfmtd=straitjacket.sjfmtd:main
    """,
    python_requires=">=3.6",
    zip_safe=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
