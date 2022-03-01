# Copyright (C) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_ml.quantum.gate_chain.pytket_converter import PytketGateChainConverter

from pytket.transform import Transform
from pytket.routing import Architecture

_strategy_class_name = "PytketCxDirected"


class PytketCxDirected(CompressionStrategy):
    r"""Pytket CxDirected Strategy

        (changes direction of CX gates to match topology)
    """

    def __init__(
        self,
        hardware,
        analyser_options={},
    ):
        super().__init__(hardware, analyser_options)
        self.pytket_hardware = self.convert_to_pytket_hardware()

    def run(self, target, run_analyser=True):
        circuit_object = PytketGateChainConverter().from_gate_chain(target)

        start_time = timer()

        # Change direction of CXs if needed (for directed coupling graph)
        Transform.DecomposeCXDirected(self.pytket_hardware).apply(circuit_object)
        self.execution_time = timer() - start_time
        gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object)
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain

    def convert_to_pytket_hardware(self):
        coupling_map = self.quantum_hardware.qubit_connectivity.get_coupling_map()
        topology = [tuple(edge) for edge in coupling_map]
        hardware = Architecture(topology)
        return hardware
