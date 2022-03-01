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


import re
import sys
import traceback
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns

from matplotlib import pyplot as plt
from tqdm import tqdm
from pprint import pprint
from contextlib import suppress
from os import makedirs, path

from arline_quantum.hardware import hardware_by_name

matplotlib.use("Agg")


class BenchmarkPlotter:
    r"""Benchmark Report Plotter Class

    **Description:**
        Generates plots based on .csv benchmarking report file.
        Benchmark plotter methods are grouped according to the plot type (histogram, heatmap, radar etc):

            * Pipeline comparison histogram
            * Plots bar histogram for various metrics types (gate count, depth, ...) for each pipeline stage
            * Scatter plots (for cluster analytics)
            * Heatmap plots for compression factor by feature type (gate count, depth, ...)
            * Heatmap plots for gate composition (gate count distribution by gate type)
            * Radar plot for multi-factor comparison of compilation pipelines by compression feature factor

    """

    def __init__(self, data, output_path, config):
        self.data = data
        self.output_path = output_path
        makedirs(self.output_path, exist_ok=True)
        self.config = config
        self.dpi = 300
        with suppress(KeyError):
            self.dpi = self.config["plotter"]["dpi"]

    def filter_condition(self, df, conditions):
        data = df.copy()
        for criteria, value in conditions.items():
            data = data[data[criteria] == value]
        return data

    def plot(self):
        for plot_cfg in tqdm(self.config["plotter"]["plots"]):
            fixed_conditions = plot_cfg["fixed_conditions"]
            df = self.filter_condition(self.data, fixed_conditions)
            iterative_conditions = plot_cfg["iterative_conditions"]
            condition_combinations = df[iterative_conditions].drop_duplicates().to_dict("records")

            for cc in condition_combinations:
                comb_conditions = fixed_conditions.copy()
                comb_conditions.update(cc)
                # comb_conditions = dict(**fixed_conditions, **cc)
                selected_data = self.filter_condition(df, cc)
                title = None
                if plot_cfg["title"] is not None:
                    title = plot_cfg["title"].format(**comb_conditions, **plot_cfg["args"])
                plot_function = getattr(self, plot_cfg["plot_function"])
                try:
                    plot_function(data=selected_data, title=title, **plot_cfg["args"])
                except Exception as e:
                    print(f"Error occurred when plotting {title}:", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                    print("Plot config:", file=sys.stderr)
                    pprint(plot_cfg, stream=sys.stderr)
                # save
                filename = plot_cfg["filename"].format(**comb_conditions, **plot_cfg["args"])
                filename = path.join(
                    path.dirname(filename), path.basename(filename).replace(" ", "_").replace("-", "_").lower()
                )  # Consistent file names

                full_path = path.join(self.output_path, filename)
                makedirs(path.dirname(full_path), exist_ok=True)
                if path.exists(full_path):
                    print(f"Warning: file {filename} already exists!")
                plt.savefig(full_path, dpi=self.dpi, bbox_inches="tight")
                plt.close()

    def plot_pipelines_comparison_bars(
        self, data, y_col, pipelines_settings, stages_settings, baseline={}, title=None, yscale="linear"
    ):
        sns.set(style="darkgrid", font_scale=1.5)

        # Prepare "Stage" and "Pipeline" columns
        # data["Stage"] = data["Stage ID"].map({s: d["name"] for s, d in stages_settings.items()})
        data["Pipeline"] = data["Pipeline ID"].map({s: d["name"] for s, d in pipelines_settings.items()})

        # Filter stages
        data = data[data["Stage ID"].isin(stages_settings.keys())]

        # Filter pipelines
        data = data[data["Pipeline ID"].isin(pipelines_settings.keys())]

        pallete = {d["name"]: d["color"] for n, d in stages_settings.items()}

        if len(data) == 0:
            raise Exception("No data in CSV")

        x = []
        y = []
        color = []
        stage_names = []
        pipeline_x = []
        pipeline_names = []
        errors = []

        i = 0
        for pl in data["Pipeline"].unique():
            pipeline_names.append(pl)
            pl_df = data[data["Pipeline"] == pl]
            stages = pl_df["Stage ID"].unique()

            pipeline_x.append(i + len(stages) / 2)

            for stage in stages:
                x.append(i)
                y.append(pl_df[pl_df["Stage ID"] == stage][y_col].mean())
                errors.append(pl_df[pl_df["Stage ID"] == stage][y_col].std())
                color.append(stages_settings[stage]["color"])
                stage_names.append(stages_settings[stage]["name"])
                i += 1
            i += 2

        x = np.array(x)
        y = np.array(y)
        color = np.array(color)
        stage_names = np.array(stage_names)
        pipeline_x = np.array(pipeline_x)
        pipeline_names = np.array(pipeline_names)
        errors = np.array(errors)

        for st, st_cfg in stages_settings.items():
            st_mask = stage_names == st_cfg["name"]
            g = plt.bar(
                x[st_mask],
                y[st_mask],
                color=color[st_mask],
                width=1,
                edgecolor="white",
                label=st_cfg["name"],
                alpha=0.5,
                yerr=errors[st_mask],
            )

        plt.grid(axis="x", b=None)
        plt.grid(axis="y", which="minor", color="w", linestyle="-", linewidth=0.5)
        plt.grid(axis="y", which="major", color="w", linestyle="-", linewidth=1)

        plt.xticks(pipeline_x, pipeline_names)
        plt.gca().set_yscale(yscale)

        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5), fancybox=False, framealpha=0, title="Stages")

        plt.xlabel("Pipeline")
        plt.ylabel(y_col)

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.9)

        if baseline:
            plt.hlines(
                baseline["value"],
                plt.gca().get_xlim()[0],
                plt.gca().get_xlim()[1],
                **baseline["style"],
                label=baseline["name"],
            )

    def plot_scatter(
        self, data, x_col, y_col, input_stage=None, output_stage=None, pipelines_settings={}, baseline={}, title=None,
    ):
        sns.set(style="darkgrid", font_scale=1.5)

        # Filter pipelines and prepare 'Pipeline' column
        data = data[data["Pipeline ID"].isin(pipelines_settings.keys())]
        data["Pipeline"] = data["Pipeline ID"].map({s: d["name"] for s, d in pipelines_settings.items()})

        # Filter stages
        if output_stage is not None:
            output_df = data[data["Stage ID"] == output_stage].reset_index()
            data_history = output_df
            output_df = output_df.rename(columns={c: "Output " + c for c in output_df.columns})
            data_history = pd.concat([data_history, output_df], axis=1)

        if input_stage is not None:
            input_df = data[data["Stage ID"] == input_stage].reset_index()
            input_df = input_df.rename(columns={c: "Input " + c for c in input_df.columns})
            data_history = pd.concat([data_history, input_df], axis=1)

        data = data_history
        pallete = {d["name"]: d["color"] for n, d in pipelines_settings.items()}

        if len(data) == 0:
            raise Exception("No data in CSV")

        g = sns.scatterplot(x=x_col, y=y_col, hue="Pipeline", data=data, palette=pallete, alpha=0.5, s=90)
        g.legend(loc="center left", bbox_to_anchor=(1, 0.5), ncol=1, fancybox=False, framealpha=0)

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.9)

        if baseline:
            plt.hlines(baseline["value"], *g.ax.get_xlim(), **baseline["style"], label=baseline["name"])

    def plot_compression_heatmap(
        self,
        data,
        rows_feature,
        pipelines_settings,
        input_stage,
        output_stage,
        compression_feature,
        row_label,
        title=None,
    ):
        sns.set(style="darkgrid", font_scale=1.5)

        # Filter pipelines and prepare 'Pipeline' column
        data = data[data["Pipeline ID"].isin(pipelines_settings.keys())]
        data["Pipeline"] = data["Pipeline ID"].map({s: d["name"] for s, d in pipelines_settings.items()})

        # Filter stages
        input_df = data[data["Stage ID"] == input_stage].reset_index()
        output_df = data[data["Stage ID"] == output_stage].reset_index()

        output_df[compression_feature] = input_df[compression_feature].divide(output_df[compression_feature])

        heat_df = pd.pivot_table(
            output_df, values=compression_feature, index=[rows_feature], columns=["Pipeline"], aggfunc=np.mean,
        )

        if len(heat_df) == 0:
            raise Exception("No data in CSV")

        cmap = "Purples"
        g = sns.heatmap(
            heat_df, cmap=cmap, linewidths=0.5, center=1, cbar_kws={"shrink": 1.0}, square=False, alpha=1.0,
        )
        plt.ylim(0, len(heat_df.index))

        if row_label is None:
            row_label = rows_feature

        plt.ylabel(row_label)
        plt.yticks(rotation=0)

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.9)

    def plot_gate_composition(self, data, stages_settings, title=None):
        # Filter stages and prepare 'Stage' column
        data["Stage"] = data["Stage ID"].map({s: d["name"] for s, d in stages_settings.items()})
        data = data[data["Stage ID"].isin(stages_settings.keys())]

        df = data.reset_index().groupby(by="Stage").aggregate(np.sum)
        df = df.reset_index()
        df = df.sort_values("index", ascending=False)
        stage_id = df["Stage"]

        g_count_sum = df.filter(regex=("Count of .* Gates"), axis=1)
        g_count_sum = g_count_sum.loc[:, (df != 0).any(axis=0)]

        old_g_names = g_count_sum.columns
        g_names = [re.search("Count of (.*) Gates", g).group(1) for g in old_g_names]
        # g_count_sum = g_count_sum.div(g_count_sum.sum(axis=1), axis=0)
        cmap = plt.cm.get_cmap("gnuplot2").reversed()

        sns.heatmap(
            g_count_sum,
            # annot=True,
            # fmt=".2g",
            cmap=cmap,
            square=False,
            linewidths=1.5,
            norm=matplotlib.colors.SymLogNorm(linthresh=1, base=10),
            # center=0.5,
            cbar_kws={"shrink": 1.0},
            xticklabels=g_names,
            yticklabels=stage_id,
        )
        plt.ylim(0, len(g_count_sum))
        plt.yticks(rotation=0)

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.9)

    def plot_compression_radar(
        self, data, pipelines_settings, input_stage, output_stage, compression_features, title=None,
    ):
        sns.set(style="darkgrid", font_scale=1.5)

        # Filter pipelines and prepare 'Pipeline' column
        data = data[data["Pipeline ID"].isin(pipelines_settings.keys())]
        data["Pipeline"] = data["Pipeline ID"].map({s: d["name"] for s, d in pipelines_settings.items()})

        # Filter stages
        input_df = data[data["Stage ID"] == input_stage].reset_index()
        output_df = data[data["Stage ID"] == output_stage].reset_index()

        for cc in compression_features.keys():
            output_df[cc] = input_df[cc].divide(output_df[cc])

        mean_by_pipeline_id = output_df.groupby("Pipeline ID").mean()

        fig = plt.figure(figsize=(2.5, 2.5))
        ax = fig.add_subplot(111, polar=True)
        labels = [compression_features[key]["name"] for key in compression_features.keys()]
        angles = np.linspace(0, 2 * np.pi, len(labels) + 1, endpoint=True)

        sorted_pipelines_settings = sorted(pipelines_settings.keys(), key=lambda x: x.lower(), reverse=True)
        for p_id in sorted_pipelines_settings:
            p_cfg = pipelines_settings[p_id]
            try:
                stats = [mean_by_pipeline_id[col_name][p_id] for col_name in compression_features]
                stats.append(stats[0])
                color = None
                with suppress(KeyError):
                    color = p_cfg["color"]
                ax.plot(
                    angles, stats, "o-", linewidth=1.0, markersize=2.0, label=p_cfg["name"], color=color, alpha=0.9,
                )
                ax.fill(angles, stats, alpha=0.0)
            except Exception as e:
                print(
                    f"Can't plot plot_compression_radar '{title}', pipeline '{p_id}', compression_features:"
                    f" {compression_features}"
                )

        ax.set_thetagrids(angles * 180 / np.pi, labels, fontweight="black")
        ax.grid(True)
        # Fix axis to go in the right order and start at 12 o'clock.
        ax.set_theta_offset(0)
        ax.set_theta_direction(-1)
        # Draw ylabels
        ax.set_rlabel_position(-90)
        ax.set_yticks([0.0, 0.5, 1.0, 1.5])
        ax.set_ylim(0, ax.get_ylim()[1])
        ax.tick_params(labelsize=4.0)

        plt.legend(loc="upper left", bbox_to_anchor=(0.9, 1.05), fancybox=False, framealpha=0, fontsize=4)

        fig.tight_layout()

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.7)

    def plot_compression_radar_grid(
        self, data, pipelines_settings, input_stage, output_stage, compression_features, title=None,
    ):
        sns.set(style="darkgrid", font_scale=1.5)

        # Filter pipelines and prepare 'Pipeline' column
        data = data[data["Pipeline ID"].isin(pipelines_settings.keys())]
        data["Pipeline"] = data["Pipeline ID"].map({s: d["name"] for s, d in pipelines_settings.items()})

        # Filter stages
        input_df = data[data["Stage ID"] == input_stage].reset_index()
        output_df = data[data["Stage ID"] == output_stage].reset_index()

        for cc in compression_features.keys():
            output_df[cc] = input_df[cc].divide(output_df[cc])

        hardw_list = data["Pipeline Output Hardware Name"].drop_duplicates()
        targ_list = data["Test Target Generator Name"].drop_duplicates()
        fig, axs = plt.subplots(
            len(hardw_list),
            len(targ_list),
            subplot_kw=dict(polar=True),
            figsize=(2.5 * len(targ_list), 2.5 * len(hardw_list)),
        )
        # fig.subplots_adjust(bottom=0.15, left=0.4)

        for i_hardw, hardw in enumerate(hardw_list):
            for j_targ, targ in enumerate(targ_list):
                if len(hardw_list) == 1 and len(targ_list) == 1:
                    ax = axs
                elif len(hardw_list) == 1:
                    ax = axs[j_targ]
                elif len(targ_list) == 1:
                    ax = axs[i_hardw]
                else:
                    ax = axs[i_hardw, j_targ]
                if i_hardw == 0:
                    ax.set_title(targ, fontsize=7, fontweight="bold", position=(0.5, 1.3))
                if j_targ == 0:
                    ax.set_ylabel(hardw, rotation=90, fontsize=7, fontweight="bold", labelpad=40)

                tmp_df = output_df[output_df["Pipeline Output Hardware Name"] == hardw]
                tmp_df = tmp_df[tmp_df["Test Target Generator Name"] == targ]

                mean_by_pipeline_id = tmp_df.groupby("Pipeline ID").mean()

                labels = [compression_features[key]["name"] for key in compression_features.keys()]
                angles = np.linspace(0, 2 * np.pi, len(labels) + 1, endpoint=True)
                if i_hardw == 0 and j_targ == 0:
                    ax.set_thetagrids(angles * 180 / np.pi, labels, fontweight="black")
                else:
                    labels = [""] * len(labels)
                    ax.set_thetagrids(angles * 180 / np.pi, labels, fontweight="black")

                sorted_pipelines_settings = sorted(pipelines_settings.keys(), key=lambda x: x.lower(), reverse=True)
                for p_id in sorted_pipelines_settings:
                    p_cfg = pipelines_settings[p_id]
                    try:
                        stats = [mean_by_pipeline_id[col_name][p_id] for col_name in compression_features]
                        stats.append(stats[0])
                        color = None
                        with suppress(KeyError):
                            color = p_cfg["color"]
                        ax.plot(
                            angles,
                            stats,
                            "o-",
                            linewidth=1.0,
                            markersize=2.0,
                            label=p_cfg["name"],
                            color=color,
                            alpha=0.9,
                        )
                        ax.fill(angles, stats, alpha=0.0)

                    except Exception as e:
                        print(
                            f"Can't plot plot_compression_radar_grid '{title}', pipeline '{p_id}', compression_features:"
                            f" {compression_features}"
                        )
                if i_hardw == 0 and j_targ == 0:
                    ax.legend(loc="upper left", bbox_to_anchor=(0.9, 1.05), fancybox=False, framealpha=0, fontsize=5)
                ax.grid(True)
                # Fix axis to go in the right order and start at 12 o'clock.
                ax.set_theta_offset(0)
                ax.set_theta_direction(-1)
                # Draw ylabels
                ax.set_rlabel_position(-90)
                ax.set_yticks([0.0, 0.5, 1.0, 1.5])
                ax.set_ylim(0, ax.get_ylim()[1])
                ax.tick_params(labelsize=5.0)

        fig.tight_layout()

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.7)

    def plot_pipelines_compression_factor(
        self, data, pipelines_settings, input_stage, output_stage, compression_features, baseline, title=None,
    ):
        sns.set(style="darkgrid", font_scale=1.5)

        # Filter pipelines and prepare 'Pipeline' column
        data = data[data["Pipeline ID"].isin(pipelines_settings.keys())]
        data["Pipeline"] = data["Pipeline ID"].map({s: d["name"] for s, d in pipelines_settings.items()})

        # Filter stages
        input_df = data[data["Stage ID"] == input_stage].reset_index()
        output_df = data[data["Stage ID"] == output_stage].reset_index()

        for cc in compression_features.keys():
            output_df[cc] = input_df[cc].divide(output_df[cc])

        melted_df = pd.melt(
            output_df,
            id_vars=["Pipeline"],
            value_vars=compression_features,
            var_name="Metrics",
            value_name="Compression",
        )

        pallete = {k: v["color"] for k, v in compression_features.items()}

        if len(data) == 0:
            raise Exception("No data in CSV")

        g = sns.catplot(
            x="Pipeline",
            y="Compression",
            hue="Metrics",
            data=melted_df,
            height=8,
            kind="bar",
            alpha=0.5,
            palette=pallete,
            legend_out=True,
        )

        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.9)

        if baseline:
            plt.hlines(baseline["value"], *g.ax.get_xlim(), **baseline["style"], label=baseline["name"])

        g.despine(left=True, bottom=False)
        g.set_ylabels("Compression Factor")

    def plot_connectivity_map(self, data, title, hardware_list):
        sns.set(style="darkgrid", font_scale=1.5)
        hw_name = data["Pipeline Output Hardware Name"].to_list()[0]
        if not isinstance(hardware_list, list):
            raise TypeError("hardware_list is not a list")

        for cfg in hardware_list:
            hw = hardware_by_name(cfg)
            if hw.name == hw_name:
                break

        cmap = sns.light_palette((260, 75, 60), input="husl")
        adj_mat = hw.qubit_connectivity._connectivity
        num_qubs = adj_mat.shape[0]
        g = sns.heatmap(
            adj_mat,
            cmap=cmap,
            linewidths=0.5,
            center=1,
            cbar_kws={"shrink": 1.0},
            square=True,
            alpha=0.5,
            cbar=False,
            xticklabels=np.arange(num_qubs),
            yticklabels=np.arange(num_qubs),
        )

        title = hw_name
        if title is not None:
            plt.suptitle(title, fontweight="bold")
            plt.subplots_adjust(top=0.9)
