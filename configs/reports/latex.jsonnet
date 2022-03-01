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
// The purpose of .jsonnet format is to provide sufficient flexibility.

local latex_config(
  initial_stage,
  final_stage,
  fig_format,
  calculate_fidelity=false,
  compression_radar_with_cost=false,
) = {
  local gate_metrics = [
    {
      name: "Depth",
      fig_name: "depth",
    },
    {
      name: "Total Gate Count",
      fig_name: "total_gate_count",
    },
    {
      name: "Single-Qubit Gate Count",
      fig_name: "single_qubit_gate_count",
    },
    {
      name: "Two-Qubit Gate Count",
      fig_name: "two_qubit_gate_count"
    },
    {
      name: "Single-Qubit Gate Depth",
      fig_name: "single_qubit_gate_depth"
    },
    {
      name: "Two-Qubit Gate Depth",
      fig_name: "two_qubit_gate_depth"
    },
  ],
  local circuit_metrics = (
    if calculate_fidelity then [
      {
        name: "Circuit Cost Function",
        fig_name: "circuit_cost_function",
      },
      {
        name: "Measurement Infidelity",
        fig_name: "measurement_infidelity",
      },
    ]
    else [
      {
        name: "Circuit Cost Function",
        fig_name: "circuit_cost_function",
      },
    ]
  ),
  local time_metrics = [
    {
      name: "Execution Time",
      fig_name: "execution_time",
    }
  ],
  local all_metrics = (
    std.flattenArrays ([
      gate_metrics,
      circuit_metrics,
      time_metrics,
    ])
  ),
  local scatter_fig_list = [
    "total_gate_count_vs_depth",
    "two_qubit_gate_count_vs_depth",
    "two_qubit_gate_count_vs_single_qubit_gate_count",
    "total_execution_time_vs_total_gate_count",
    "single_qubit_gate_depth_vs_single_qubit_gate_count",
    "two_qubit_gate_depth_vs_two_qubit_gate_count",
  ],
  initial_stage: initial_stage,
  final_stage: final_stage,
  fig_format: fig_format,
  gate_metrics: gate_metrics,
  circuit_metrics: circuit_metrics,
  time_metrics: time_metrics,
  all_metrics: all_metrics,
  scatter_fig_list: scatter_fig_list,
  compression_radar_with_cost: compression_radar_with_cost,
};


{
  latex_config: latex_config,
}