# Copyright (c) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.gate_chain import GateChain

import pyzx as zx

_strategy_class_name = "PyzxCliffordSimp"


class PyzxCliffordSimp(CompressionStrategy):
    r"""PyZX Clifford Simplify Strategy
    """

    def run(self, target, run_analyser=True):
        qasm_data = target.to_qasm(qreg_name="q", creg_name="c")

        start_time = timer()

        # Convert qasm into circuit
        graph = zx.sqasm(qasm_data)

        # Perform Clifford optimization of PyZX graph
        zx.simplify.clifford_simp(graph)
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
