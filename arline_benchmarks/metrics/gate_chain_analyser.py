# Arline Benchmarks
# Copyright (C) 2019-2020 Turation Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from arline_quantum.gates import __gates_by_names__

DEBUG = 0


class Analyser:
    """General analyser class
    """
    def __init__(self, anls_list=None):
        self.report = {}
        self.anls_list = None

    def run_all(self, target, gate_chain):
        for f_name in self.available_anls():
            getattr(self, f_name)(target, gate_chain)
        return self.report

    def available_anls(self):
        self.report = {}
        return [a for a in dir(self) if callable(getattr(self, a)) and hasattr(getattr(self, a), "is_analyse_function")]

    def run_selected(self, target, gate_chain):
        for f_name in self.anls_list:
            getattr(self, f_name)(target, gate_chain)
        return self.report


def analyse(anls_func):
    """Call anls function and save result to file
    """

    def anls_and_save(self, target, gate_chain):
        anls_name = anls_func.__name__
        if DEBUG:
            print(anls_name, anls_func(self))
        self.report.update(anls_func(self, target, gate_chain))

    anls_and_save.is_analyse_function = True
    return anls_and_save


class BasicAnalyser(Analyser):
    r"""Basic Gate Chain Analyser Class

    **Description:**
        Returns following relevant metrics:

            * Gate count by gate type
            * Circuit depth
            * Number of populated qubits (qubits involved in calculation)

    """

    def __init__(self):
        super().__init__()

    @analyse
    def depth(self, target, gate_chain):
        return {"Depth": gate_chain.get_depth()}

    @analyse
    def total_gate_count(self, target, gate_chain):
        return {"Total Gate Count": gate_chain.get_num_gates()}

    @analyse
    def gate_count_by_num_qubits(self, target, gate_chain):
        """Gate count by the number of qubits the gate acts on
        """
        n_qubits = set()
        for g in gate_chain.quantum_hardware.gate_set.gate_list:
            n_qubits.add(g.num_qubits)
        r = {n: 0 for n in range(1, max(n_qubits) + 1)}
        for gc in gate_chain.chain:
            r[gc._gate.num_qubits] += 1
        gcm = {}
        for n, v in r.items():
            if n == 1:
                gcm["Single-Qubit Gate Count"] = v
            elif n == 2:
                gcm["Two-Qubit Gate Count"] = v
            else:
                gcm["{n}-Qubit Gate Count"] = v
        return gcm

    @analyse
    def gate_count_by_type(self, target, gate_chain):
        gates_from_chain = gate_chain.get_gate_count()
        return {
            "Count of {} Gates".format(gate_name): gates_from_chain[gate_name] if gate_name in gates_from_chain else 0
            for gate_name in __gates_by_names__.keys()
        }

    @analyse
    def num_populated_qubit(self, target, gate_chain):
        populated_qubits = 0
        for i in range(gate_chain.quantum_hardware.num_qubits):
            if gate_chain.get_num_gates_by_qubit(i) != 0:
                populated_qubits += 1
        return {"Number of Populated Qubits": populated_qubits}


class GateChainTransformAnalyser(BasicAnalyser):
    r"""Gate Chain Transformation Analyser Class

    **Description:**
        Returns additional metrics:

            * Gate chain hardware (hardware class name corresponding to the current compilation pipeline stage)
            * Gate set for the current pipeline stage
            * Total number of qubits in the gate chain

    """

    @analyse
    def gate_chain_hardware(self, target, gate_chain):
        hardw = gate_chain.quantum_hardware
        return {"Gate Chain Hardware": "{}{}Q".format(hardw.name, hardw.num_qubits)}

    @analyse
    def gate_chain_gate_set(self, target, gate_chain):
        gate_set_str = gate_chain.quantum_hardware.gate_set.get_gate_list_str()
        return {"Gate Set": gate_set_str}

    @analyse
    def gate_chain_hardware_number_of_qubits(self, target, gate_chain):
        return {"Gate Chain Number of Qubits": gate_chain.quantum_hardware.num_qubits}

    def __init__(self):
        super().__init__()
