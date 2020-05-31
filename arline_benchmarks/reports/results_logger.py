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


from contextlib import contextmanager

import pandas as pd


class CsvResultsLogger:
    """
    Columns order in csv:

        * all `id_columns_names` columns
        * columns with names from `columns_order` in specified order
        * all other columns
    """

    def __init__(self, filename, id_columns_names, columns_order=[]):
        self._filename = filename
        self._id_columns_names = id_columns_names
        self._data = []
        self._columns_order = columns_order

    def add_results(self, line_id, data):
        if len(line_id) != len(self._id_columns_names):
            Exception("line_id must be tuple with values of:", self._id_columns_names)
        d = data.copy()
        d.update({k: v for k, v in zip(self._id_columns_names, line_id)})
        self._data.append(d)

    def close(self):
        columns_names = list(self._id_columns_names)
        columns_names += self._columns_order
        columns_name_set = set(columns_names)
        for d in self._data:
            for k in d.keys():
                if k not in columns_name_set:
                    columns_names.append(k)
                    columns_name_set.add(k)

        results_df = pd.DataFrame(self._data, columns=columns_names)
        results_df.to_csv(self._filename, index=None, header=True)


@contextmanager
def open_csv_results_logger(*args, **kwargs):
    logger = CsvResultsLogger(*args, **kwargs)
    try:
        yield logger
    finally:
        logger.close()
