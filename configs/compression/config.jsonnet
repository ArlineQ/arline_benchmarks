// Arline Benchmarks
// Copyright (C) 2019-2020 Turation Ltd
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


// List of compilation pipelines:
//    target -- class of target circuits, e.g. random_chain_cliford_t_target or circuits from .qasm
//    hardware -- class of hardware [defined by vendor and connectivity map], e.g. IbmAll2all or IbmRueschlikon
//    plot_group -- auxillary parameter, needed for plotter and LaTeX report generator,
//                  '2q' for kAk benchmarking, 'multiqubit' for general case benchmarking

local target_analysis = { id: 'target_analysis', config: { strategy: 'target_analysis' } };

local final_stage = 'compression';

local pipelines_set(target, hardware, plot_group) = [
  // Qiskit-based compilation pipeline
  {
    id: 'QiskitPl',  // pipeline identificator
    plot_group: plot_group,  // identificator for LaTeX report
    target: target,
    stages: [
      // 'target_analysis' calculates metrics for the input target circuit and saves results to
      //  gate_chain_report.csv. This is not a true compilation stage but it is required for correct
      //  generation of benchmarking report and must be present at the start of each pipeline.
      target_analysis,
      {
        id: 'mapping',  // stage identificator
        config: {
          strategy: 'qiskit_mapping',
          routing_method: 'stochastic',
          seed_transpiler: 1,  // random seed for Qiskit transpiler
          hardware: hardware,
        },
      },
      {
        id: 'compression',
        config: {
          strategy: 'qiskit_compression',
          routing_method: 'stochastic',
          optimization_level: 3,  // Qiskit transpiler optimization level, can take values (0,1,2,3)
          seed_transpiler: 1,
          hardware: hardware,
        },
      },
    ],
  },
  // Cirq-based compilation pipeline
  {
    id: 'CirqPl',
    target: target,
    plot_group: plot_group,
    stages: [
      target_analysis,
      {
        id: 'mapping',
        config: {
          strategy: 'cirq_mapping',
          hardware: hardware,
        },
      },
      {
        id: 'compression',
        config: {
          strategy: 'cirq_compression',
          hardware: hardware,
        },
      },
    ],
  },
];

// Define random circuit targets from [Clifford, T] gate set
local random_chain_cliford_t_target(num_qubits, chain_length) = {
  task: 'circuit_transformation',
  name: 'random_chain_clifford_t_' + num_qubits + 'q_' + chain_length,  // random chain identificator
  hardware: {
    name: 'CliffordTAll2All',  // name of hardware class [determines gateset of generated target circuit]
    args: {
      num_qubits: num_qubits,
    },
  },
  algo: 'random_chain',
  number: 10,  // number of circuits to be generated
  seed: 10,  // random seed
  // We define uniform distribution of gate probabilities in the gate chain.
  // Two-qubit gates acting on different qubits are sampled independently.
  // For N qubit circuits number of distinct CNOT placements is N*(N-1), so
  // that for large N probability of CNOT gates will be small.
  gate_distribution: 'uniform',
  chain_length: chain_length,  // total number of gates in the chain
};

// Define random circuit targets for [U3, CX] gate set
// (U3 has 3 random angles phi, theta, psi drawn from uniform distribution [0, 2*pi])
local random_chain_cx_u3_target(num_qubits, chain_length) = {
  task: 'circuit_transformation',
  name: 'random_chain_cx_u3_' + num_qubits + 'q_' + chain_length,  // random chain identificator
  hardware: {
    gate_set: ['U3', 'Cnot'],
    num_qubits: num_qubits,
  },
  algo: 'random_chain',
  number: 10,  // number of circuits to be generated
  seed: 10,  // random seed
  // We define uniform distribution of gate probabilities in the gate chain.
  // Two-qubit gates acting on different qubits are sampled independently.
  // For N qubit circuits number of distinct CNOT placements is N*(N-1), so
  // that for large N probability of CNOT gates will be small.
  gate_distribution: 'uniform',
  chain_length: chain_length,  // total number of gates in the chain
};

// Define qasm targets from a predefined circuit dataset (the dataset can be easily extended)
local qasm_circuits_target = {
  name: 'QASM',
  task: 'circuit_transformation',
  algo: 'qasm',
  number: null,
  // List of paths of .qasm circuits
  // To run benchmark for all .qasm circuits in the folder provide the
  // path to the folder instead, e.g. -> qasm_path: '../../circuits/'
  qasm_path: [
    '../../circuits/rd53_135.qasm',
    '../../circuits/mini-alu_167.qasm',
    '../../circuits/C17_204.qasm',
    '../../circuits/sym9_146.qasm',
    '../../circuits/one-two-three-v0_97.qasm',
  ],
};

// Lets list all hardware of interest for benchmarking

// First - 2 qubit IBM hardware for kAk benchmarking
local hardware_2q = [
  {
    name: 'IbmAll2All',
    args: {
      num_qubits: 2,
    },
  },
];

// Second - 16 qubit IBM hardware
local hardware_16q = [
  {
    name: 'IbmAll2All',  // IBM hardware with all-to-all connectivity
    args: {
      num_qubits: 16,
    },
  },
  {
    name: 'IbmRueschlikonSymmetrical',  // IBM Rueschlikon 16q hardware with symmetrized connectivity map
    args: {},
  },
];
// Now we finally define parameters of benchmarking experiment
// Nested .jsonnet lists expressed via "for loops" allow to
// generate all possible combinations of targets, hardware and compilation pipelines
// subject to benchmarking.
local fig_format = 'pdf';
{
  pipelines:
    std.flattenArrays([  // 2 qubit benchmarks
      pipelines_set(target, hardware, '2qubit')
      for hardware in hardware_2q
      for target in [random_chain_cliford_t_target(num_qubits=2, chain_length=120)]
    ]) +
    std.flattenArrays(  // 16 qubit benchmarks
      [
        pipelines_set(target, hardware, 'multiqubit')
        for hardware in hardware_16q
        for target in [
          // random circuit target
          random_chain_cliford_t_target(num_qubits=16, chain_length=120),
          // random target built from u3 and cnot gates
          random_chain_cx_u3_target(num_qubits=16, chain_length=120),
          // target circuits from .qasm dataset
          qasm_circuits_target,
        ]
      ]
    ),


  // -----------------------------------------------------------------------------
  // Below we define parameters of plotter for generating images for LaTeX report
  // Please ignore these settings unless some tweaks in plots are needed
  // ----------------------------------------------------------------------------
  plotter: {
    local pipelines_settings = {  // {pipeline_id: {name: "Pipeline label on plot", color: "matplotlib color"}}
      CirqPl: { name: 'CirqPl', color: 'g' },
      QiskitPl: { name: 'QiskitPl', color: 'b' },
    },
    local stages_settings = {  // {stage_id: {name: "Stage label on plot", color: "matplotlib color"}}
      target_analysis: { name: 'Target', color: 'b' },
      mapping: { name: 'Mapping', color: 'g' },
      compression: { name: 'Compression', color: 'y' },
    },
    local bars_2q(y_col, baseline_value) = {
      title: y_col,
      plot_function: 'plot_pipelines_comparison_bars',
      fixed_conditions: { 'Plot Group': '2qubit' },
      iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
      additional_args: {
        y_col: y_col,
        baselines: { kAk: { value: baseline_value, style: { linestyle: 'solid', linewidth: 2, color: 'r' } } },
        pipelines_settings: pipelines_settings,
        stages_settings: stages_settings,
      },
      filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'bars_{y_col}.' + fig_format,
    },
    local bars_multiqubit(y_col, yscale) = {
      title: y_col,
      plot_function: 'plot_pipelines_comparison_bars',
      fixed_conditions: { 'Plot Group': 'multiqubit' },
      iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
      additional_args: {
        y_col: y_col,
        pipelines_settings: pipelines_settings,
        stages_settings: stages_settings,
        yscale: yscale,
      },
      filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'bars_{y_col}.' + fig_format,
    },
    local scatter_multiqubit(x_col, y_col, input_stage, output_stage,) = {
      title: '{y_col} vs {x_col}',
      plot_function: 'plot_scatter',
      fixed_conditions: { 'Plot Group': 'multiqubit' },
      iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
      additional_args: {
        x_col: x_col,
        y_col: y_col,
        input_stage: input_stage,
        output_stage: output_stage,
        pipelines_settings: pipelines_settings,
      },
      filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'scatter_{y_col}_vs_{x_col}.' + fig_format,
    },
    local compression_multiqubit(input_stage, output_stage) = {
      title: 'Compression Factor',
      plot_function: 'plot_pipelines_compression_factor',
      fixed_conditions: { 'Plot Group': 'multiqubit' },
      iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
      additional_args: {
        input_stage: input_stage,
        output_stage: output_stage,
        baselines: { 'No compression': { value: 1, style: { linestyle: 'solid', linewidth: 2, color: 'r' } } },
        compression_features: {
          'Depth': { color: 'y' },
          'Total Gate Count': { color: 'r' },
          'Two-Qubit Gate Count': { color: 'b' },
          'Single-Qubit Gate Count': { color: 'g' },
        },
        pipelines_settings: pipelines_settings,
      },
      filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'compression_{input_stage}_to_{output_stage}.' + fig_format,
    },
    local hardware_heatmap_multiqubit(compression_feature, rows_feature, input_stage, output_stage, row_label=null) = {
      title: 'CF({compression_feature})',
      plot_function: 'plot_compression_heatmap',
      fixed_conditions: { 'Plot Group': 'multiqubit' },
      iterative_conditions: ['Test Target Generator Name'],
      additional_args: {
        rows_feature: rows_feature,
        input_stage: input_stage,
        output_stage: output_stage,
        pipelines_settings: pipelines_settings,
        compression_feature: compression_feature,
        row_label: row_label,
      },
      filename: '{Plot Group}/{Test Target Generator Name}/' +
                'comp_heatmap_{compression_feature}_{input_stage}_to_{output_stage}.' + fig_format,
    },
    local target_heatmap_multiqubit(compression_feature, input_stage, output_stage) = {
      title: 'CF({compression_feature})',
      plot_function: 'plot_compression_heatmap',
      fixed_conditions: { 'Plot Group': 'multiqubit' },
      iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
      additional_args: {
        rows_feature: 'Test Target ID',
        input_stage: input_stage,
        output_stage: output_stage,
        pipelines_settings: pipelines_settings,
        compression_feature: compression_feature,
        row_label: 'Target',
      },
      filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'comp_heatmap_{compression_feature}_{input_stage}_to_{output_stage}.' + fig_format,
    },
    plots: [
      // Grid plot with radar subplots
      {
        title: '',
        plot_function: 'plot_compression_radar_grid',
        fixed_conditions: { 'Plot Group': 'multiqubit' },
        iterative_conditions: ['Plot Group'],
        additional_args: {
          input_stage: 'target_analysis',
          output_stage: final_stage,
          compression_features: {
            'Total Gate Count': { color: 'r', name: 'CF(Total Gates)' },
            'Two-Qubit Gate Count': { color: 'b', name: 'CF(2Q Gate Count)' },
            'Depth': { color: 'y', name: 'CF(Depth)' },
            'Single-Qubit Gate Count': { color: 'g', name: 'CF(1Q Gate Count)' },
          },
          pipelines_settings: pipelines_settings,
        },
        filename: '{Plot Group}/' +
                  'comp_radar_{input_stage}_to_{output_stage}_grid.' + fig_format,
      },
      bars_2q(y_col='Depth', baseline_value=7),
      bars_2q(y_col='Single-Qubit Gate Count', baseline_value=8),
      bars_2q(y_col='Two-Qubit Gate Count', baseline_value=3),
      bars_2q(y_col='Total Gate Count', baseline_value=11),
      bars_multiqubit('Depth', yscale='linear'),
      bars_multiqubit('Single-Qubit Gate Count', yscale='linear'),
      bars_multiqubit('Two-Qubit Gate Count', yscale='linear'),
      bars_multiqubit('Total Gate Count', yscale='linear'),
      compression_multiqubit(input_stage='target_analysis', output_stage=final_stage),
      compression_multiqubit(input_stage='mapping', output_stage='compression'),
      {
        title: '',
        plot_function: 'plot_compression_radar',
        fixed_conditions: { 'Plot Group': 'multiqubit' },
        iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
        additional_args: {
          input_stage: 'target_analysis',
          output_stage: final_stage,
          baselines: { 'No compression': { value: 1, style: { linestyle: 'solid', linewidth: 2, color: 'r' } } },
          compression_features: {
            'Total Gate Count': { color: 'r', name: 'CF(Total Gates)' },
            'Two-Qubit Gate Count': { color: 'b', name: 'CF(2Q Gate Count)' },
            'Depth': { color: 'y', name: 'CF(Depth)' },
            'Single-Qubit Gate Count': { color: 'g', name: 'CF(1Q Gate Count)' },
          },
          pipelines_settings: pipelines_settings,
        },
        filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                  'comp_radar_{input_stage}_to_{output_stage}.' + fig_format,
      },
      hardware_heatmap_multiqubit(compression_feature='Depth',
                                  rows_feature='Pipeline Output Hardware Name',
                                  input_stage='target_analysis',
                                  output_stage=final_stage,
                                  row_label='Hardware'),
      hardware_heatmap_multiqubit(compression_feature='Total Gate Count',
                                  rows_feature='Pipeline Output Hardware Name',
                                  input_stage='target_analysis',
                                  output_stage=final_stage,
                                  row_label='Hardware'),
      hardware_heatmap_multiqubit(compression_feature='Single-Qubit Gate Count',
                                  rows_feature='Pipeline Output Hardware Name',
                                  input_stage='target_analysis',
                                  output_stage=final_stage,
                                  row_label='Hardware'),
      hardware_heatmap_multiqubit(compression_feature='Two-Qubit Gate Count',
                                  rows_feature='Pipeline Output Hardware Name',
                                  input_stage='target_analysis',
                                  output_stage=final_stage,
                                  row_label='Hardware'),
      {
        title: 'Execution Time',
        plot_function: 'plot_pipelines_comparison_bars',
        fixed_conditions: { 'Plot Group': 'multiqubit' },
        iterative_conditions: ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
        additional_args: {
          y_col: 'Execution Time',
          pipelines_settings: pipelines_settings,
          stages_settings: {
            mapping: { name: 'Mapping', color: 'g' },
            compression: { name: 'Compression', color: 'y' },
          },
          yscale: 'log',
        },
        filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                  'bars_Execution Time.' + fig_format,
      },
      scatter_multiqubit(x_col='Input Depth',
                         y_col='Execution Time',
                         input_stage='target_analysis',
                         output_stage=final_stage),
      scatter_multiqubit(x_col='Single-Qubit Gate Count',
                         y_col='Two-Qubit Gate Count',
                         input_stage='target_analysis',
                         output_stage=final_stage),
      scatter_multiqubit(x_col='Depth',
                         y_col='Two-Qubit Gate Count',
                         input_stage='target_analysis',
                         output_stage=final_stage),
      scatter_multiqubit(x_col='Depth',
                         y_col='Total Gate Count',
                         input_stage='mapping',
                         output_stage='compression'),
      target_heatmap_multiqubit(compression_feature='Depth',
                                input_stage='mapping',
                                output_stage='compression'),
      target_heatmap_multiqubit(compression_feature='Total Gate Count',
                                input_stage='mapping',
                                output_stage='compression'),
      target_heatmap_multiqubit(compression_feature='Single-Qubit Gate Count',
                                input_stage='mapping',
                                output_stage='compression'),
      target_heatmap_multiqubit(compression_feature='Two-Qubit Gate Count',
                                input_stage='mapping',
                                output_stage='compression'),
      target_heatmap_multiqubit(compression_feature='Depth',
                                input_stage='target_analysis',
                                output_stage=final_stage),
      target_heatmap_multiqubit(compression_feature='Total Gate Count',
                                input_stage='target_analysis',
                                output_stage=final_stage),
      target_heatmap_multiqubit(compression_feature='Single-Qubit Gate Count',
                                input_stage='target_analysis',
                                output_stage=final_stage),
      target_heatmap_multiqubit(compression_feature='Two-Qubit Gate Count',
                                input_stage='target_analysis',
                                output_stage=final_stage),
      {
        title: '{Pipeline ID}',
        plot_function: 'plot_gate_composition',
        fixed_conditions: { 'Plot Group': 'multiqubit' },
        iterative_conditions: ['Test Target Generator Name', 'Pipeline ID', 'Pipeline Output Hardware Name'],
        additional_args: {
          stages_settings: stages_settings,
        },
        filename: '{Plot Group}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                  'gate_composition_heatmap_{Pipeline ID}.' + fig_format,
      },

    ],
  },
}
