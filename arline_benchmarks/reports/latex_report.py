#!/usr/bin/env python3

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


# Importing pylatex package - tool for automated LaTeX generation.
from pylatex import (
    Document,
    Section,
    Subsection,
    Command,
    Itemize,
    Enumerate,
    Math,
    Alignat,
    Hyperref,
    Figure,
    LineBreak,
    NewPage,
    NewLine,
    TextColor,
    FootnoteText,
    Label,
    PageStyle,
    Head,
    Foot,
    simple_page_number,
    LongTabu,
    MultiColumn,
)
from pylatex.section import Chapter
from pylatex.utils import italic, NoEscape, bold
from importlib_metadata import version
from psutil import virtual_memory
from shutil import rmtree
from os import makedirs, path
import arline_benchmarks

import platform
import os
import cpuinfo
import pandas as pd
import numpy as np
import re


class LatexReport:
    r"""Latex Report Analyser Class

    **Description:**

        Calculates additional metrics based on .csv report file.
        These metrics are required for automated analytics and text generation in .tex report file.
    """

    def __init__(self, input_dir, output_dir, config):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config["latex"]
        self.gate_metrics = self.config["gate_metrics"]
        self.circuit_metrics = self.config["circuit_metrics"]
        self.time_metrics = self.config["time_metrics"]
        self.all_metrics = self.config["all_metrics"]
        self.scatter_fig_list = self.config["scatter_fig_list"]
        self.initial_stage = self.config["initial_stage"]
        self.final_stage = self.config["final_stage"]
        self.fig_format = self.config["fig_format"]
        self.compression_radar_with_cost = self.config["compression_radar_with_cost"]

        fname = os.path.join(self.input_dir, "benchmarks", "gate_chain_report.csv")
        fname = os.path.abspath(fname)
        if not os.path.isfile(fname):
            raise FileNotFoundError("Benchmarking report file {:} is not found".format(fname))
        self.df = pd.read_csv(fname)

        self.frameworks = self.df["Pipeline ID"].unique()
        self.hardware_list = set(self.df["Pipeline Output Hardware Name"])

        rmtree(self.output_dir, ignore_errors=True)
        makedirs(self.output_dir)
        filepath = os.path.join(self.output_dir, "benchmark_report")
        self.filepath = os.path.abspath(filepath)
        self.geometry_options = {
            "bindingoffset": "0.2in",
            "left": "1in",
            "right": "1in",
            "top": "1in",
            "bottom": "1in",
            "footskip": "0.25in",
        }
        self.doc = Document(
            documentclass="report", geometry_options=self.geometry_options, default_filepath=self.filepath
        )
        # Analyse Report Content
        self.kak_hardware_list = self.get_kak_hardware_list()
        self.kak_target_list = self.get_kak_target_list()
        self.hardware_list = self.get_not_kak_hardware_list()
        self.target_list = self.get_not_kak_target_list()
        self.kak_chapter = (len(self.kak_hardware_list) != 0)
        self.multi_qubit_chapter = (len(self.hardware_list) != 0)

    def get_kak_hardware_list(self):
        hardw_names = self.df["Pipeline Output Hardware Name"]
        hardw_qubits = self.df["Pipeline Output Number of Qubits"]
        filter = hardw_qubits == 2
        hardw_names = hardw_names[filter]
        hardw_list = set(hardw_names)
        return hardw_list

    def get_not_kak_hardware_list(self):
        hardw_names = self.df["Pipeline Output Hardware Name"]
        hardw_qubits = self.df["Pipeline Output Number of Qubits"]
        filter = hardw_qubits != 2
        hardw_names = hardw_names[filter]
        hardw_list = set(hardw_names)
        return hardw_list

    def get_kak_target_list(self):
        num_qubs = self.df["Pipeline Output Number of Qubits"]
        targ_list = self.df["Test Target Generator Name"][num_qubs == 2].unique()
        return targ_list

    def get_not_kak_target_list(self):
        num_qubs = self.df["Pipeline Output Number of Qubits"]
        targ_list = self.df["Test Target Generator Name"][num_qubs != 2].unique()
        return targ_list

    def get_sum_agg_data(self, hardware, target):
        filter1 = self.df["Test Target Generator Name"] == target
        filter2 = self.df["Pipeline Output Hardware Name"] == hardware
        df = self.df[filter1][filter2]
        sum_data = df.groupby(by=["Pipeline ID"]).aggregate(np.sum)
        sum_data = sum_data.reset_index()
        return sum_data

    def get_min_exec_time_framework(self, hardware, target):
        df = self.get_sum_agg_data(hardware, target)
        idx = df["Execution Time"].idxmin()
        framework = df["Pipeline ID"][idx]
        return framework

    def get_max_exec_time_framework(self, hardware, target):
        df = self.get_sum_agg_data(hardware, target)
        idx = df["Execution Time"].idxmax()
        framework = df["Pipeline ID"][idx]
        return framework

    def get_pipelines_summary(self):
        pipelines_summary = []
        for framework in self.frameworks:
            _df = self.df[self.df["Pipeline ID"] == framework]["Stage ID"]
            stages = list(_df.unique())
            stages.remove("target_analysis")
            pipelines_summary.append({"pipeline": framework, "stages": stages})
        return pipelines_summary

    def target_class_display_name(self, target):
        if "random" in target:
            if "random_chain" in target:
                if "clifford_t" in target:
                    targ_name = "Random Circuits from [Clifford + T] Gate Set"
                    targ_name_lower_case = "random circuits from [Clifford + T] gate set"
                elif "cnot_u3" in target:
                    if "uniform" in target:
                        targ_name = "Random Circuits from [CNOT, U$_3$] Gate Set with Uniform Distribution"
                        targ_name_lower_case = "random circuits from [CNOT, U$_3$] gate set with uniform distribution"
                    elif "high_cnots" in target:
                        targ_name = "Random Circuits from [CNOT, U$_3$] Gate Set with High CNOTs Frequency"
                        targ_name_lower_case = "random circuits from [CNOT, U$_3$] gate set with high CNOTs frequency"
                    elif "low_cnots" in target:
                        targ_name = "Random Circuits from [CNOT, U$_3$] Gate Set with Low CNOTs Frequency"
                        targ_name_lower_case = "random circuits from [CNOT, U$_3$] gate set with low CNOTs frequency"
                    else:
                        targ_name = "Random Circuits from [CNOT, U$_3$] Gate Set"
                        targ_name_lower_case = "random circuits from [CNOT, U$_3$] gate set"
                elif "cnot_only" in target:
                    targ_name = "Random Circuits from [CNOT] Gate Set"
                    targ_name_lower_case = "random circuits from [CNOT] gate set"
                elif "u3_only" in target:
                    targ_name = "Random Circuits from [U$_3$] Gate Set"
                    targ_name_lower_case = "random circuits from [U$_3$] gate set"
                else:
                    targ_name = "Random Circuits"
                    targ_name_lower_case = "random circuits"
        elif "qasm" in target and "block" not in target:
            if "math" in target:
                targ_name = "QASM Circuits for Arithmetic Algorithms"
                targ_name_lower_case = "QASM circuits for arithmetic blocks"
            elif "finance" in target:
                targ_name = "QASM Circuits for Finance Algorithms"
                targ_name_lower_case = "QASM circuits for finance algorithms"
            elif "chemistry" in target:
                targ_name = "QASM Circuits for Quantum Chemistry"
                targ_name_lower_case = "QASM circuits for quantum chemistry"
            elif "toffoli" in target:
                targ_name = "QASM Circuits for Toffoli Gate"
                targ_name_lower_case = "QASM circuits for Toffoli Gate"
            elif "fredkin" in target:
                targ_name = "QASM Circuits for Fredkin Gate"
                targ_name_lower_case = "QASM circuits for Fredkin Gate"
            elif "or" in target:
                targ_name = "QASM Circuits for Or Operation"
                targ_name_lower_case = "QASM circuits for Or Operation"
            elif "peres" in target:
                targ_name = "QASM Circuits for Peres"
                targ_name_lower_case = "QASM circuits for Peres"
            else:
                targ_name = "QASM Circuits"
                targ_name_lower_case = "QASM circuits"
        else:
            targ_name = target.replace("_", "\_")
            targ_name_lower_case = target.replace("_", "\_")
        return targ_name, targ_name_lower_case

    def get_target_summary(self, target, hardware=None, stage_id="target_analysis", framework=None):
        # Filter by particular target class
        filter = self.df["Test Target Generator Name"] == target
        df = self.df[filter]
        if hardware is not None:
            filter = df["Pipeline Output Hardware Name"] == hardware
            df = df[filter]
        if framework is not None:
            filter = df["Pipeline ID"] == framework
            df = df[filter]
        num_targets = len(df["Test Target ID"].unique())
        targ_df = df[df["Stage ID"] == stage_id]

        gates_list = targ_df.filter(regex=("Count of .* Gates"), axis=1)
        g_count_sum = gates_list.sum()
        g_count_sum = g_count_sum[g_count_sum != 0]
        g_frequencies = g_count_sum / g_count_sum.sum()

        g_names = g_frequencies.index.to_list()
        g_names = [re.search("Count of (.*) Gates", g).group(1) for g in g_names]

        # Assumes that all targets for given class have the same number of qubits!
        mean_num_qubits = targ_df["Gate Chain Number of Qubits"].mean()
        mean_depth = targ_df["Depth"].mean()
        mean_1q_gate_count = targ_df["Single-Qubit Gate Count"].mean()
        mean_2q_gate_count = targ_df["Two-Qubit Gate Count"].mean()
        mean_total_gate_count = targ_df["Total Gate Count"].mean()
        target_summary = {
            "gate_frequencies": g_frequencies,
            "gate_names": g_names,
            "mean_num_qubits": mean_num_qubits,
            "num_targets": num_targets,
            "mean_depth": mean_depth,
            "mean_total_gate_count": mean_total_gate_count,
            "mean_two_qubit_gate_count": mean_2q_gate_count,
            "mean_one_qubit_gate_count": mean_1q_gate_count,
        }
        return target_summary

    def max_result_by_feature(self, feature, stage_id, hardware, target):
        """ Examples of features: Depth,
                                  Sngle-Qubit Gate Count,
                                  Two-Qubit Gate Count,
                                  Total Gate Count,
                                  Execution time """
        df = self.df
        conditions = {
            "Pipeline Output Hardware Name": hardware,
            "Stage ID": stage_id,
            "Test Target Generator Name": target,
        }
        for key in conditions.keys():
            cond = conditions[key]
            df = df.loc[df[key] == cond]

        max_feature_val = df[feature].max()
        idx = df[feature].idxmax()
        circuit_id = df["Test Target ID"][idx]
        pipeline_name = df["Pipeline ID"][idx]
        return max_feature_val, circuit_id, pipeline_name

    def min_result_by_feature(self, feature, stage_id, hardware, target):
        """ Examples of features: Depth,
                                  1-Qubit Gate Count,
                                  2-Qubit Gate Count,
                                  Total Gate Count,
                                  Execution time """
        df = self.df
        conditions = {
            "Pipeline Output Hardware Name": hardware,
            "Stage ID": stage_id,
            "Test Target Generator Name": target,
        }

        for key in conditions.keys():
            cond = conditions[key]
            df = df.loc[df[key] == cond]

        min_feature_val = df[feature].min()
        idx = df[feature].idxmin()
        circuit_id = df["Test Target ID"][idx]
        pipeline_name = df["Pipeline ID"][idx]
        return min_feature_val, circuit_id, pipeline_name

    def groupby_framework_mean(self, stage_id, hardware, target):
        df = self.df
        conditions = {
            "Pipeline Output Hardware Name": hardware,
            "Stage ID": stage_id,
            "Test Target Generator Name": target,
        }
        for key in conditions.keys():
            cond = conditions[key]
            df = df.loc[df[key] == cond]

        df_mean = df.groupby(by=["Pipeline ID"]).mean()
        return df_mean

    def get_df_mean_by_hardware(self, feature, hardw_list):
        df = self.df
        df = df[df["Pipeline Output Hardware Name"].isin(hardw_list)]
        df_mean_by_hardware = df.groupby(by=["Pipeline ID", "Pipeline Output Hardware Name"]).aggregate(np.mean)
        df_mean_by_hardware = df_mean_by_hardware.reset_index()
        heat_df = df_mean_by_hardware.pivot(
            index="Pipeline Output Hardware Name", columns="Pipeline ID", values=feature
        )
        return heat_df

    def print_figure(self, test_type, target, hardware, figure_name, fig):
        filename = (
            rf"figures/{test_type}/{target}/{hardware}/{figure_name}.{self.fig_format}"
        )
        filename = os.path.join(self.input_dir, filename)
        filename = os.path.abspath(filename)
        fig.add_image(filename, width=NoEscape(r"0.4\textwidth"))
        return fig

    def print_figure_from_stage_to_stage(
        self, test_type, target, hardware, figure_name, initial_stage, final_stage, fig
    ):
        filename = (
            rf"figures/{test_type}/{target}/{hardware}/{figure_name}_{initial_stage}_to_{final_stage}.{self.fig_format}"
        )
        filename = os.path.join(self.input_dir, filename)
        filename = os.path.abspath(filename)
        fig.add_image(filename, width=NoEscape(r"0.4\textwidth"))
        return fig

    def print_figure_from_initial_to_final_stage(self, test_type, target, hardware, figure_name, fig):
        return self.print_figure_from_stage_to_stage(
            test_type, target, hardware, figure_name, self.initial_stage, self.final_stage, fig
        )

    def add_line_into_target_table(self, metrics, df, table):
        row = [metrics, df[metrics].idxmin(), df[metrics].idxmax()]
        table.add_row(row)
        table.add_hline()
        return table

    def add_line_into_hardware_table(self, metrics, hardware_list, table):
        heat_df = self.get_df_mean_by_hardware(metrics, hardware_list)
        idx_min = heat_df.idxmin()
        idx_max = heat_df.idxmin()
        row = [metrics, idx_min[0], idx_max[0]]
        table.add_row(row)
        table.add_hline()
        return table

    def add_line_into_comp_factor_table(self, metric, hardware, target, table, is_round=False):
        min_val, min_circ, min_pip = self.min_result_by_feature(metric, self.final_stage, hardware, target)
        max_val, max_circ, max_pip = self.max_result_by_feature(metric, self.final_stage, hardware, target)
        if is_round:
            row = [metric, min_pip, min_circ, round(min_val, 3), max_pip, max_circ, round(max_val, 3)]
        else:
            row = [metric, min_pip, min_circ, min_val, max_pip, max_circ, max_val]
        table.add_row(row)
        table.add_hline()
        return table

    def generate_hardware_comparison_section(self, test_type, target, hardware, hardware_list):
        with self.doc.create(Section("Hardware Comparison")):
            self.doc.append("This analysis is performed across all classes of target circuit.")
            with self.doc.create(LongTabu("|l|l|l|", row_height=1.5)) as table:
                table.add_hline()
                table.add_row(["Metrics", "Min", "Max"], mapper=bold, color="lightgray")
                table.add_hline()
                table.end_table_header()
                table.add_row((MultiColumn(3, align="|r|", data="Continued on Next Page"),))
                table.add_hline()
                table.end_table_footer()
                table.end_table_last_footer()
                for i in self.all_metrics:
                    table = self.add_line_into_hardware_table(i["name"], hardware_list, table)
            with self.doc.create(Figure(position="h!")) as fig:
                for i, metric in enumerate(self.gate_metrics):
                    fig = self.print_figure_from_initial_to_final_stage(
                        test_type, target, hardware, f"comp_heatmap_{metric['fig_name']}", fig
                    )
                    if i % 2 == 1:
                        self.doc.append(LineBreak())
                fig.add_caption(NoEscape(r"""Final circuit metrics after compilation vs hardware backend."""))

    def generate_metrics_analysis_subsection(self, test_type, target, hardware):
        self.doc.append(
            Subsection(
                NoEscape(
                    r"""Metrics for each stage of compilation pipeline and aggregate compression factor
                    (initial/final)"""
                ),
                numbering=False,
            )
        )
        self.doc.append(
            NoEscape(
                r"""Note that in most cases single-qubit gate count and single-qubit gate compression factor
                have only limited meaning as a metric of compiler performance.This is because single-qubit
                gate count is very sensitive to the choice single-qubit basis gates (e.g. $U_3$ is
                equivalent to a combination of 3 rotation gates $R_x$, $R_y$ and $R_z$)."""
            )
        )
        with self.doc.create(Figure(position="h!")) as fig:
            for i, metric in enumerate(self.gate_metrics):
                fig = self.print_figure(test_type, target, hardware, f"bars_{metric['fig_name']}", fig)
                if i % 2 == 1:
                    self.doc.append(LineBreak())
            fig.add_caption(
                NoEscape(rf"""Circuits metrics for each compilation pipeline stage for {hardware}.""")
            )
        with self.doc.create(Figure(position="h!")) as fig:
            is_fidelity = 0
            for i, metric in enumerate(self.circuit_metrics):
                fig = self.print_figure(test_type, target, hardware, f"bars_{metric['fig_name']}", fig)
                if metric['name'] == "Measurement Infidelity":
                    is_fidelity == 1
            if is_fidelity:
                fig.add_caption(
                    NoEscape(rf"""Circuit cost function and measurement infidelity for {hardware}.""")
                )
            else:
                fig.add_caption(
                    NoEscape(rf"""Circuit cost function for {hardware}.""")
                )
        with self.doc.create(Figure(position="h!")) as fig:
            fig = self.print_figure_from_initial_to_final_stage(test_type, target, hardware, "compression", fig)
            if self.compression_radar_with_cost:
                fig = self.print_figure_from_initial_to_final_stage(
                    test_type, target, hardware, "comp_radar_with_cost", fig
                )
                fig.add_caption(
                    NoEscape(
                        rf"""Compression factor ($CF$) and Circuit cost improvement between target and final compilation
                        stage for {hardware} (histogram and radar plot).
                        """
                    )
                )
            else:
                fig = self.print_figure_from_initial_to_final_stage(test_type, target, hardware, "comp_radar", fig)
                fig.add_caption(
                    NoEscape(
                        rf"""Compression factor ($CF$) between target and final compilation stage for {hardware}
                        (histogram and radar plot).
                        """
                    )
                )
        self.doc.append(NoEscape(r"\clearpage"))

    def generate_gate_composition_subsection(self, test_type, target, hardware):
        self.doc.append(Subsection(r"""Gate composition for each compilation pipeline stage""", numbering=False))
        with self.doc.create(Figure(position="h!")) as fig:
            for i, framework in enumerate(self.frameworks):
                fig = self.print_figure(
                    test_type, target, hardware, f"gate_composition_heatmap_{framework.lower()}", fig
                )
                if i % 2 == 1:
                    self.doc.append(LineBreak())
            fig.add_caption(NoEscape(rf"""Gate frequencies in each pipeline stage for {hardware}."""))

    def generate_execution_time_stats_subsection(self, test_type, target, hardware):
        self.doc.append(Subsection(r"""Execution time stats """, numbering=False))
        self.doc.append(
            NoEscape(
                """Here we present stats about execution time (in seconds)
                spent by frameworks for each compilation stage."""
            )
        )
        with self.doc.create(Figure(position="h!")) as fig:
            fig = self.print_figure(test_type, target, hardware, "bars_execution_time", fig)
            fig.add_caption(NoEscape(f"""Mean execution time of each compilation stage for {hardware}."""))

    def generate_summary_stats_subsection(self, target, hardware):
        self.doc.append(Subsection(r"Summary stats (averaged over target circuits) by" r" pipeline", numbering=False))
        with self.doc.create(LongTabu("|l|l|l|", row_height=1.5)) as table:
            df_mean = self.groupby_framework_mean(self.final_stage, hardware, target)
            table.add_hline()
            table.add_row(["Metrics", "Min", "Max"], mapper=bold, color="lightgray")
            table.add_hline()
            table.end_table_header()
            table.add_row((MultiColumn(3, align="|r|", data="Continued on Next Page"),))
            table.add_hline()
            table.end_table_footer()
            table.end_table_last_footer()
            for i in self.all_metrics:
                table = self.add_line_into_target_table(i["name"], df_mean, table)

    def generate_cluster_analytics_subsection(self, test_type, target, hardware):
        self.doc.append(Subsection(r"""Cluster analytics """, numbering=False))
        self.doc.append(
            NoEscape(
                r"""Scatter plots with axes representing: depth, (input/output) single-qubit gate count,
                (input/output) two-qubit gate count, (input/output) total gate count and execution time."""
            )
        )
        with self.doc.create(Figure(position="h!")) as fig:
            for i, metric in enumerate(self.scatter_fig_list):
                fig = self.print_figure(test_type, target, hardware, f"scatter_{metric}", fig)
                if i % 2 == 1:
                    self.doc.append(LineBreak())
            fig.add_caption(
                NoEscape(
                    rf"""Cluster analytics for {hardware}. Each point corresponds to an individual target
                    quantum circuit from the target generator."""
                )
            )
        self.doc.append(NoEscape(r"\clearpage"))

    def generate_circuit_analysis_subsection(self, test_type, target, hardware):
        self.doc.append(Subsection(r"""Breakdown by individual circuits """, numbering=False))
        with self.doc.create(Figure(position="h!")) as fig:
            for i, metric in enumerate(self.gate_metrics):
                fig = self.print_figure_from_initial_to_final_stage(
                    test_type, target, hardware, f"comp_heatmap_{metric['fig_name']}", fig
                )
                if i % 2 == 1:
                    self.doc.append(LineBreak())
            fig.add_caption(NoEscape(rf"""Compression factor ($CF$) vs circuit for {hardware}."""))
        with self.doc.create(LongTabu("|X[3l]|X[l]|X[l]|X[l]|X[l]|X[l]|X[l]|", row_height=1.5)) as table:
            table.add_hline()
            row_cells = [
                bold("Metrics"),
                MultiColumn(3, align="l|", data=bold("Min")),
                MultiColumn(3, align="l|", data=bold("Max")),
            ]
            table.add_row(row_cells)
            table.add_hline()
            table.add_row(
                ["", "Pipeline", "Circuit", "Val", "Pipeline", "Circuit", "Val"], mapper=bold, color="lightgray"
            )
            table.add_hline()
            table.end_table_header()
            table.add_row((MultiColumn(7, align="|r|", data="Continued on Next Page"),))
            table.add_hline()
            table.end_table_footer()
            table.end_table_last_footer()
            for i in self.all_metrics:
                if i["name"] == "Circuit Cost Function" or i["name"] == "Measurement Infidelity" or i["name"] == "Execution Time":
                    table = self.add_line_into_comp_factor_table(i["name"], hardware, target, table, is_round=True)
                else:
                    table = self.add_line_into_comp_factor_table(i["name"], hardware, target, table, is_round=False)

    def generate_frameworks_section(self):
        # Description of frameworks involved in benchmarking
        with self.doc.create(Section("""Frameworks """)):
            self.doc.append(NoEscape("Below we list compilation frameworks used in the benchmarking run:"))
            if "QiskitPl" in self.frameworks:
                with self.doc.create(Itemize()) as itemize:
                    itemize.add_item(NoEscape(r"""\textbf{IBM Qiskit}\footnotemark"""))
                    self.doc.append(
                        NoEscape(
                            r"""\footnotetext{IBM and Qiskit are trademarks of International
                            Business Machines Corporation, registered in many jurisdictions worldwide.}"""
                        )
                    )
                    self.doc.append(
                        NoEscape(
                            f"""v{version('qiskit')} (open-source)."""
                            + r"""\textbf{Qiskit} is an open-source framework for working with quantum computers at the
                            level of circuits, pulses, and algorithms. Qiskit transpiler combines mapping and
                            compression subroutines. The transpiler has three levels of optimization, in our report,
                            we invoke the most advanced optimization level (3)."""
                        )
                    )
                    with self.doc.create(Itemize()) as itemize2:
                        itemize2.add_item(
                            NoEscape(
                                r"""Compression/optimization algorithm relies on \textbf{commutative cancellations of
                                gates, aggregation of single-qubit gates, removal of diagonal gates before
                                measurement.}"""
                            )
                        )
                        itemize2.add_item(
                            NoEscape(
                                r"""Routing and mapping algorithms are based on construction of a
                                \textbf{basic, stochastic or lookahead swap network.}"""
                            )
                        )
                        itemize2.add_item("""The output circuit gate set: """)
                        self.doc.append(NoEscape(r"$U_1$, $U_2$, $U_3$, $CNOT$, $I$."))
            if "CirqPl" in self.frameworks:
                with self.doc.create(Itemize()) as itemize:
                    itemize.add_item(NoEscape(r"""\textbf{Google Cirq library} """))
                    self.doc.append(
                        NoEscape(
                            f"""v{version('cirq')} (open-source). """
                            + r"""\textbf{Cirq} has been developed by Google AI Quantum Team. Cirq supports
                            mapping/routing operations and tailored towards specific grid-like qubit coupling
                            topologies."""
                        )
                    )
                    with self.doc.create(Itemize()) as itemize2:
                        itemize2.add_item(
                            NoEscape(
                                r"""The compression subroutines include \textbf{pushing Pauli gates and phased
                                Pauli gates to the end of the circuit, merging single-qubit gates and dropping
                                negligible gates and empty moments}."""
                            )
                        )
                        itemize2.add_item(
                            NoEscape(
                                r"""Routing and mapping methods are based on a \textbf{greedy swap insertion
                                strategy.}"""
                            )
                        )
                        itemize2.add_item(NoEscape(r"""The output circuit gate set: $R_x$, $R_z$, $CZ$."""))
            if "PyzxPl" in self.frameworks:
                with self.doc.create(Itemize()) as itemize:
                    itemize.add_item(
                        NoEscape(
                            r"""\textbf{PyZX} git cc34a6b (Radboud University, open-source). PyZX realizes
                            a non-standard approach to quantum circuit compression based on ZX-calculus
                            (``spider''-calculus). PyZX only supports hardware with all-to-all qubit connectivity. """
                        )
                    )
                    with self.doc.create(Itemize()) as itemize2:
                        itemize2.add_item(
                            NoEscape(
                                r"""In this report, we use the main simplification routine of PyZX (full reduce).
                                It uses a combination of \textit{Clifford gates simplification and the gadgetization
                                strategies.}"""
                            )
                        )
                        itemize2.add_item(
                            NoEscape(
                                r"""The output circuit gate set: \textit{SWAP, CX, CZ, H, X, Z, S, T, Rx, Rz}"""
                            )
                        )

    def generate_definitions_section(self):
        with self.doc.create(Section("Definitions")):
            self.doc.append(
                NoEscape(
                    """We define compression factor ($CF$) for a particular class of gates ($G$)
                    (e.g. single-qubit gates, two-qubit gates) averaged over circuits ($C$) as:"""
                )
            )
            with self.doc.create(Itemize()) as itemize:
                itemize.add_item(
                    NoEscape(
                        r"""Compression factor greater then unity ($CF(G)>1$) corresponds to a successful compression
                        (the gate count of the gate ($G$) in the output circuit is less compared to the input circuit).
                        Similarly, compression factor less then unity ($CF(G)<1$) corresponds to
                        unsuccessful compression (the output circuit contains more gates of type ($G$)
                        compared to the input circuit)."""
                    )
                )
                with self.doc.create(Alignat(numbering=False, escape=False)) as agn:
                    agn.append(
                        r"""CF(G) =\left \langle  \frac{\textrm{gate count}
                        (G, C_i)_{\textrm{before}}}{\textrm{gate count}(G, C_i)_{\textrm{after}}} \right\rangle_{C}."""
                    )
                itemize.add_item(
                    NoEscape(
                        r"""Circuits \textbf{before} and \textbf{after} correspond to initial and
                        final compilation stages. In the present report, we usually assume that the initial stage is
                        target generation, the final stage is typically either \textbf{compression} or
                        \textbf{rebase} to the output hardware gate set.
                        """
                    )
                )
            self.doc.append(
                NoEscape(
                    """As an additional metric that defines a circuit cost we use the following
                    circuit cost function:"""
                )
            )
            with self.doc.create(Alignat(numbering=False, escape=False)) as agn:
                agn.append(r"""C = -\log{\left(K^d \prod_i F^{1q}_i \prod_j F^{2q}_j\right)},""")
            self.doc.append(
                NoEscape(
                    r"""where $C$ - circuit cost, $K$ - factor that penalises deep circuits,
                    $d$ - circuit depth, $F^{1q}_i$ - fidelity of single qubit gates,
                    $F^{2q}_j$ - fidelity of two qubit gates. """
                )
            )

    def generate_metrics_section(self):
        with self.doc.create(Section("Metrics")):
            with self.doc.create(Itemize()) as itemize:
                for i in self.all_metrics:
                    itemize.add_item(NoEscape(rf"""{i["name"]}"""))
            self.doc.append(
                NoEscape(
                    r"""Note that in most cases single-qubit gate count and single-qubit gate compression factor
                    have only limited meaning as a metric of compiler performance. This is because single-qubit
                    gate count is very sensitive to the choice single-qubit basisgates (e.g. $U_3$ is equivalent
                    to a combination of 3 rotation gates $R_x$, $R_y$ and $R_z$)."""
                )
            )

    def generate_hardware_backends_section(self):
        with self.doc.create(Section("Hardware Backends ")):
            self.doc.append(
                NoEscape(
                    r"""Hardware backends are defined in open-source \textbf{Arline Quantum} library """
                )
            )
            self.doc.append(LineBreak())
            self.doc.append(Hyperref(marker="", text="""https://github.com/ArlineQ/arline_quantum"""))
            self.doc.append(
                NoEscape(
                    r""". Names of hardware backends reflect gate set and connectivity. E.g. IbmAll2All16Q
                    corresponds to a 16-qubit fully-connected mock backend with the native gate set of the IBM
                    quantum hardware. \bigskip"""
                )
            )
            for cnt, hardw in enumerate(self.hardware_list):  # TODO add gate set information
                with self.doc.create(Figure(position="h!")) as fig:
                    filename = rf"figures/coupling_map_{hardw}.{self.fig_format}".lower()
                    filename = os.path.join(self.input_dir, filename)
                    filename = os.path.abspath(filename)
                    fig.add_image(filename, width=NoEscape(r"0.3\textwidth"))
                    fig.add_caption(f"{hardw} hardware coupling map: adjacency matrix.")
            self.doc.append(NoEscape(r"\clearpage"))

    def generate_compilation_pipelines_section(self):
        self.doc.append(Section("Compilation Pipelines"))
        self.doc.append(
            NoEscape(
                r"""\textbf{Compilation pipeline} is a sequence of compilation routines,
                which typically consist of three main stages:"""
            )
        )
        with self.doc.create(Enumerate()) as enumerate_tex:
            enumerate_tex.add_item(NoEscape(r"""\textbf{Unroll} (optional) for the three-qubit gates;"""))
            enumerate_tex.add_item(
                NoEscape(
                    r"""\textbf{Mapping} and \textbf{routing} of the original circuit to
                    a hardware topology, further \textbf{mapping};"""
                )
            )
            enumerate_tex.add_item(
                NoEscape(r"""\textbf{Compression} of the circuit that reduces the number of gates involved;""")
            )
            enumerate_tex.add_item(
                NoEscape(r"""\textbf{Rebase} (optional) of the final gate sequence into a particular gate set;""")
            )

        pipelines = self.get_pipelines_summary()
        self.doc.append(
            NoEscape(
                r"""Summary of compilation pipelines settings used in the current report is presented below. \\ """
            )
        )
        self.doc.append(
            NoEscape(
                f"""Number of pipelines for benchmarking: """ + r"\textbf{" + "{:}".format(len(pipelines)) + r"}")
        )
        with self.doc.create(Itemize()) as itemize:
            for pip_i in range(len(pipelines)):
                pipeline_name = pipelines[pip_i]["pipeline"].replace("_", "\_")
                itemize.add_item(NoEscape(r"Pipeline name: \textbf{" + pipeline_name + r"}"))
                with self.doc.create(Enumerate()) as enumerate_tex:
                    stages = pipelines[pip_i]["stages"]
                    for stage in stages:
                        stage_parsed = stage.replace("_", "\_")
                        enumerate_tex.add_item(NoEscape(r"Stage name: \textbf{" + stage_parsed + r"}"))

    def generate_system_info_section(self):
        with self.doc.create(Section("System Info")):
            with self.doc.create(Itemize()) as itemize:
                itemize.add_item(f"Platform: {platform.platform(aliased=1)}")
                itemize.add_item(f"Processor: {cpuinfo.get_cpu_info()['brand_raw']}")
                memory = virtual_memory().total / 2 ** 30
                itemize.add_item(f"Memory: {round(memory, 1)} Gb")

    def generate_targets_section(self):
        with self.doc.create(Section("Targets")):
            target_list_full = self.df["Test Target Generator Name"].unique()
            self.doc.append("Target is a quantum circuit subject to compilation. List of target generators: ")
            for targ in target_list_full:
                with self.doc.create(Itemize()) as itemize:
                    target_summary = self.get_target_summary(targ)
                    targ_name, targ_name_lower_case = self.target_class_display_name(targ)
                    itemize.add_item(NoEscape(rf"Target generator type: {targ_name_lower_case}:"))
                    if targ_name == "QASM Circuits for Arithmetic Blocks":
                        with self.doc.create(Itemize()) as itemize3:
                            itemize3.add_item(
                                NoEscape(
                                    r"""This QASM dataset contains circuits relevant for arithmetic
                                    operations in quantum algorithms such as Shor's algorithm and many other. """
                                )
                            )
                            self.doc.append(NoEscape(r"""More info can be found on D. Maslov's  website """))
                            self.doc.append(LineBreak())
                            self.doc.append(Hyperref(marker="", text="""http://webhome.cs.uvic.ca/~dmaslov/"""))
                            self.doc.append(NoEscape(r"""."""))
                            itemize3.add_item(
                                NoEscape(
                                    r"""Some examples of frequently used arithmetic block circuits:"""
                                )
                            )
                            with self.doc.create(Itemize()) as itemize4:
                                itemize4.add_item(r"""ALU (arithmetic logical unit) [e.g. mini-alu_167.qasm]""")
                                itemize4.add_item(r"""Symmetric functions [e.g. sym9_146.qasm]""")
                                itemize4.add_item(r"""RD-Input weight functions [e.g. rd53_135.qasm]""")
                    g_names = target_summary["gate_names"]
                    g_frequencies = target_summary["gate_frequencies"]
                    s = "[" + ", ".join([g + ": " + str(round(f, 3)) for g, f in zip(g_names, g_frequencies)]) + "]"
                    with self.doc.create(Itemize()) as itemize2:
                        itemize2.add_item(f"Number of circuits: {target_summary['num_targets']}")
                        itemize2.add_item(f"Gates frequencies: {s}")
                        itemize2.add_item(f"Mean number of qubits: {target_summary['mean_num_qubits']}")
                        itemize2.add_item(
                            f"Mean circuit depth per circuit: {round(target_summary['mean_depth'], 1)}")
                        itemize2.add_item(
                            f"Mean single-qubit gate count per circuit: "
                            f"{round(target_summary['mean_one_qubit_gate_count'], 1)}"
                        )
                        itemize2.add_item(
                            f"Mean two-qubit gate count per circuit: "
                            f"{round(target_summary['mean_two_qubit_gate_count'], 1)}"
                        )
                        itemize2.add_item(
                            f"Mean total gate count per circuit:"
                            f" {round(target_summary['mean_total_gate_count'], 1)}"
                        )

    def generate_benchmark_comparison_chapter(self, test_type, target_list, hardware_list):
        for target in target_list:
            targ_name, targ_name_lower_case = self.target_class_display_name(target)
            with self.doc.create(Chapter(NoEscape(rf"Target: {targ_name}"))):
                for i_hardw, hardware in enumerate(hardware_list):
                    self.doc.append(Section(r"Hardware: {:}".format(hardware)))
                    self.generate_metrics_analysis_subsection(test_type, target, hardware)
                    self.generate_gate_composition_subsection(test_type, target, hardware)
                    self.generate_execution_time_stats_subsection(test_type, target, hardware)
                    self.generate_summary_stats_subsection(target, hardware)
                    self.generate_cluster_analytics_subsection(test_type, target, hardware)
                    self.generate_circuit_analysis_subsection(test_type, target, hardware)
                self.generate_hardware_comparison_section(test_type, target, hardware, hardware_list)

    def generate_kak_summary_chapter(self):
        with self.doc.create(Chapter(NoEscape(rf"Comparison with KAK Decomposition: Two-Qubit Circuits"))):
            with self.doc.create(Section("Cartan decomposition")):
                self.doc.append(
                    NoEscape(
                        r"""Cartan decomposition (KAK decomposition) provides theoretical
                        $CNOT$-optimal schemes for two-qubit circuits (Figure \ref{fig:KAK}).\bigskip"""
                    )
                )
                with self.doc.create(Figure(position="h")) as fig:
                    kak_scheme_path = path.join(
                        os.path.dirname(os.path.abspath(arline_benchmarks.__file__)), "reports"
                    )
                    filename = "./kak_scheme.png"
                    filename = os.path.join(kak_scheme_path, filename)
                    fig.add_image(filename, width=NoEscape(r"0.7\textwidth"))
                    fig.add_caption(
                        NoEscape(r"""\label{fig:KAK}KAK decomposition scheme for two-qubit circuits.""")
                    )
                self.doc.append(
                    NoEscape(
                        r"""\noindent{Arbitrary two-qubit unitary can be represented using $U_3$ and $CNOT$ gates
                        with no more than: }"""
                    )
                )
                with self.doc.create(LongTabu("|l|l|l|", row_height=1.5)) as table:
                    table.add_hline()
                    table.add_row(["Metrics", "Gate Count", "Depth"], mapper=bold, color="lightgray")
                    table.add_hline()
                    table.end_table_header()
                    table.add_row((MultiColumn(3, align="|r|", data="Continued on Next Page"),))
                    table.add_hline()
                    table.end_table_footer()
                    table.end_table_last_footer()
                    row = [NoEscape(r"""$CNOT$"""), "3", "3"]
                    table.add_row(row)
                    table.add_hline()
                    row = [NoEscape(r"""$U_3$"""), "8", "4"]
                    table.add_row(row)
                    table.add_hline()
                    row = [NoEscape(r"""Total"""), "11", "7"]
                    table.add_row(row)
                    table.add_hline()
        self.doc.append(NewPage())

    def generate_multi_qubit_summary_chapter(self):
        with self.doc.create(Chapter(rf"Quick Summary")):
            with self.doc.create(Section("Aggregate Multi-Factor Comparison")):
                self.doc.append(
                    NoEscape(
                        r"""This analysis is performed across all compilation frameworks, target circuits and hardware.
                        From this result, we can deduce the degree of compressibility of different target
                        circuits. \bigskip

                        \noindent{Note that in most cases single-qubit gate count and single-qubit gate compression
                        factor have only limited meaning as a metric of compiler performance. This is because
                        single-qubit gate count is very sensitive to the choice single-qubit basis gates
                        (e.g. $U_3$ is equivalent to a combination of 3 rotation gates $R_x$, $R_y$ and $R_z$).}
                        """
                    )
                )
                with self.doc.create(Figure(position="h!")) as fig:
                    if self.compression_radar_with_cost:
                        filename = (
                            f"figures/multiqubit/comp_radar_with_cost_{self.initial_stage}_to_{self.final_stage}_grid."
                            f"{self.fig_format}"
                        )
                        filename = os.path.join(self.input_dir, filename)
                        filename = os.path.abspath(filename)
                        fig.add_image(filename, width=NoEscape(r"0.45\textwidth"))  # TODO fix coeff to fit into page
                        fig.add_caption(
                            NoEscape(
                                rf"""Aggregate multi-factor comparison of compilation frameworks: compression factor
                                ($CF$) across various features and circuit cost improvement. Columns correspond to
                                specific target circuit classes, and row correspond to different hardware architectures.
                                Better performance corresponds to a larger polygon area."""
                            )
                        )
                    else:
                        filename = (
                            f"figures/multiqubit/comp_radar_{self.initial_stage}_to_{self.final_stage}_grid."
                            f"{self.fig_format}"
                        )
                        filename = os.path.join(self.input_dir, filename)
                        filename = os.path.abspath(filename)
                        fig.add_image(filename, width=NoEscape(r"0.45\textwidth"))  # TODO fix coeff to fit into page
                        fig.add_caption(
                            NoEscape(
                                rf"""Aggregate multi-factor comparison of compilation frameworks: compression factor
                                ($CF$) across various features. Columns correspond to specific target circuit classes,
                                and row correspond to different hardware architectures. Better performance corresponds
                                to a larger polygon area."""
                            )
                        )

    def generate_references_chapter(self):
        self.doc.append(Chapter("References", numbering=False))
        with self.doc.create(Itemize()) as itemize:
            if self.kak_chapter:
                itemize.add_item(
                    NoEscape(
                        r""" G. Vidal and C.M. Dawson, “A universal quantum circuit for two-qubit
                        transformations with three CNOT gates”, Phys. Rev. A 69, 010301 (2004),  """
                    )
                )
                self.doc.append(Hyperref(marker="", text="""https://arxiv.org/pdf/quant-ph/0307177.pdf"""))
            if "QiskitPl" in self.frameworks:
                itemize.add_item(r"""IBM Qiskit repository """)
                self.doc.append(Hyperref(marker="", text="""https://github.com/Qiskit"""))
            if "CirqPl" in self.frameworks:
                itemize.add_item(r"""Google Quantum AI Lab repository """)
                self.doc.append(Hyperref(marker="", text="""https://github.com/quantumlib/Cirq"""))
            if "PyzxPl" in self.frameworks:
                itemize.add_item(r"""PyZX repository """)
                self.doc.append(Hyperref(marker="", text="""https://github.com/Quantomatic/pyzx"""))
            itemize.add_item(
                NoEscape(
                    r"""P. Jurcevic et al, "Demonstration of quantum volume 64 on a superconducting quantum
                    computing system", https://arxiv.org/abs/2008.08571 (2020)."""
                )
            )

    def generate_overview_chapter(self):
        with self.doc.create(Chapter(r"""Overview""")):
            self.doc.append(
                NoEscape(
                    r"""Quantum compilation is a problem of translating quantum algorithm to the set of low-level
                    hardware instructions to be executed on the quantum processor. Efficient compilation and circuit
                    optimisation (finding an optimal sequence of gates for the desired quantum computation) is immense
                    importance for practical applications and is necessary for further progress towards scalable quantum
                    computation.\bigskip

                    \noindent{The importance of optimal quantum compilation stems from the fact that noisy
                    intermediate-scale quantum (NISQ) devices suffer from unavoidable noise caused by individual gates.
                    Extreme susceptibility of quantum computation to noise is the crucial problem that hinders
                    the development of large-scale quantum computers. By the means of optimising gate count in the
                    quantum circuit, it is possible to significantly reduce hardware errors.} \bigskip

                    \noindent{Optimal (or near-optimal) circuit compilation is an extremely challenging task due to
                    additional constraints imposed by hardware configuration, such as restricted qubit connectivity
                    and hardware-native gate set. Finding optimal gate sequences for a given quantum circuit with all
                    imposed constraints is an open problem. For two-qubit circuits, the KAK algorithm is an example
                    of the efficient compilation algorithm, that is used in practical applications.} \bigskip

                    \noindent{The subroutines for quantum circuit optimisation, mapping and routing for particular
                    hardware connectivity are an integral part of existing quantum software frameworks. The complexity
                    and diversity of various quantum compilation algorithms create a necessity of cross-benchmarking and
                    comparison between different compiler frameworks. It worth to note, that the problem of hardware
                    benchmarking often arises in classical computing, where hardware is compared based on their
                    performance on a set of predefined tests.} \\ \\ \bigskip

                    \noindent{Arline Benchmarks}\footnotemark"""
                )
            )
            self.doc.append(
                NoEscape(
                    r"""\footnotetext{\textbf{Disclaimer.} This report was prepared using open source program Arline
                    Benchmarks and is provided "AS IS", "AS AVAILABLE", and all warranties, express or implied,
                    are disclaimed.\bigskip

                    Neither the authors of the Arline Benchmarks program, nor any of their employees, nor any of
                    their contractors, subcontractors or their employees, makes any warranty, express or implied, or
                    assumes any legal liability or responsibility for the accuracy, completeness, or any third party's
                    use or the results of such use of any information, apparatus, product, or process disclosed,
                    or represents that its use would not infringe privately owned rights.\bigskip

                    Readers are cautioned that information contained in this report is only current as of the
                    respective dates of such information. The technical condition, analyzed program code,
                    comparative results may have changed since those dates. Readers are advised to review only the most
                    recent document for the most current information. \\ \bigskip}
                    """
                )
            )
            self.doc.append(
                NoEscape(
                    r"""platform is created to solve benchmarking problem in the quantum world and aims to provide a
                    fair comparison between compilers for various quantum hardware and quantum algorithms.
                    """
                )
            )
            self.generate_frameworks_section()
            self.generate_definitions_section()
            self.generate_metrics_section()
            self.generate_hardware_backends_section()
            self.generate_compilation_pipelines_section()
            self.generate_system_info_section()
            self.generate_targets_section()

    def generate_title(self):
        self.doc.preamble.append(NoEscape(r"\linespread{1.5}"))
        self.doc.preamble.append(
            Command(
                "title",
                NoEscape(
                    r"""\textbf{Arline: Benchmarks} \\
                    Automated benchmarking platform for quantum compilers, quantum hardware and quantum algorithms \\
                    \vspace{2cm}
                    \normalsize{\textbf{Automatically generated report}} \\
                    \vspace{0.5cm}
                    \normalsize{\textbf{by Arline Benchmarks}}
                    \vspace{2cm}
                    """
                ),
            )
        )
        self.doc.preamble.append(Command("author", "https://github.com/ArlineQ/arline_benchmarks"))
        self.doc.preamble.append(Command("date", NoEscape(r"\today")))
        self.doc.append(NoEscape(r"\maketitle"))
        self.doc.append(NoEscape(r"\tableofcontents"))
        header = PageStyle("header")
        # Create right header
        with header.create(Head("R")):
            header.append(NoEscape(r"""\leftmark"""))
        with header.create(Foot("R")):
            header.append(simple_page_number())
        with header.create(Foot("L")):
            header.append(
                NoEscape(
                    r"""\footnotesize{\textbf{Automatically generated report by Arline Benchmarks \\
                    https://github.com/ArlineQ/arline\_benchmarks}}"""
                )
            )
        self.doc.preamble.append(header)
        self.doc.change_document_style("header")

    def generate_report(self):
        print("Generating LaTeX report, please wait ...")
        self.generate_title()
        self.generate_overview_chapter()
        # Generate chapter for KAK analysis (two-qubit hardware)
        if self.kak_chapter:
            test_type = 'kak'
            self.generate_kak_summary_chapter()
            self.generate_benchmark_comparison_chapter(test_type, self.kak_target_list, self.kak_hardware_list)
        # Generate chapter for multi-qubit analysis (>two-qubit hardware)
        if self.multi_qubit_chapter:
            test_type = 'multiqubit'
            self.generate_multi_qubit_summary_chapter()
            self.generate_benchmark_comparison_chapter(test_type, self.target_list, self.hardware_list)
        # Generate chapter for References
        self.generate_references_chapter()
        # Generate .tex file from the text provided above
        self.doc.generate_tex()
        # Converts .tex file to .pdf
        self.doc.generate_pdf(clean_tex=False)
        # The document as string in LaTeX syntax
        tex = self.doc.dumps()
        print(f"PDF report has been successfully generated from LaTeX in {self.filepath}")
