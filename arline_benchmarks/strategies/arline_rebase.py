# Copyright (c) 2019-2020 Turation Ltd

from timeit import default_timer as timer

from arline_benchmarks.strategies.strategy import RebaseStrategy
from arline_quantum.gate_sets.google import GoogleGateSet
from arline_quantum.gate_sets.ibm import IbmGateSet
from arline_quantum.gate_sets.ionq import IonqGateSet
from arline_quantum.gate_sets.rigetti import RigettiGateSet
from arline_quantum.gate_sets.pyzx import PyzxGateSet
from arline_quantum.gate_sets.cx_rz_rx import CnotRzRxGateSet
from arline_quantum.gate_sets.arline import ArlineGateSet
from arline_quantum.gate_chain.basis_translator import ArlineTranslator

_strategy_class_name = "ArlineRebase"


class ArlineRebase(RebaseStrategy):
    r"""Class Wrapper for Arline Gate Rebase Strategy
    """

    def run(self, target, run_analyser=True):

        start_time = timer()

        if isinstance(self.quantum_hardware.gate_set, GoogleGateSet):
            gate_chain = ArlineTranslator().rebase_to_google(target)
        elif isinstance(self.quantum_hardware.gate_set, IbmGateSet):
            gate_chain = ArlineTranslator().rebase_to_ibm(target)
        elif isinstance(self.quantum_hardware.gate_set, RigettiGateSet):
            gate_chain = ArlineTranslator().rebase_to_rigetti(target)
        elif isinstance(self.quantum_hardware.gate_set, IonqGateSet):
            gate_chain = ArlineTranslator().rebase_to_ionq(target)
        elif isinstance(self.quantum_hardware.gate_set, PyzxGateSet):
            gate_chain = ArlineTranslator().rebase_to_pyzx(target)
        elif isinstance(self.quantum_hardware.gate_set, CnotRzRxGateSet):
            gate_chain = ArlineTranslator().rebase_to_cx_rz_rx(target)
        elif isinstance(self.quantum_hardware.gate_set, ArlineGateSet):
            gate_chain = ArlineTranslator().rebase_to_arline(target)
        else:
            raise NotImplementedError()

        self.execution_time = timer() - start_time

        gate_chain.quantum_hardware = self.quantum_hardware

        if run_analyser:
            self.analyse(target, gate_chain)
            self.analyser_report["Execution Time"] = self.execution_time
        return gate_chain
