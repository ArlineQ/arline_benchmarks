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


from tqdm import tqdm

from arline_benchmarks.strategies.strategy import Strategy


class Pipeline:
    r"""Abstract Class for Pipeline
    """

    def __init__(self, pipeline_id, stages, run_analyser):
        self.stages = stages
        self.run_analyser = run_analyser
        self.stage_results = []
        self.analyser_report_history = []
        self.id = pipeline_id
        self.strategy_list = []
        for st_cfg in stages:
            self.strategy_list.append(Strategy.from_config(st_cfg["config"]))

    def run(self, target):
        self.stage_results = []
        self.analyser_report_history.clear()
        prev_stage_result = target
        # Sequentially execute strategies (stages) in compilation pipeline
        for strategy in self.strategy_list:
            tqdm.write("Pipeline ID: {}; Strategy: {}".format(self.id, str(strategy)))
            prev_stage_result = strategy.run(prev_stage_result, self.run_analyser)
            self.stage_results.append(prev_stage_result)
            # Return analyser results for the current compilation stage
            if self.run_analyser:
                self.analyser_report_history.append(strategy.analyser_report)
        return prev_stage_result

    def get_execution_time(self):
        execution_time = 0
        # Get runtime of the current compilation stage
        for i in self.analyser_report_history:
            execution_time += i["execution_time"]
        return execution_time

    def get_execution_time_by_stage(self, index):
        # Get runtime info for a particular compilation stage enumerated by index
        if index > len(self.stages):
            raise Exception(
                f"Index is larger then the number of stages: index = {index}, number of stages = {len(self.stages)}"
            )
        return self.analyser_report_history[index]["execution_time"]

    def get_gate_chain_by_stage(self, index):
        if index > len(self.stages):
            raise Exception(
                f"Index is larger then the number of stages: index = {index}, number of stages = {len(self.stages)}"
            )
        return self.stage_results[index]
