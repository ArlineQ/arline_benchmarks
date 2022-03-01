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
from arline_quantum.gate_chain.basis_translator import ArlineTranslator
from arline_quantum.gate_sets.cx_rz_rx import CnotRzRxGateSet

from cirq.optimizers import EjectZ

_strategy_class_name = "CirqEjectZ"


class CirqEjectZ(CompressionStrategy):
    r"""Strategy for Cirq Push Z Gates Toward the End of the Circuit
    """

    def run(self, target, run_analyser=True):
        unique_gates = set([g.gate.name for g in target.chain])
        if not all(g in CnotRzRxGateSet().get_gate_list_str() for g in unique_gates):
            gate_chain = ArlineTranslator().rebase_to_cx_rz_rx(target)
        else:
            gate_chain = target
        circuit_object = gate_chain.convert_to("cirq")

        start_time = timer()

        eject_z = EjectZ()
        eject_z.optimize_circuit(circuit_object)

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(circuit_object, format_id="cirq")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
