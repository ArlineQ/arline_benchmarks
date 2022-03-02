# Copyright (C) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_quantum.gate_chain.converters import PytketGateChainConverter

from pytket.transform import RemoveRedundancies

_strategy_class_name = "PytketRemoveRedundancies"


class PytketRemoveRedundancies(CompressionStrategy):
    r"""Pytket RemoveRedundancies Strategy
    (Applies a collection of simple optimisations, such as removing gate-inverse pairs, merging similar rotation gates,
    and removing identity gates. Preserves the gate set and any placement/orientation of multi-qubit gates.)
    """

    def run(self, target, run_analyser=True):
        circuit_object = PytketGateChainConverter().from_gate_chain(target)

        start_time = timer()
        RemoveRedundancies().apply(circuit_object)
        self.execution_time = timer() - start_time
        gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object)
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
