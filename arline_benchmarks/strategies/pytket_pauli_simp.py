# Copyright (C) 2019-2020 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import CompressionStrategy
from arline_ml.quantum.gate_chain.pytket_converter import PytketGateChainConverter
from arline_quantum.gate_chain.basis_translator import ArlineTranslator
from arline_quantum.gate_sets.cx_rz_rx import CnotRzRxGateSet

from pytket.passes import PauliSimp

_strategy_class_name = "PytketPauliSimp"


class PytketPauliSimp(CompressionStrategy):
    r"""PytketPauliSimp Optimise Strategy
    """

    def run(self, target, run_analyser=True):
        unique_gates = set([g.gate.name for g in target.chain])
        if not all(g in CnotRzRxGateSet().get_gate_list_str() for g in unique_gates):
            gate_chain = ArlineTranslator().rebase_to_cx_rz_rx(target)
        else:
            gate_chain = target
        circuit_object = PytketGateChainConverter().from_gate_chain(gate_chain)

        start_time = timer()

        PauliSimp().apply(circuit_object)

        self.execution_time = timer() - start_time

        gate_chain = PytketGateChainConverter().to_gate_chain(circuit_object)
        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
