# Copyright (C) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.converters import PytketGateChainConverter

from pytket.passes import FullPeepholeOptimise

_strategy_class_name = "PytketPeephole"


class PytketPeephole(CompressionStrategy):
    r"""Pytket Full Peephole Optimise Strategy
    """

    def run(self, target, run_analyser=True):
        circuit_object = PytketGateChainConverter().from_gate_chain(target)

        start_time = timer()

        # The main optimisation pass (heavy)
        FullPeepholeOptimise().apply(circuit_object)

        self.execution_time = timer() - start_time

        gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object)
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
