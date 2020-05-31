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
from contextlib import suppress
from timeit import default_timer as timer
from typing import List

import cirq.contrib.routing as ccr
from arline_benchmarks.strategies.strategy import MappingStrategy
from arline_quantum.gate_chain.gate_chain import GateChain
from cirq import CNotPowGate, ExpandComposite, LineQubit, NamedQubit
from cirq.contrib.qasm_import import circuit_from_qasm

_strategy_class_name = "CirqMapping"


class CirqMapping(MappingStrategy):
    r"""Class Wrapper for CirQ Mapping Strategy
    """

    def __init__(self, cfg):
        super().__init__(cfg)
        self.cirq_hardware = self.quantum_hardware.convert_to_cirq_hardware()

    def run(self, target, run_analyser=True):
        with tempfile.TemporaryDirectory() as tmpdirname:
            fname = os.path.join(tmpdirname, "target.qasm")
            target.save_to_qasm(fname, qreg_name="q")
            with open(fname) as file:
                qasm_data = file.read()
        original_circuit = circuit_from_qasm(qasm_data)
        start_time = timer()
        # only 'greedy' routing is implemented in Cirq
        swap_networks: List[ccr.SwapNetwork] = []
        routing_attempts = 1
        with suppress(KeyError):
            routing_attempts = self._cfg["routing_attempts"]
        for _ in range(routing_attempts):
            swap_network = ccr.route_circuit(original_circuit, self.cirq_hardware, router=None, algo_name="greedy")
            swap_networks.append(swap_network)
        assert len(swap_networks) > 0, "Unable to get routing for circuit"
        # Sort by the least number of qubits first (as routing sometimes adds extra ancilla qubits),
        # and then the length of the circuit second.
        swap_networks.sort(key=lambda swap_network: (len(swap_network.circuit.all_qubits()), len(swap_network.circuit)))
        routed_circuit = swap_networks[0].circuit

        qubit_order = {LineQubit(n): NamedQubit(f"q_{n}") for n in range(self.quantum_hardware.num_qubits)}

        # decompose composite gates
        no_decomp = lambda op: isinstance(op.gate, CNotPowGate)
        opt = ExpandComposite(no_decomp=no_decomp)
        opt.optimize_circuit(routed_circuit)

        self.execution_time = timer() - start_time

        qasm_data = routed_circuit.to_qasm(qubit_order=qubit_order)
        lines = qasm_data.split("\n")
        gate_chain = GateChain.from_qasm_list_of_lines(lines, quantum_hardware=None)
        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
