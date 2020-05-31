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


import itertools
from glob import glob
from os import listdir
from os.path import basename, isfile, join, splitext

import numpy as np

from arline_quantum.gate_chain.gate_chain import GateChain
from arline_quantum.gates.u3 import U3
from arline_quantum.hardware import hardware_by_name


def limit_targets_number(f):
    r"""Limits total number of generated circuits (`<=number`), `f` is the target generator
    """

    def g(self):
        if "number" not in self._cfg or not self._cfg["number"] is None and self._cfg["number"] < 0:
            return f(self)

        try:
            self.cnt
        except AttributeError:
            self.cnt = 0

        if self._cfg["number"] is None:
            if self.cnt >= self.number:
                raise StopIteration()
        elif self.cnt >= self._cfg["number"]:
            raise StopIteration()
        self.cnt += 1

        return f(self)

    return g


class Target:
    r"""Abstract class for benchmarking target circuits
    """

    def __init__(self, config={}):
        self._cfg = config
        if "seed" in self._cfg:
            self.seed(self._cfg["seed"])  # TODO test

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        raise NotImplementedError()

    def seed(self, seed=None):
        raise NotImplementedError()

    @staticmethod
    def from_config(config):
        target_classes = [RandomChainTarget, QasmChainTarget]

        cl = {(c.task, c.algo,): c for c in target_classes}[(config["task"], config["algo"])]
        return cl(config)


class GateChainTarget(Target):

    task = "circuit_transformation"


class RandomChainTarget(GateChainTarget):
    r"""Random Chain Target Class

    **Description:**
        Generates random quantum circuits (gate chains) from a discrete gateset
        Supports two types of gate probability distribution in the target generator:

            * Uniform distribution (all gate placements have equal probabilities)
            * Custom probability distribution for each gate placement [e.g. action_probabilities = {"CX_01": 0.1, "CX_10": 0.2, "S_0": 0.5, "S_1": 0.2}]

        Additional optional arguments:
            * Depth limit - maximum depth of generated circuits
            * Two qubit gate count upper bound
            * Two qubit gate count lower bound
            * Total gate count (gate_chain_length)
    """
    algo = "random_chain"

    def __init__(self, config):
        super().__init__(config=config)
        self._quantum_hardware = hardware_by_name(self._cfg)
        self._actions = []
        self.two_qubit_actions = []
        self.id = 0

        try:
            self.depth_limit = self._cfg["depth_limit"]
        except KeyError:
            self.depth_limit = None

        try:
            self.two_qubit_gate_num_upper_bound = self._cfg["two_qubit_gate_num_upper_bound"]
        except KeyError:
            self.two_qubit_gate_num_upper_bound = None

        try:
            self.two_qubit_gate_num_lower_bound = self._cfg["two_qubit_gate_num_lower_bound"]
            assert self.two_qubit_gate_num_upper_bound is not None
            assert self.two_qubit_gate_num_upper_bound - self.two_qubit_gate_num_lower_bound >= 0
        except KeyError:
            self.two_qubit_gate_num_lower_bound = 0

        if self.two_qubit_gate_num_upper_bound is not None and self.depth_limit is not None:
            raise Exception("'two_qubit_gate_num_upper_bound' and 'depth_limit' can not be specified simultaneously.")

        for gate_name, gate in self._quantum_hardware.gate_set.gates_by_name.items():
            for appy_to_qubits in itertools.permutations(range(self._quantum_hardware.num_qubits), gate.num_qubits):
                if len(appy_to_qubits) > 1:
                    if not self._quantum_hardware.qubit_connectivity.check_connection(appy_to_qubits):
                        continue

                action_name = gate_name + ("_{}" * len(appy_to_qubits)).format(*appy_to_qubits)

                if gate.num_qubits == 2 and self.two_qubit_gate_num_upper_bound is not None:
                    self.two_qubit_actions.append((action_name, gate, appy_to_qubits))
                    continue

                self._actions.append((action_name, gate, appy_to_qubits))

        self._actions_probabilities = None
        try:
            if self._cfg["gate_distribution"] == "uniform":
                pass
            else:
                self._actions_probabilities = [None for a in self._actions]

                actions_per_gate = {}
                for action_name, gate, appy_to_qubits in self._actions:
                    try:
                        actions_per_gate[gate.__name__] += 1
                    except KeyError:
                        actions_per_gate[gate.__name__] = 1

                total_p = 0
                for i, a in enumerate(self._actions):
                    action_name, gate, appy_to_qubits = a

                    try:
                        p = self._cfg["gate_distribution"][gate.__name__] / actions_per_gate[gate.__name__]
                        self._actions_probabilities[i] = p
                        total_p += p
                    except KeyError:
                        pass

                empty_p_cnt = sum([1 if p is None else 0 for p in self._actions_probabilities])

                if total_p > 1:
                    raise Exception("The sum of gates probabilies must be <= 1")
                if total_p != 1:
                    if empty_p_cnt == 0:
                        raise Exception("The sum of gates probabilies must be == 1")
                    else:
                        self._actions_probabilities = [
                            p if p is not None else (1 - total_p) / empty_p_cnt for p in self._actions_probabilities
                        ]

                print("Actions probabilities:\n", {a[0]: p for a, p in zip(self._actions, self._actions_probabilities)})

            if self.two_qubit_gate_num_upper_bound is not None and self._actions_probabilities is not None:
                raise Exception(
                    "'two_qubit_gate_num_upper_bound' and 'gate_distribution' can not be specified simultaneously."
                )

        except KeyError:
            pass

    @limit_targets_number
    def next(self):
        self.id += 1
        chain = GateChain(self._quantum_hardware)

        if "chain_length" in self._cfg:
            chain_length = self._cfg["chain_length"]
        elif "chain_length_max" in self._cfg:
            max_length = self._cfg["chain_length_max"]
            min_length = 0
            if "chain_length_max" in self._cfg:
                min_length = self._cfg["chain_length_min"]
            chain_length = self.np_random.randint(min_length, max_length + 1)
        else:
            raise Exception("No chain_length specified")

        two_qubit_pos = []
        if self.two_qubit_gate_num_upper_bound is not None:
            two_qubit_number = self.np_random.randint(
                self.two_qubit_gate_num_lower_bound, self.two_qubit_gate_num_upper_bound + 1
            )
            two_qubit_pos = self.np_random.choice(range(chain_length), two_qubit_number, replace=False)

        for i in range(chain_length):
            if self.depth_limit is not None and chain.get_depth() >= self.depth_limit:
                break

            if i in two_qubit_pos:
                action = self.np_random.choice(range(len(self.two_qubit_actions)))
                action_name, gate_class, appy_to_qubits = self.two_qubit_actions[action]
            else:
                action = self.np_random.choice(range(len(self._actions)), p=self._actions_probabilities)
                action_name, gate_class, appy_to_qubits = self._actions[action]
            if gate_class == U3:
                angles = self.np_random.uniform(low=0, high=2 * np.pi, size=3)
                gate = gate_class(*angles)
            else:
                gate = gate_class()
            chain.add_gate(gate, appy_to_qubits)

        return chain, self.id

    def seed(self, seed=None):
        self.np_random = np.random.RandomState(seed)


class QasmChainTarget(GateChainTarget):
    r"""Qasm Chain Target Class

    **Description:**
        Generates target quantum circuits (gate chains) from a .qasm dataset.
        QASM circuits are stored in folder `arline_benchmarking/benchmarking/circuits`.
    """
    algo = "qasm"  # TODO algo -> type

    def __init__(self, config):
        super().__init__(config=config)
        if isinstance(self._cfg["qasm_path"], str):
            self.qasm_list = glob(join(self._cfg["qasm_path"], "*.qasm"))
        if isinstance(self._cfg["qasm_path"], list):
            self.qasm_list = self._cfg["qasm_path"]
        self.number = len(self.qasm_list)
        self.qasm_number = 0

    @limit_targets_number
    def next(self):
        qasm_f = self.qasm_list[self.qasm_number]
        chain = GateChain.from_qasm(qasm_f, None)
        self.qasm_number += 1
        return chain, splitext(basename(qasm_f))[0]

    def __str__(self):
        return "From QASM {}".format(self.qasm_list[self.qasm_number])
