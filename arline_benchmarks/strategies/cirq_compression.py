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

import cirq
from cirq.contrib.qasm_import import circuit_from_qasm
from cirq import NamedQubit

_strategy_class_name = "CirqCompression"


class CirqCompression(CompressionStrategy):
    r"""Class Wrapper for CirQ Compression Strategy
    """

    def __init__(self, cfg):
        super().__init__(cfg)

    def run(self, target, run_analyser=True):
        with tempfile.TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, "target.qasm")
            target.save_to_qasm(fname, qreg_name="q")
            with open(fname) as file:
                qasm_data = file.read()
        optimised_circuit = circuit_from_qasm(qasm_data)

        start_time = timer()
        # Push Z gates toward the end of the circuit
        eject_z = cirq.optimizers.EjectZ()
        eject_z.optimize_circuit(optimised_circuit)
        # Push X, Y, and PhasedXPow gates toward the end of the circuit
        eject_paulis = cirq.optimizers.EjectPhasedPaulis()
        eject_paulis.optimize_circuit(optimised_circuit)
        # Merge single qubit gates into PhasedX and PhasedZ gates
        cirq.merge_single_qubit_gates_into_phased_x_z(optimised_circuit)
        # drop negligible gates
        drop_neg = cirq.optimizers.DropNegligible()
        drop_neg.optimize_circuit(optimised_circuit)
        # drop empty moments
        drop_empty = cirq.optimizers.DropEmptyMoments()
        drop_empty.optimize_circuit(optimised_circuit)
        self.execution_time = timer() - start_time
        qubit_order = {NamedQubit(f'q_{n}'): NamedQubit(f'q_{n}') for n in range(target.quantum_hardware.num_qubits)}
        qasm_data = optimised_circuit.to_qasm(qubit_order=qubit_order)
        lines = qasm_data.split("\n")
        gate_chain = GateChain.from_qasm_list_of_lines(lines, quantum_hardware=None)
        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
