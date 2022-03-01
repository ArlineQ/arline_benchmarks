# Copyright (c) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.gate_chain import GateChain
from arline_quantum.gate_chain.basis_translator import ArlineTranslator
from arline_quantum.gate_sets.pyzx import PyzxGateSet
import pyzx as zx

_strategy_class_name = "PyzxFullReduce"


class PyzxFullReduce(CompressionStrategy):
    r"""PyZX Full Reduce Strategy
    """

    def run(self, target, run_analyser=True):
        # Check if all gates in target gate chain are from PyZX gate set
        # If not, than perform rebase to PyZX gate set
        unique_gates = set([g.gate.name for g in target.chain])
        if not all(g in PyzxGateSet().get_gate_list_str() for g in unique_gates):
            gate_chain = ArlineTranslator().rebase_to_pyzx(target)
        else:
            gate_chain = target
        qasm_data = gate_chain.to_qasm(qreg_name="q", creg_name="c")

        start_time = timer()

        # Convert qasm to PyZX circuit object
        graph = zx.sqasm(qasm_data)
        # Fully fledged optimization of PyZX graph (can change graph structure)
        zx.simplify.full_reduce(graph)
        # Convert optimized graph back to circuit
        optimised_circuit = zx.extract_circuit(graph)

        self.execution_time = timer() - start_time

        qasm_data = optimised_circuit.to_qasm()
        lines = qasm_data.split("\n")
        gate_chain = GateChain.from_qasm_list_of_lines(lines, quantum_hardware=None)  # TODO set quantum_hardware
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
