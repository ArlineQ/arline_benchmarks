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


import sys
import traceback
from os import makedirs, path
from pprint import pprint
from shutil import rmtree

import pandas as pd
from tqdm import tqdm

from arline_benchmarks.pipeline.pipeline import Pipeline
from arline_benchmarks.reports.plot_benchmarks import BenchmarkPlotter
from arline_benchmarks.reports.results_logger import open_csv_results_logger
from arline_benchmarks.targets.target import Target
from arline_quantum.gate_chain.gate_chain import GateChain


class PipelineEngine:
    """Benchmark Engine Class
    """

    def __init__(self, cfg, args):
        self.args = args
        self.cfg = cfg
        self.run_id = 0

    def run(self):
        # Output path
        output_dir = path.join(self.args.output, "output")
        output_qasm_dir = path.join(output_dir, "output_qasm")
        self.create_result_dir(output_dir)
        self.create_result_dir(output_qasm_dir)
        # Convert .jsonnet config file to .json
        self.cfg.to_json(path.join(self.args.output, "config.json"))

        # column names in .csv output file
        id_columns_names = [
            "Run ID",
            "Pipeline ID",
            "Stage ID",
            "Strategy ID",
            "Test Target Generator Name",
            "Test Target ID",
            "Pipeline Output Hardware Name",
            "Pipeline Output Number of Qubits",
            "QASM Path",
            "Plot Group",
        ]

        columns_first = []
        # Path to .csv report file with benchmarking results
        report_file = path.join(output_dir, "gate_chain_report.csv")

        with open_csv_results_logger(report_file, id_columns_names, columns_order=columns_first) as csv_logger:
            # Create Pipeline
            for pipeline_cfg in tqdm(self.cfg["pipelines"], desc="Overall benchmark progress", unit="pipeline"):
                pipeline = Pipeline(pipeline_id=pipeline_cfg["id"], stages=pipeline_cfg["stages"], run_analyser=True)
                # Create Target Generator
                target_generator = Target.from_config(config=pipeline_cfg["target"])

                targets = []
                while True:
                    try:
                        t = next(target_generator)
                        if t is None:
                            print("\n\nTarget is None", file=sys.stderr)
                            print("Target config:", file=sys.stderr)
                            pprint(pipeline_cfg["target"], stream=sys.stderr)
                            continue
                        targets.append(t)
                    except StopIteration:
                        break
                    except Exception as e:
                        print("\n\nError occurred when generating target", target_generator, file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                        print("Target config:", file=sys.stderr)
                        pprint(pipeline_cfg["target"], stream=sys.stderr)
                        continue

                for target, target_id in tqdm(
                    targets, desc="Benchmarking pipeline {}".format(pipeline_cfg["id"]), unit="target",
                ):
                    try:
                        tqdm.write("Target ID: {}, Target Name: {}".format(target_id, pipeline_cfg["target"]["name"]))
                        r = pipeline.run(target)
                    except Exception as e:
                        print(
                            f"\n\nError occurred when running pipeline {pipeline.id} on target_id {target_id}:",
                            file=sys.stderr,
                        )
                        traceback.print_exc(file=sys.stderr)
                        print("Pipeline config:", file=sys.stderr)
                        pprint(pipeline_cfg, stream=sys.stderr)
                        continue

                    for stg_cfg, stage_result, stg_report in zip(
                        pipeline.stages, pipeline.stage_results, pipeline.analyser_report_history
                    ):
                        # Save Gate Chain
                        qasm_path = path.join(
                            output_qasm_dir,
                            "{}_output_{}_{}_{}.qasm".format(
                                self.run_id, pipeline_cfg["target"]["name"], target_id, stg_cfg["id"]
                            ),
                        )
                        if isinstance(stage_result, GateChain):
                            stage_result.save_to_qasm(qasm_path, "q")

                        # Add result into report
                        hardw = pipeline.strategy_list[-1].quantum_hardware  # Take hardware the last stage
                        csv_logger.add_results(
                            line_id=(
                                self.run_id,  # "Run ID",
                                pipeline_cfg["id"],  # "Pipeline ID",
                                stg_cfg["id"],  # "Stage ID",
                                stg_cfg["config"]["strategy"],  # "Strategy ID"
                                pipeline_cfg["target"]["name"],  # "Test Target Generator Name",
                                target_id,  # "Test Target ID",
                                "{}{}Q".format(hardw.name, hardw.num_qubits),  # "Pipeline Output Hardware Name",
                                hardw.num_qubits,  # "Pipeline Output Number of Qubits",
                                qasm_path,  # "QASM path"
                                pipeline_cfg["plot_group"],  # "Plot Group"
                            ),
                            data=stg_report,
                        )
                    self.run_id += 1

        data = pd.read_csv(report_file)
        bp = BenchmarkPlotter(data=data, output_path=path.join(output_dir, "figures"), config=self.cfg)
        bp.plot()

    def create_result_dir(self, d):
        rmtree(d, ignore_errors=True)
        makedirs(d)
