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

from arline_benchmarks.strategies.strategy import QSPStrategy
from arline_quantum.gate_chain.gate_chain import GateChain

from qiskit import QuantumCircuit
from qiskit.compiler import transpile

_strategy_class_name = "QiskitQSP"


class QiskitQSP(QSPStrategy):
    r"""Qiskit Compression Strategy
    """

    def __init__(
        self,
        hardware,
        seed_transpiler=1,
        optimization_level=3,
        analyser_options={},
    ):
        super().__init__(hardware, analyser_options)
        self.qiskit_hardware = self.quantum_hardware.convert_to_qiskit_hardware()
        self.seed_transpiler = seed_transpiler
        self.optimization_level = optimization_level

    def run(self, target, run_analyser=True):
        original_circuit = QuantumCircuit(self.quantum_hardware.num_qubits)
        original_circuit.initialize(target, range(self.quantum_hardware.num_qubits))

        start_time = timer()

        optimised_circuit = transpile(
            original_circuit,
            backend=self.qiskit_hardware,
            seed_transpiler=self.seed_transpiler,
            optimization_level=self.optimization_level,
            initial_layout=list(range(self.quantum_hardware.num_qubits)),
        )

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(optimised_circuit, format_id="qiskit")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
