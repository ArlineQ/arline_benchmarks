# Copyright (C) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_ml.quantum.gate_chain.pytket_converter import PytketGateChainConverter

from pytket.transform import Transform

_strategy_class_name = "PytketPostrouting"


class PytketPostrouting(CompressionStrategy):
    r"""Pytket Optimise Post Routing Strategy
    """

    def run(self, target, run_analyser=True):
        circuit_object = PytketGateChainConverter().from_gate_chain(target)

        start_time = timer()

        # Fast optimisation pass, performing basic simplifications
        # Works on any circuit, giving the result in U1, U2, U3, CX gates.
        # If all multi-qubit gates are CXs, then this preserves their placement and orientation,
        # so it is safe to perform after routing.

        Transform.OptimisePostRouting().apply(circuit_object)
        self.execution_time = timer() - start_time
        gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object)
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
