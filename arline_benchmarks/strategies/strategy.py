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


import importlib
from contextlib import suppress

from arline_benchmarks.metrics.gate_chain_analyser import GateChainTransformAnalyser, SynthesisAnalyser
from arline_quantum.hardware import hardware_by_name
from arline_quantum.utils.fidelity import statevector_fidelity


class Strategy:
    r"""Abstract Class for Strategy
    """

    def __init__(
        self,
        analyser_options={}
    ):
        self.execution_time = 0
        self.analyser = None
        self.analyser_report = None
        self.analyser_options = analyser_options

    def run(self, target, run_analyser=True):
        raise NotImplementedError()

    def analyse(self, target, result):
        raise NotImplementedError()

    @staticmethod
    def from_config(cfg):
        strategy_name = cfg["strategy"]
        m = importlib.import_module("arline_benchmarks.strategies." + strategy_name)
        strategy_class = getattr(m, m._strategy_class_name)
        strategy_cfg = cfg["args"]
        return strategy_class(**strategy_cfg)

    def __str__(self):
        s = self.__class__.__name__
        with suppress(AttributeError):
            s += f" ({self.quantum_hardware.name})"
        return s


class CircuitProcessingStrategy(Strategy):
    r"""Abstract Class for Connectivity Mapping Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={}
    ):
        super().__init__(analyser_options)
        self.quantum_hardware = hardware_by_name(hardware)

    def analyse(self, target, result):
        if self.analyser is None:
            self.analyser = GateChainTransformAnalyser(**self.analyser_options)
        self.analyser_report = self.analyser.run_all(target, result)


class MappingStrategy(Strategy):
    r"""Abstract Class for Connectivity Mapping Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={}
    ):
        super().__init__(analyser_options)
        self.quantum_hardware = hardware_by_name(hardware)

    def analyse(self, target, result):
        if self.analyser is None:
            self.analyser = GateChainTransformAnalyser(**self.analyser_options)
        self.analyser_report = self.analyser.run_all(target, result)


class RebaseStrategy(Strategy):
    r"""Abstract Class for Gate Set Rebase Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={}
    ):
        super().__init__(analyser_options)
        self.quantum_hardware = hardware_by_name(hardware)

    def analyse(self, target, result):
        if self.analyser is None:
            self.analyser = GateChainTransformAnalyser(**self.analyser_options)
        self.analyser_report = self.analyser.run_all(target, result)


class CompressionStrategy(Strategy):
    r"""Abstract Class for Compression Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={}
    ):
        super().__init__(analyser_options)
        self.quantum_hardware = hardware_by_name(hardware)

    def analyse(self, target, result):
        if self.analyser is None:
            self.analyser = GateChainTransformAnalyser(**self.analyser_options)
        self.analyser_report = self.analyser.run_all(target, result)


class QSPStrategy(Strategy):
    r"""Abstract Class for QSP Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={}
    ):
        super().__init__(analyser_options)
        self.quantum_hardware = hardware_by_name(hardware)

    def analyse(self, target, result):
        if self.analyser is None:

            def fidelity_function(t, u):
                return statevector_fidelity(t, u)

            self.analyser = SynthesisAnalyser(fidelity_function)
        self.analyser_report = self.analyser.run_all(target, result)
