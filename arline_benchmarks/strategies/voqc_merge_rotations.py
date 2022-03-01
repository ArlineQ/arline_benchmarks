# Copyright (C) 2019-2020 Turation Ltd

from timeit import default_timer as timer

from arline_quantum.gate_chain.gate_chain import GateChain
from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_ml.quantum.gate_chain.pytket_converter import PytketGateChainConverter

from qiskit import QuantumCircuit

from pyvoqc.voqc import VOQC
from pyvoqc.qiskit.voqc_optimization import QisVOQC
from qiskit.transpiler import PassManager

from arline_quantum.gate_chain.basis_translator import ArlineTranslator
from arline_quantum.gate_sets.voqc import VoqcGateSet

_strategy_class_name = "VoqcMergeRotations"


class VoqcMergeRotations(CompressionStrategy):
    r"""VOQC Merge Single-Qubit Rotations Strategy
    """

    def run(self, target, run_analyser=True):
        # Perform preliminrary rebase to comply with supported VOQC gates
        unique_gates = set([g.gate.name for g in target.chain])
        if not all(g in VoqcGateSet().get_gate_list_str() for g in unique_gates):
            gate_chain = ArlineTranslator().rebase_to_voqc(target)
        else:
            gate_chain = target
        circuit_object = gate_chain.convert_to("qiskit")

        start_time = timer()

        # Append VOQC pass without argument to the Pass Manager
        pm = PassManager()
        pm.append(QisVOQC(["merge_rotations"]))
        new_circuit = pm.run(circuit_object)

        self.execution_time = timer() - start_time

        gate_chain = GateChain.convert_from(new_circuit, "qiskit")
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
