# Copyright (c) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import MappingStrategy
from arline_quantum.gate_chain.converters import PytketGateChainConverter

from pytket.transform import Transform

from pytket.passes import DefaultMappingPass
from pytket.device import Device
from pytket.routing import Architecture

_strategy_class_name = "PytketDefaultMapping"


class PytketDefaultMapping(MappingStrategy):
    r"""Pytket Default Mapping Strategy.
    Constructs a pass to relabel Circuit Qubits to Device Nodes,
    and then routes to the connectivity graph of a :py:class: ‘Device’.
    Edge direction is ignored. Placement used is GraphPlacement.
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
        DefaultMappingPass(Device(self.pytket_hardware)).apply(circuit_object)
        Transform.DecomposeBRIDGE().apply(circuit_object)
        Transform.DecomposeSWAPtoCX(self.pytket_hardware).apply(circuit_object)
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
