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

from arline_benchmarks.strategies.strategy import CircuitProcessingStrategy
from arline_quantum.gates.measure import Measure
from arline_quantum.gates.barrier import Barrier

_strategy_class_name = "PreProcessing"


class PreProcessing(CircuitProcessingStrategy):
    r"""Pre-Processing Strategy
    """

    def __init__(
        self,
        hardware,
        add_measure=False,
        combine_regs=True,
        analyser_options={}
    ):
        super().__init__(hardware, analyser_options)
        self.add_measure = add_measure
        self.combine_regs = combine_regs

    def run(self, target, run_analyser=False):
        gate_chain = target.copy()
        start_time = timer()

        if self.combine_regs and len(gate_chain.qreg_mapping) > 1:
            gate_chain.qreg_mapping = {}
            gate_chain.qreg_mapping["q"] = {v: v for v in range(self.quantum_hardware.num_qubits)}

        if self.combine_regs and len(gate_chain.creg_mapping) > 1:
            creg_num = sum([len(r) for r in self.creg_mapping.values()])
            gate_chain.creg_mapping = {}
            gate_chain.creg_mapping["c"] = {v: v for v in range(creg_num)}

        if self.add_measure:
            # Add barrier separator
            qubits = list(range(gate_chain.quantum_hardware.num_qubits))
            gate_chain.add_gate(Barrier(), connections=qubits)
            # Add Measure gates (default creg assignment)
            for q in qubits:
                gate_chain.add_gate(Measure(), connections=[q], cregs=[q])

        self.execution_time = timer() - start_time
        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain