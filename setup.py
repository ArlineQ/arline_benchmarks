# Arline Benchmarks
# Copyright (C) 2019-2020 Turation Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="arline-benchmarks",
    version="0.1.4",
    author="Turation Ltd",
    author_email="info@arline.io",
    description="Automated benchmarking platform for quantum compilers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ArlineQ/arline_benchmarks",
    packages=setuptools.find_packages(exclude=['tests*']),
    license="GNU Affero General Public License v3 (AGPLv3)",
    install_requires=[
        "numpy>=1.18.3",
        "scipy>=1.3.1",
        "jsonnet>=0.15.0",
        "pylatex>=1.3.1",
        "py-cpuinfo>=5.0.0",
        "psutil>=5.7.0",
        "pandas>=0.25.3",
        "tqdm>=4.46.0",
        "seaborn>=0.10.1",
        "matplotlib>=3.2.1",
        "cirq~=0.6.0",
        "qiskit~=0.18.0",
        "arline-quantum~=0.1.4",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    scripts=[
        "scripts/arline-benchmarks-runner",
        "scripts/arline-latex-report-generator",
    ],
    python_requires=">=3.6",
    include_package_data=True,
)
