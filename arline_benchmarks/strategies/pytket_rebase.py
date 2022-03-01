# Copyright (c) 2019-2022 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import RebaseStrategy
from arline_quantum.gate_chain.gate_chain import GateChain
from arline_quantum.gate_sets.google import GoogleGateSet
from arline_quantum.gate_sets.ibm import IbmGateSet
from arline_quantum.gate_sets.ionq import IonqGateSet
from arline_ml.quantum.gate_sets.pyzx import PyzxGateSet
from arline_quantum.gate_sets.rigetti import RigettiGateSet
from arline_ml.quantum.gate_chain.pytket_converter import PytketGateChainConverter

from pytket.cirq import tk_to_cirq
from pytket.passes import RebaseCirq, RebaseIBM, RebasePyZX, RebaseQuil, RebaseUMD


_strategy_class_name = "PytketRebase"


class PytketRebase(RebaseStrategy):
    r"""Pytket Gate Rebase Strategy
    """

    def run(self, target, run_analyser=True):
        circuit_object = PytketGateChainConverter().from_gate_chain(target)

        start_time = timer()

        if isinstance(self.quantum_hardware.gate_set, GoogleGateSet):
            RebaseCirq().apply(circuit_object)
        elif isinstance(self.quantum_hardware.gate_set, IbmGateSet):
            RebaseIBM().apply(circuit_object)
        elif isinstance(self.quantum_hardware.gate_set, PyzxGateSet):
            RebasePyZX().apply(circuit_object)
        elif isinstance(self.quantum_hardware.gate_set, RigettiGateSet):
            RebaseQuil().apply(circuit_object)
        elif isinstance(self.quantum_hardware.gate_set, IonqGateSet):  # TODO PhasedX to Rxy
            # RebaseUMD().apply(optimised_circuit)
            raise Exception("PhasedX gate is not implemented yet")
        else:
            raise NotImplementedError()

        self.execution_time = timer() - start_time

        gate_chain = self.save_gate_chain(circuit_object)
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain

    def save_gate_chain(self, circuit_object):
        # Check if this code is still needed
        if isinstance(self.quantum_hardware.gate_set, GoogleGateSet):
            cirq_circuit = tk_to_cirq(circuit_object)
            qasm_data = cirq_circuit.to_qasm()
            lines = qasm_data.split("\n")
            gate_chain = GateChain.from_qasm(lines, self.quantum_hardware)  # TODO set quantum_hardware
            return gate_chain
        else:
            gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object)
            return gate_chain
