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


from timeit import default_timer as timer

from qiskit.transpiler.passmanager import PassManager
from qiskit.transpiler.passes import Collect2qBlocks
from qiskit.transpiler.passes import ConsolidateBlocks
from qiskit.transpiler.passes import UnitarySynthesis
from qiskit.transpiler.passes import Optimize1qGates

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.gate_chain import GateChain

from qiskit.compiler import transpile

_strategy_class_name = "QiskitKakBlocks"


class QiskitKakBlocks(CompressionStrategy):
    r"""Qiskit kAk 2q blocks Compression Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={},
    ):
        super().__init__(hardware, analyser_options)

    def run(self, target, run_analyser=True):
        circuit_object = target.convert_to("qiskit")
        start_time = timer()
        basis_gates = ['u1', 'u2', 'u3', 'cx']
        passes = [
            Collect2qBlocks(),
            ConsolidateBlocks(basis_gates=basis_gates),
            UnitarySynthesis(basis_gates),
            Optimize1qGates(basis_gates),
        ]
        pm = PassManager().append(passes)
        circuit_object = transpile(circuit_object, pass_manager=pm)

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(circuit_object, format_id="qiskit")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
