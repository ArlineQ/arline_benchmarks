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

from arline_benchmarks.strategies.strategy import RebaseStrategy
from arline_quantum.gate_chain.gate_chain import GateChain

from qiskit.transpiler.passes import BasisTranslator
from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary as sel
from qiskit.converters import circuit_to_dag, dag_to_circuit

_strategy_class_name = "QiskitRebase"


class QiskitRebase(RebaseStrategy):
    r"""Qiskit Gate Rebase Strategy
    """

    def run(self, target, run_analyser=True):
        original_circuit = target.convert_to("qiskit")

        start_time = timer()

        # Get gate set of quantum hardware object (target gate set)
        gate_set = self.quantum_hardware.gate_set
        basis_gates = list(gate_set.gates_by_qasm_name.keys())
        # Core part of rebase transformation
        dag = circuit_to_dag(original_circuit)
        rebased_dag = BasisTranslator(sel, basis_gates).run(dag)
        optimised_circuit = dag_to_circuit(rebased_dag)

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(optimised_circuit, format_id="qiskit")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
