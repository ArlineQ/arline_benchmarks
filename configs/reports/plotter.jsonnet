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


local fig_format = 'pdf';

local plotter_config(
  pipelines_settings,
  hardware_list,
  compilation_stages_settings,
  stages_settings,
  initial_stage,
  final_stage,
  calculate_fidelity=false
) = {
  local bars(y_col, yscale, baseline_name=null, baseline_value=0, fixed_conditions={}) = {
    title: y_col,
    plot_function: 'plot_pipelines_comparison_bars',
    fixed_conditions: fixed_conditions,
    iterative_conditions: if fixed_conditions=={} then ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'] else ['Pipeline Output Hardware Name', 'Test Target Generator Name'],
    args: {
      y_col: y_col,
      yscale: yscale,
      baseline: if baseline_name==null then {} else {
        name: baseline_name,
        value: baseline_value,
        style: {
          linestyle: 'solid',
          linewidth: 2,
          color: 'crimson'
        },
      },
      pipelines_settings: pipelines_settings,
      stages_settings: stages_settings,
    },
    filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' + 'bars_{y_col}.' + fig_format,
  },
  local scatter(x_col, y_col, input_stage, output_stage) = {
    title: '{y_col} vs {x_col}',
    plot_function: 'plot_scatter',
    fixed_conditions: {},
    iterative_conditions: ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'],
    args: {
      x_col: x_col,
      y_col: y_col,
      input_stage: input_stage,
      output_stage: output_stage,
      pipelines_settings: pipelines_settings,
    },
    filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
              'scatter_{y_col}_vs_{x_col}.' + fig_format,
  },
  local compression(input_stage, output_stage) = {
    title: 'Compression Factor',
    plot_function: 'plot_pipelines_compression_factor',
    fixed_conditions: {},
    iterative_conditions: ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'],
    args: {
      input_stage: input_stage,
      output_stage: output_stage,
      baseline: {
        name: 'No compression',
        value: 1,
        style: {
          linestyle: 'solid',
          linewidth: 2,
          color: 'crimson'
        },
      },
      compression_features: {
        Depth: { color: 'teal' },
        'Single-Qubit Gate Depth': { color: 'indigo' },
        'Two-Qubit Gate Depth': { color: 'darkred' },
        'Total Gate Count': { color: 'green' },
        'Single-Qubit Gate Count': { color: 'lightcoral' },
        'Two-Qubit Gate Count': { color: 'magenta' },
      },
      pipelines_settings: pipelines_settings,
    },
    filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
              'compression_{input_stage}_to_{output_stage}.' + fig_format,
  },
  local hardware_heatmap(compression_feature, rows_feature, input_stage, output_stage, row_label=null) = {
    title: 'CF({compression_feature})',
    plot_function: 'plot_compression_heatmap',
    fixed_conditions: {},
    iterative_conditions: ['Test Type', 'Test Target Generator Name'],
    args: {
      rows_feature: rows_feature,
      input_stage: input_stage,
      output_stage: output_stage,
      pipelines_settings: pipelines_settings,
      compression_feature: compression_feature,
      row_label: row_label,
    },
    filename: '{Test Type}/{Test Target Generator Name}/' +
              'comp_heatmap_{compression_feature}_{input_stage}_to_{output_stage}.' + fig_format,
  },
  local target_heatmap(compression_feature, input_stage, output_stage) = {
    title: 'CF({compression_feature})',
    plot_function: 'plot_compression_heatmap',
    fixed_conditions: {},
    iterative_conditions: ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'],
    args: {
      rows_feature: 'Test Target ID',
      input_stage: input_stage,
      output_stage: output_stage,
      pipelines_settings: pipelines_settings,
      compression_feature: compression_feature,
      row_label: 'Target',
    },
    filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
              'comp_heatmap_{compression_feature}_{input_stage}_to_{output_stage}.' + fig_format,
  },
  local connectivity_map(hardware_list) = {
    title: '',
    fixed_conditions: {},
    plot_function: 'plot_connectivity_map',
    iterative_conditions: ['Pipeline Output Hardware Name'],
    args: { hardware_list: hardware_list },
    filename: 'coupling_map_{Pipeline Output Hardware Name}.' + fig_format,
  },
  plots: [
    bars(
      y_col='Depth',
      yscale='linear',
      baseline_name='KAK',
      baseline_value=7,
      fixed_conditions = { 'Test Type': 'kak' }
    ),
    bars(
      y_col='Single-Qubit Gate Count',
      yscale='linear',
      baseline_name='KAK',
      baseline_value=8,
      fixed_conditions = { 'Test Type': 'kak' }
    ),
    bars(
      y_col='Two-Qubit Gate Count',
      yscale='linear',
      baseline_name='KAK',
      baseline_value=3,
      fixed_conditions = { 'Test Type': 'kak' }
    ),
    bars(
      y_col='Total Gate Count',
      yscale='linear',
      baseline_name='KAK',
      baseline_value=11,
      fixed_conditions = { 'Test Type': 'kak' }
    ),
    bars(
      y_col='Single-Qubit Gate Depth',
      yscale='linear',
      baseline_name='KAK',
      baseline_value=4,
      fixed_conditions = { 'Test Type': 'kak' }
    ),
    bars(
      y_col='Two-Qubit Gate Depth',
      yscale='linear',
      baseline_name='KAK',
      baseline_value=3,
      fixed_conditions = { 'Test Type': 'kak' }
    ),
    bars(y_col='Depth', yscale='linear', fixed_conditions = { 'Test Type': 'multiqubit' }),
    bars(y_col='Single-Qubit Gate Count', yscale='linear', fixed_conditions = { 'Test Type': 'multiqubit' }),
    bars(y_col='Two-Qubit Gate Count', yscale='linear', fixed_conditions = { 'Test Type': 'multiqubit' }),
    bars(y_col='Total Gate Count', yscale='linear', fixed_conditions = { 'Test Type': 'multiqubit' }),
    bars(y_col='Single-Qubit Gate Depth', yscale='linear', fixed_conditions = { 'Test Type': 'multiqubit' }),
    bars(y_col='Two-Qubit Gate Depth', yscale='linear', fixed_conditions = { 'Test Type': 'multiqubit' }),
  ] + (
    if calculate_fidelity then [
      bars(y_col='Measurement Infidelity', yscale='log'),
    ]
    else [
    ]
  ) + [
    bars(y_col='Circuit Cost Function', yscale='log'),
    compression(input_stage=initial_stage, output_stage=final_stage),
    {
      title: '',
      plot_function: 'plot_compression_radar',
      fixed_conditions: {},
      iterative_conditions: ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'],
      args: {
        input_stage: initial_stage,
        output_stage: final_stage,
        compression_features: {
          Depth: { color: 'teal', name: 'CF(Depth)' },
          'Single-Qubit Gate Depth': { color: 'palevioletred', name: 'CF(1Q Gate Depth)' },
          'Two-Qubit Gate Depth': { color: 'thistle', name: 'CF(2Q Gate Depth)' },
          'Total Gate Count': { color: 'tomato', name: 'CF(Total Gates)' },
          'Single-Qubit Gate Count': { color: 'lightcoral', name: 'CF(1Q Gate Count)' },
          'Two-Qubit Gate Count': { color: 'salmon', name: 'CF(2Q Gate Count)' },
        },
        pipelines_settings: pipelines_settings,
      },
      filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'comp_radar_{input_stage}_to_{output_stage}.' + fig_format,
    },
    {
      title: '',
      plot_function: 'plot_compression_radar',
      fixed_conditions: {},
      iterative_conditions: ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'],
      args: {
        input_stage: initial_stage,
        output_stage: final_stage,
        compression_features: {
          Depth: { color: 'teal', name: 'CF(Depth)' },
          'Two-Qubit Gate Depth': { color: 'thistle', name: 'CF(2Q Gate Depth)' },
          'Total Gate Count': { color: 'tomato', name: 'CF(Total Gates)' },
          'Two-Qubit Gate Count': { color: 'salmon', name: 'CF(2Q Gate Count)' },
          'Circuit Cost Function': { color: 'palevioletred', name: 'Cost Improvement'},
        },
        pipelines_settings: pipelines_settings,
      },
      filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'comp_radar_with_cost_{input_stage}_to_{output_stage}.' + fig_format,
    },
    hardware_heatmap(
      compression_feature='Depth',
      rows_feature='Pipeline Output Hardware Name',
      input_stage=initial_stage,
      output_stage=final_stage,
      row_label='Hardware'
    ),
    hardware_heatmap(
      compression_feature='Total Gate Count',
      rows_feature='Pipeline Output Hardware Name',
      input_stage=initial_stage,
      output_stage=final_stage,
      row_label='Hardware'
    ),
    hardware_heatmap(
      compression_feature='Single-Qubit Gate Count',
      rows_feature='Pipeline Output Hardware Name',
      input_stage=initial_stage,
      output_stage=final_stage,
      row_label='Hardware'
    ),
    hardware_heatmap(
      compression_feature='Two-Qubit Gate Count',
      rows_feature='Pipeline Output Hardware Name',
      input_stage=initial_stage,
      output_stage=final_stage,
      row_label='Hardware'
    ),
    hardware_heatmap(
      compression_feature='Single-Qubit Gate Depth',
      rows_feature='Pipeline Output Hardware Name',
      input_stage=initial_stage,
      output_stage=final_stage,
      row_label='Hardware'
    ),
    hardware_heatmap(
      compression_feature='Two-Qubit Gate Depth',
      rows_feature='Pipeline Output Hardware Name',
      input_stage=initial_stage,
      output_stage=final_stage,
      row_label='Hardware'
    ),
    {
      title: 'Execution Time',
      plot_function: 'plot_pipelines_comparison_bars',
      fixed_conditions: {},
      iterative_conditions: ['Test Type', 'Pipeline Output Hardware Name', 'Test Target Generator Name'],
      args: {
        y_col: 'Execution Time',
        pipelines_settings: pipelines_settings,
        stages_settings: compilation_stages_settings,
        yscale: 'log',
      },
      filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'bars_Execution Time.' + fig_format,
    },
    scatter(
      x_col='Total Gate Count',
      y_col='Total Execution Time',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    scatter(
      x_col='Single-Qubit Gate Count',
      y_col='Two-Qubit Gate Count',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    scatter(
      x_col='Depth',
      y_col='Two-Qubit Gate Count',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    scatter(
      x_col='Depth',
      y_col='Total Gate Count',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    scatter(
      x_col='Single-Qubit Gate Count',
      y_col='Single-Qubit Gate Depth',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    scatter(
      x_col='Two-Qubit Gate Count',
      y_col='Two-Qubit Gate Depth',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    target_heatmap(
      compression_feature='Depth',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    target_heatmap(
      compression_feature='Total Gate Count',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    target_heatmap(
      compression_feature='Single-Qubit Gate Count',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    target_heatmap(
      compression_feature='Two-Qubit Gate Count',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    target_heatmap(
      compression_feature='Single-Qubit Gate Depth',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    target_heatmap(
      compression_feature='Two-Qubit Gate Depth',
      input_stage=initial_stage,
      output_stage=final_stage
    ),
    {
      title: '{Pipeline ID}',
      plot_function: 'plot_gate_composition',
      fixed_conditions: {},
      iterative_conditions: ['Test Type', 'Test Target Generator Name', 'Pipeline ID', 'Pipeline Output Hardware Name'],
      args: {
        stages_settings: stages_settings,
      },
      filename: '{Test Type}/{Test Target Generator Name}/{Pipeline Output Hardware Name}/' +
                'gate_composition_heatmap_{Pipeline ID}.' + fig_format,
    },
    // Grid plot with radar subplots
    {
      title: '',
      plot_function: 'plot_compression_radar_grid',
      fixed_conditions: {},
      iterative_conditions: ['Test Type'],
      args: {
        input_stage: initial_stage,
        output_stage: final_stage,
        compression_features: {
          Depth: { color: 'teal', name: 'CF(Depth)' },
          'Single-Qubit Gate Depth': { color: 'palevioletred', name: 'CF(1Q Gate Depth)' },
          'Two-Qubit Gate Depth': { color: 'thistle', name: 'CF(2Q Gate Depth)' },
          'Total Gate Count': { color: 'tomato', name: 'CF(Total Gates)' },
          'Single-Qubit Gate Count': { color: 'lightcoral', name: 'CF(1Q Gate Count)' },
          'Two-Qubit Gate Count': { color: 'salmon', name: 'CF(2Q Gate Count)' },
        },
        pipelines_settings: pipelines_settings,
      },
      filename: '{Test Type}/comp_radar_{input_stage}_to_{output_stage}_grid.' + fig_format,
    },
    // Grid plot with radar subplots
    {
      title: '',
      plot_function: 'plot_compression_radar_grid',
      fixed_conditions: {},
      iterative_conditions: ['Test Type'],
      args: {
        input_stage: initial_stage,
        output_stage: final_stage,
        compression_features: {
          Depth: { color: 'teal', name: 'CF(Depth)' },
          'Two-Qubit Gate Depth': { color: 'thistle', name: 'CF(2Q Gate Depth)' },
          'Total Gate Count': { color: 'tomato', name: 'CF(Total Gates)' },
          'Two-Qubit Gate Count': { color: 'salmon', name: 'CF(2Q Gate Count)' },
          'Circuit Cost Function': { color: 'palevioletred', name: 'Cost Improvement'},
        },
        pipelines_settings: pipelines_settings,
      },
      filename: '{Test Type}/comp_radar_with_cost_{input_stage}_to_{output_stage}_grid.' + fig_format,
    },
    connectivity_map(hardware_list),
  ]
};



{
  plotter_config: plotter_config,
  fig_format: fig_format,
}
