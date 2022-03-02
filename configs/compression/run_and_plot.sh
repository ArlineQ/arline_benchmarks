#!/usr/bin/env bash

# Arline Benchmarks
# Copyright (C) 2019-2022 Turation Ltd
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


# run benchmark comparison with configuration defined in ./config.jsonnet
arline-benchmarks-runner -c config.jsonnet -o results/benchmarks

# Draw figures for LaTeX Report
arline-benchmarks-plotter --csv results/benchmarks/gate_chain_report.csv -j config.jsonnet -o results/figures

# Run LaTeX report engine
arline-benchmarks-latex-report-generator -j config.jsonnet -i results -o results/latex_report
