# Copyright (C) 2019-2020 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_ml.quantum.gate_chain.pytket_converter import PytketGateChainConverter

from pytket.transform import Transform
from pytket.passes import PauliSimp, SequencePass, FullPeepholeOptimise

from pytket.routing import Architecture
from pytket.passes import DefaultMappingPass
from pytket.device import Device
from pytket.passes import SynthesiseIBM

_strategy_class_name = "PytketMappingCompression"


class PytketMappingCompression(CompressionStrategy):
    r"""Pytket Mapping+Compression Strategy
    """

    def __init__(
        self,
        hardware,
        analyser_options={},
        chem_pass=False,
    ):
        super().__init__(hardware, analyser_options)
        self.pytket_hardware = self.convert_to_pytket_hardware()
        self.chem_pass = chem_pass

    def run(self, target, run_analyser=True):
        circuit_object = PytketGateChainConverter().from_gate_chain(target)

        start_time = timer()

        # This works only for pytket==0.6.0
        # qubit_placement = LinePlacement(Device(self.pytket_hardware))
        # qubit_placement.place(circuit_object)  # In case of LinePlacement or GraphPlacement
        # qmap = qubit_placement.get_placement_map(circuit_object)

        # Uncomment to impose trivial qubit map
        # qmap = {Qubit(i): Node(i) for i in range(self.quantum_hardware.num_qubits)}
        # place_with_map(circuit_object, qmap)

        # Default qubit mapping
        qmap = None
        if self.chem_pass:
            # Chemistry-tailored optimisation pass
            SequencePass([PauliSimp(), FullPeepholeOptimise()]).apply(circuit_object)
            SynthesiseIBM().apply(circuit_object)
        else:
            # The main optimisation pass (heavy)
            FullPeepholeOptimise().apply(circuit_object)
        # Default mapping pass
        DefaultMappingPass(Device(self.pytket_hardware)).apply(circuit_object)
        # Decomposes all Pytket BRIDGE gates into CX gates
        Transform.DecomposeBRIDGE().apply(circuit_object)
        # Decomposes all SWAP gates into triples of CX gates.
        # If the SWAP is adjacent to a CX, it will prefer to insert in the direction that allows for gate cancellation.
        # When an Architecture is provided, this will prefer to insert the CXs such that fewer need redirecting.
        Transform.DecomposeSWAPtoCX(self.pytket_hardware).apply(circuit_object)
        # Rebase to CX, U1, U3 and optimize
        SynthesiseIBM().apply(circuit_object)
        self.execution_time = timer() - start_time

        gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object, qmap=qmap)
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
