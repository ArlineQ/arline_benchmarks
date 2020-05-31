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


import os
import tempfile
from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.gate_chain import GateChain
from arline_quantum.hardware import hardware_by_name

from qiskit import QuantumCircuit
from qiskit.compiler import transpile

_strategy_class_name = "QiskitCompression"


class QiskitCompression(CompressionStrategy):
    r"""Class Wrapper for Qiskit Compression Strategy
    """

    def __init__(self, cfg):
        super().__init__(cfg)
        self.quantum_hardware = hardware_by_name(self._cfg)
        self.qiskit_hardware = self.quantum_hardware.convert_to_qiskit_hardware()

    def run(self, target, run_analyser=True):
        with tempfile.TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, "target.qasm")
            target.save_to_qasm(fname, qreg_name="q")
            original_circuit = QuantumCircuit.from_qasm_file(fname)

        start_time = timer()
        optimised_circuit = transpile(
            original_circuit,
            backend=self.qiskit_hardware,
            seed_transpiler=self._cfg["seed_transpiler"],
            optimization_level=self._cfg["optimization_level"],
            routing_method=self._cfg["routing_method"],
        )
        self.execution_time = timer() - start_time

        qasm_data = optimised_circuit.qasm()
        lines = qasm_data.split("\n")
        gate_chain = GateChain.from_qasm_list_of_lines(lines, quantum_hardware=None)
        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
