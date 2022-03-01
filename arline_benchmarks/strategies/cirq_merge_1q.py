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

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.gate_chain import GateChain

from cirq import merge_single_qubit_gates_into_phased_x_z


_strategy_class_name = "CirqMerge1Q"


class CirqMerge1Q(CompressionStrategy):
    r"""Strategy for Cirq Merge Single-Qubit Gates into PhasedX and PhasedZ Gates
    """

    def run(self, target, run_analyser=True):
        circuit_object = target.convert_to("cirq")

        start_time = timer()

        # Merge single qubit gates into PhasedX and PhasedZ gates
        merge_single_qubit_gates_into_phased_x_z(circuit_object)

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(circuit_object, format_id="cirq")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
