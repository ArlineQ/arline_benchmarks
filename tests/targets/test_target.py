# Copyright (c) 2019-2020 Turation Ltd

import unittest

import numpy as np

from arline_benchmarks.targets.target import RandomChainTarget

from arline_quantum.gates.cnot import Cnot


class TestTarget(unittest.TestCase):
    def test_random_chain_wo_2qubit_limit_creation(self):
        chain_length = 100
        hw_cfg = {
            "gate_set": ["Rx(2*pi/30)", "Cnot"],
            "qubit_connectivity": {
                "adj_matrix": [[0, 1], [1, 0]],
                "args": {
                    "num_qubits": 2,
                }
            }
        }
        target_cfg = {
            "task": "decomposition",
            "algo": "random_chain",
            "number": -1,
            "seed": 10,
            "gate_distribution": "uniform",
            "chain_length": chain_length,
            "hardware": hw_cfg,
        }
        t = RandomChainTarget(target_cfg)

        for i in range(100):
            target_chain, _ = next(t)
            self.assertEqual(len(target_chain), chain_length)

    def test_random_chain_depth_limit(self):
        depth_limit = 5
        hw_cfg = {
            "gate_set": ["Rx(2*pi/30)", "Cnot"],
            "qubit_connectivity": {
                "class": "All2All",
                "args": {
                    "num_qubits": 4,
                }
            }

        }
        target_cfg = {
            "task": "circuit_transformation",
            "algo": "random_chain",
            "number": -1,
            "seed": 10,
            "gate_distribution": "uniform",
            "chain_length": 1000,
            "depth_limit": depth_limit,
            "hardware": hw_cfg,
        }
        t = RandomChainTarget(target_cfg)

        for i in range(100):
            chain, chain_id = next(t)
            self.assertEqual(chain.get_depth(), depth_limit)

    def test_random_chain_gate_distribution(self):
        hw_cfg = {
            "gate_set": ["Rx(2*pi/30)", "Cnot"],
            "qubit_connectivity": {
                "adj_matrix": np.ones((3, 3)).tolist(),
                "args": {
                    "num_qubits": 2,
                }
            }

        }
        target_cfg = {
            "task": "decomposition",
            "algo": "random_chain",
            "number": -1,
            "seed": 10,
            "gate_distribution": {"Rx(2*pi/30)": 0.1, "Cnot": 0.9},
            "chain_length": 1000,
            "hardware": hw_cfg,
        }
        t = RandomChainTarget(target_cfg)

        target_chain, _ = next(t)
        cnt = target_chain.get_gate_count()

        self.assertGreaterEqual(cnt["Rx(2*pi/30)"], 1)
        self.assertGreaterEqual(cnt["Cnot"], 1)

        self.assertGreaterEqual(cnt["Cnot"] / len(target_chain), 0.85)
        self.assertLessEqual(cnt["Cnot"] / len(target_chain), 0.95)

    def test_random_chain_2qubit_limit(self):
        for chain_length in [1, 100]:
            with self.subTest(chain_length=chain_length):
                cnot_number = 1
                hw_cfg = {
                    "gate_set": ["Rx(2*pi/30)", "Cnot"],
                    "qubit_connectivity": {
                        "adj_matrix": [[0, 1], [1, 0]],
                        "args": {
                            "num_qubits": 2,
                        }
                    }
                }

                target_cfg = {
                    "task": "decomposition",
                    "algo": "random_chain",
                    "number": -1,
                    "seed": 10,
                    "gate_distribution": "uniform",
                    "two_qubit_gate_num_upper_bound": cnot_number,
                    "chain_length": chain_length,
                    "hardware": hw_cfg,
                }
                t = RandomChainTarget(target_cfg)

                total_cnot_cnt = 0

                for i in range(100):
                    target_chain, _ = next(t)
                    self.assertLessEqual(target_chain.get_gate_count_by_gate_type(Cnot), cnot_number)
                    self.assertEqual(len(target_chain), chain_length)
                    total_cnot_cnt += target_chain.get_gate_count_by_gate_type(Cnot)

                self.assertGreater(total_cnot_cnt, 0)

    def test_random_chain_exact_2qubit_limit(self):
        for chain_length in [3, 100]:
            with self.subTest(chain_length=chain_length):
                cnot_number = 3
                hw_cfg = {
                    "gate_set": ["Rx(2*pi/30)", "Cnot"],
                    "qubit_connectivity": {
                        "adj_matrix": [[0, 1], [1, 0]],
                        "args": {
                            "num_qubits": 2,
                        }
                    }
                }
                target_cfg = {
                    "task": "decomposition",
                    "algo": "random_chain",
                    "number": -1,
                    "seed": 10,
                    "gate_distribution": "uniform",
                    "two_qubit_gate_num_upper_bound": cnot_number,
                    "two_qubit_gate_num_lower_bound": cnot_number,
                    "chain_length": chain_length,
                    "hardware": hw_cfg,
                }
                t = RandomChainTarget(target_cfg)

                for i in range(100):
                    target_chain, _ = next(t)
                    self.assertLessEqual(target_chain.get_gate_count_by_gate_type(Cnot), cnot_number)
                    self.assertEqual(len(target_chain), chain_length)


if __name__ == "__main__":
    unittest.main()
