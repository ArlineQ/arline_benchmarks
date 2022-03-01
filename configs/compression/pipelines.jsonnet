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


// List of compilation pipelines

// 'target_analysis' calculates metrics for the input target circuit and saves results to
//  gate_chain_report.csv. This is not a true compilation stage but it is required for correct
//  generation of benchmarking report and must be present at the start of each pipeline.


local target_analysis(id='target_analysis') = {
  id: id,
  strategy: 'target_analysis',
  args: {},
};

local initial_stage = 'target_analysis';
local final_stage = 'mapping_compression';

local pipelines_set(target, hardware, test_type) = [
  // Qiskit-based compilation pipeline
  {
    id: 'QiskitPl',  // pipeline identificator
    target: target,
    test_type: test_type,
    stages: [
      target_analysis(),
      {
        id: 'mapping_compression',  // stage identificator
        strategy: 'qiskit_transpile',
        args: {hardware: hardware},
      },
    ],
  },
  // Cirq-based compilation pipeline
  {
    id: 'CirqPl',
    target: target,
    test_type: test_type,
    stages: [
      target_analysis(),
      {
        id: 'mapping_compression',
        strategy: 'cirq_mapping_compression',
        args: {hardware: hardware},
      },
    ],
  },
];

local pipelines_settings = {  // {pipeline_id: {name: "Pipeline label on plot", color: "matplotlib color"}}
  CirqPl: { name: 'CirqPl', color: 'indianred' },
  QiskitPl: { name: 'QiskitPl', color: 'mediumturquoise' },
};
local compilation_stages_settings = {  // {stage_id: {name: "Stage label on plot", color: "matplotlib color"}}
  mapping_compression: { name: 'Mapping+Compression', color: 'teal' },
  unroll: {name: 'Unroll', color: 'turquoise'},
};
local stages_settings = {  // {stage_id: {name: "Stage label on plot", color: "matplotlib color"}}
  target_analysis: { name: 'Target', color: 'crimson' },
} + compilation_stages_settings;

{
  pipelines_set: pipelines_set,
  pipelines_settings: pipelines_settings,
  compilation_stages_settings: compilation_stages_settings,
  stages_settings: stages_settings,
  initial_stage: initial_stage,
  final_stage: final_stage,
}
