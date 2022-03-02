// Arline Benchmarks
// Copyright (C) 2019-2022 Turation Ltd
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.


// This is .jsonnet configuration file that defines a set of benchmarking experiments with custom compilation pipelines.
// For a quick tutorial on .jsonnet format go to https://jsonnet.org/learning/tutorial.html

// This config will be eventually converted into usual .json format during parsing.
// The purpose of .jsonnet format is to provide sufficient flexibility and allows
// to define nested loops over benchmarking parameters [e.g. hardware, target circuits, compilation pipeline].


// target -- class of target circuits, e.g. random_chain_cliford_t_target or circuits from .qasm
// hardware -- class of hardware [defined by vendor and connectivity map], e.g. IbmAll2all or IbmRueschlikon

local pipeline_config = import 'pipelines.jsonnet';
local plotter_config = import '../reports/plotter.jsonnet';
local latex_config = import '../reports/latex.jsonnet';

// ----------------------------------------------------------------------------
// Define Target
// ----------------------------------------------------------------------------
local chain_length = 120;
local num_chains = 10;


local random_chain_target_list(num_qubits, chain_length, num_chains) = [
  // Define random circuit targets from [Clifford, T] gate set
  {
    task: 'circuit_transformation',
    name: 'random_chain_clifford_t_' + num_qubits + 'q_' + chain_length,  // random chain identificator
    hardware: {
      class: 'CliffordTAll2All',  // name of hardware class [determines gateset of generated target circuit]
      args: {
        num_qubits: num_qubits,
      },
    },
    algo: 'random_chain',
    number: num_chains,  // number of circuits to be generated
    seed: 10,  // random seed
    // We define uniform distribution of gate probabilities in the gate chain.
    // Two-qubit gates acting on different qubits are sampled independently.
    // For N qubit circuits number of distinct CNOT placements is N*(N-1), so
    // that for large N probability of CNOT gates will be small.
    gate_distribution: 'uniform',
    chain_length: chain_length,  // total number of gates in the chain
  },
  // Define random circuit targets for [U3, CNOT] gate set
  // (U3 has 3 random angles phi, theta, psi drawn from uniform distribution [0, 2*pi])
  {
    task: 'circuit_transformation',
    name: 'random_chain_cnot_u3_' + num_qubits + 'q_' + chain_length,  // random chain identificator
    hardware: {
      gate_set: ['U3', 'Cnot'],
      num_qubits: num_qubits,
    },
    algo: 'random_chain',
    number: num_chains,  // number of circuits to be generated
    seed: 10,  // random seed
    // We define uniform distribution of gate probabilities in the gate chain.
    // Two-qubit gates acting on different qubits are sampled independently.
    // For N qubit circuits number of distinct CNOT placements is N*(N-1), so
    // that for large N probability of CNOT gates will be small.
    gate_distribution: 'uniform',
    chain_length: chain_length,  // total number of gates in the chain
  }
];

// Define qasm targets from a predefined circuit dataset (the dataset can be easily extended)
local math_circuits_target_list = [
  {
    name: 'math_qasm_circuits',
    task: 'circuit_transformation',
    algo: 'qasm',
    number: null,
    // List of paths of .qasm circuits
    // To run benchmark for all .qasm circuits in the folder provide the
    // path to the folder instead, e.g. -> qasm_path: '$ARLINE_BENCHMARKS/circuits/'
    qasm_path: [
      '$ARLINE_BENCHMARKS/circuits/rd53_135.qasm',
      '$ARLINE_BENCHMARKS/circuits/mini-alu_167.qasm',
      '$ARLINE_BENCHMARKS/circuits/C17_204.qasm',
      '$ARLINE_BENCHMARKS/circuits/sym9_146.qasm',
      '$ARLINE_BENCHMARKS/circuits/one-two-three-v0_97.qasm',
    ],
  }
];

// ----------------------------------------------------------------------------
// Define Output Hardware
// ----------------------------------------------------------------------------

// First - 2 qubit IBM hardware for kAk benchmarking
local hardware_2q = [
  {
    class: 'IbmAll2All',
    args: {
      num_qubits: 2,
    },
  },
];

// Second - 16 qubit IBM and Rigetti hardware
local hardware_multi_q = [
  {
    class: 'IbmAll2All',  // IBM hardware with all-to-all connectivity
    args: {
      num_qubits: 16,
    },
  },
  {
    class: 'IbmRueschlikonSymmetrical',  // IBM Rueschlikon 16q hardware with symmetrized connectivity map
    args: {},
  },
  /* {
    class: 'RigettiAspenSymmetrical',  // Rigetti Aspen 16q hardware with symmetrized connectivity map
    args: {},
  }, */
];


// ----------------------------------------------------------------------------
// Final Config
// ----------------------------------------------------------------------------
// Now we finally define parameters of benchmarking experiment
// Nested .jsonnet lists expressed via "for loops" allow to
// generate all possible combinations of targets, hardware and compilation pipelines
// subject to benchmarking.
{
  // --------------------------------------------------------------------------
  // Define Parameters of Pipelines
  // --------------------------------------------------------------------------
  pipelines:
    std.flattenArrays( // 2 qubit benchmarks
      [
        pipeline_config.pipelines_set(target, hardware, 'kak')
        for hardware in hardware_2q
        for target in random_chain_target_list(num_qubits=2, chain_length=chain_length, num_chains=num_chains)
      ]
    ) +
    std.flattenArrays(  // 16 qubit benchmarks
      [
        pipeline_config.pipelines_set(target, hardware, 'multiqubit')
        for hardware in hardware_multi_q
        for target in std.flattenArrays(
          [
            random_chain_target_list(num_qubits=16, chain_length=chain_length, num_chains=num_chains),
            math_circuits_target_list,
          ]
        )
      ]
    ),
  // --------------------------------------------------------------------------
  // Define Parameters of Plotter for Generating Images for LaTeX Report
  // --------------------------------------------------------------------------
  plotter:
    plotter_config.plotter_config(
      pipeline_config.pipelines_settings,
      std.flattenArrays([hardware_2q, hardware_multi_q]),
      pipeline_config.compilation_stages_settings,
      pipeline_config.stages_settings,
      pipeline_config.initial_stage,
      pipeline_config.final_stage
    ),
  // --------------------------------------------------------------------------
  // Define Parameters of LaTeX Report
  // --------------------------------------------------------------------------
  latex:
    latex_config.latex_config(
      pipeline_config.initial_stage,
      pipeline_config.final_stage,
      plotter_config.fig_format,
    )
}
