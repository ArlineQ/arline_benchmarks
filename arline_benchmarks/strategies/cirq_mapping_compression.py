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
from typing import List

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.gate_chain import GateChain
from arline_quantum.qubit_connectivities.qubit_connectivity import All2All
from arline_quantum.gate_sets.cx_rz_rx import CnotRzRxGateSet
from arline_quantum.gate_chain.basis_translator import ArlineTranslator

import cirq.contrib.routing as ccr
from cirq import CNotPowGate, ExpandComposite, LineQubit, NamedQubit

from cirq.optimizers import EjectZ, EjectPhasedPaulis, DropNegligible, DropEmptyMoments
from cirq.optimizers import MergeInteractions
from cirq import merge_single_qubit_gates_into_phased_x_z
from cirq.google.optimizers import optimized_for_xmon

_strategy_class_name = "CirqMappingCompression"


class CirqMappingCompression(CompressionStrategy):
    r"""Cirq Mapping+Compression Strategy
    """

    def __init__(
        self,
        hardware,
        routing_attempts=1,
        router=None,
        algo_name="greedy",
        random_state=1,
        max_search_radius=1,
        analyser_options={},
    ):
        super().__init__(hardware, analyser_options)
        self.cirq_hardware = self.quantum_hardware.convert_to_cirq_hardware()
        self.routing_attempts = routing_attempts
        self.router = router
        self.algo_name = algo_name
        self.random_state = random_state
        self.max_search_radius = max_search_radius

    def run(self, target, run_analyser=True):
        # Check if gates in target gate chain are from ['Cz', 'Rz', 'Rx'] set
        # If gates are not from ['Cz', 'Rz', 'Rx'] set, than perform rebase
        unique_gates = set([g.gate.name for g in target.chain])
        if not all(g in CnotRzRxGateSet().get_gate_list_str() for g in unique_gates):
            gate_chain = ArlineTranslator().rebase_to_cx_rz_rx(target)
        else:
            gate_chain = target

        circuit_object = gate_chain.convert_to("cirq")

        start_time = timer()

        # Skip routing+mapping if hardware has All2All connectivity
        if isinstance(self.quantum_hardware.qubit_connectivity, All2All):
            print("\nAll2All connectivity, skipping routing")
        else:
            # First perform circuit routing
            # only 'greedy' routing is implemented in Cirq
            swap_networks: List[ccr.SwapNetwork] = []
            routing_attempts = self.routing_attempts
            for _ in range(routing_attempts):
                swap_network = ccr.route_circuit(
                    circuit_object,
                    self.cirq_hardware,
                    router=self.router,
                    algo_name=self.algo_name,
                    random_state=self.random_state,
                    max_search_radius=self.max_search_radius
                )
                swap_networks.append(swap_network)
            assert len(swap_networks) > 0, "Unable to get routing for circuit"
            # Sort by the least number of qubits first (as routing sometimes adds extra ancilla qubits),
            # and then the length of the circuit second.
            swap_networks.sort(key=lambda swap_network: (len(swap_network.circuit.all_qubits()), len(swap_network.circuit)))
            circuit_object = swap_networks[0].circuit

            # decompose composite gates
            no_decomp = lambda op: isinstance(op.gate, CNotPowGate)
            ExpandComposite(no_decomp=no_decomp).optimize_circuit(circuit_object)

        # Now run Cirq circuit optimization passes:
        # Convert to Xmon gates (native gates for Google transmon devices)
        # (Essential to get optimal performance)
        circuit_object = optimized_for_xmon(circuit_object)
        # Push Z gates toward the end of the circuit
        EjectZ().optimize_circuit(circuit_object)
        # Push X, Y, and PhasedXPow gates toward the end of the circuit
        EjectPhasedPaulis().optimize_circuit(circuit_object)
        # Merge Interactions pass
        MergeInteractions().optimize_circuit(circuit_object)
        # Merge single-qubit gates into PhasedX and PhasedZ gates
        merge_single_qubit_gates_into_phased_x_z(circuit_object)
        # Drop negligible gates
        DropNegligible().optimize_circuit(circuit_object)
        # Drop empty moments
        DropEmptyMoments().optimize_circuit(circuit_object)

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(circuit_object, format_id="cirq")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
