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


from arline_benchmarks.strategies.strategy import Strategy
from arline_benchmarks.metrics.gate_chain_analyser import GateChainTransformAnalyser

_strategy_class_name = "TargetAnalysis"


class TargetAnalysis(Strategy):
    r"""Dummy strategy to run analyser
    """

    def run(self, target, run_analyser=True):
        if run_analyser:
            self.analyse(target, target)
            self.analyser_report["Execution Time"] = 0
        return target

    def analyse(self, target, result):
        if self.analyser is None:
            self.analyser = GateChainTransformAnalyser()
        self.analyser_report = self.analyser.run_all(target, result)
