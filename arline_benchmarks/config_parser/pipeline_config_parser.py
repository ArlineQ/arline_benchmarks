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


import json
import _jsonnet


class PipelineConfigParser(dict):
    """Loads experiment configuration from disk (.jsonnet config file)

        :param str config_path: path to config
    """

    def __init__(self, setup_config_path):
        super().__init__()
        self._setup_config_path = setup_config_path
        self.update(json.loads(_jsonnet.evaluate_file(setup_config_path)))

    def to_json(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self, f, ensure_ascii=False, indent=2)
