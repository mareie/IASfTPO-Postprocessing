"""
Post-processing script for summarizing results from processed trawling analysis.
Reads in all CSV files in a specified folder, processes the data, and generates a summary CSV file.
The script performs the following steps:
1. Reads in CSV files containing time history data for trawling simulations.
2. Extracts relevant information from the file names and CSV content, including simulation parameters and time history data.
"""


from asyncio import events
import sys
import os

# import copy
import re
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import datetime
from plotly.subplots import make_subplots

from utils.readAndWrite import get_input_from_args_or_dialog, check_input_and_get_files
from utils.utils import write_to_csv, extract_info_from_name

from scipy.signal import find_peaks, step
from modules.csv_data import CsvData

debug = False


def main(input_path_or_files):
    outName = datetime.datetime.now().strftime("%Y-%m-%d") + ".csv"

    filtered_files = check_input_and_get_files(input_path_or_files, outName)
    list_of_csvs = [CsvData.from_file(os.path.join(file)) for file in filtered_files]

    out_df =process_csv_files_in_folder(list_of_csvs)


    # current_folder = os.getcwd()
    # out_csv = os.path.join(current_folder, outName)
    # out_df = out_df.sort_values(by=['D/t', 'Qh', 'YS', 'TS', 'WT', 'lf', 'af', 'T Ratio', 'RestartID'])
    # write_to_csv(out_csv, out_df)

    print("Done")




def process_csv_files_in_folder(list_of_csvs) -> pd.DataFrame:
    out_df = pd.DataFrame()
    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.08)
    for csv_data in list_of_csvs:
        thr = None
        df = csv_data.df
        step = df[df["Step name"] == "Trawl"]

        peaks, _ = find_peaks(step["Moment"], height=thr)
        dips, _ = find_peaks(-step["Moment"], height=thr)

        events = np.sort(np.r_[peaks, dips])

        plot_results(fig, step["Displacement"], step["End1 RF1 Force"], csv_data.metadata, csv_data.sim_info, events, row=1, col=1)
        plot_results(fig, step["Wire force"], step["Moment"], csv_data.metadata, csv_data.sim_info, events, row=2, col=1)
        plot_results(fig, step["ESF1"], step["Moment"], csv_data.metadata, csv_data.sim_info, events, row=3, col=1)

        line_of_peak = step.iloc[events].copy()
        line_of_peak["ODB name"] = csv_data.sim_info["ODB name"]

        out_df = pd.concat([out_df, line_of_peak])
    fig.update_layout(height=1600, width=1600)
    fig.show()

    return out_df

def extract_and_rename_peaks_to_dataframe(df, peak_indices, governing=False):
    """
    Extract peak data as a single row with multiple peaks across columns.

    Returns one row per simulation with columns like: Peak1_ESF1, Peak2_ESF1, etc.
    """
    peak_name = lambda n, col: f"Peak{n}_{col}"
    gov_name = lambda _, col: f"Gov_{col}"
    name_fn = gov_name if governing else peak_name

    peaks_df = df.iloc[peak_indices].reset_index(drop=True)
    peaks_df.index += 1
    peaks_df = (
        peaks_df.stack()
        .to_frame()
        .T.pipe(lambda x: x.set_axis([name_fn(n, col) for n, col in x.columns], axis=1))
    )

    return peaks_df


def plot_results(fig, x, y, md, sim_info, peaks, row=None, col=None):

    trace_name = f"{sim_info['ODB name'].rsplit('_Main')[0]}"
    trace = go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name=trace_name,
        legendgroup=trace_name,
        showlegend=row is None or row == 1,
    )
    if row is None or col is None:
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)

    for peak in peaks:
        annotation = {
            "x": x.iloc[peak],
            "y": y.iloc[peak],
            "text": f"y: {y.iloc[peak]:.0f}",
            "showarrow": False,
            "yshift": 10,
        }
        if row is None or col is None:
            fig.add_annotation(annotation)
        else:
            fig.add_annotation(annotation, row=row, col=col)

    peak_trace = go.Scatter(
        x=x.iloc[peaks],
        y=y.iloc[peaks],
        mode="markers",
        marker={"color": "red"},
        name="Peaks",
        showlegend=False,
    )
    if row is None or col is None:
        fig.add_trace(peak_trace)
        fig.update_layout(
            xaxis_title=f'{md[x.name]["description"]}',
            yaxis_title=f'{md[y.name]["description"]}',
            title=f"{x.name} vs {y.name}",
        )
    else:
        fig.add_trace(peak_trace, row=row, col=col)
        fig.update_xaxes(title_text=f'{md[x.name]["description"]}', row=row, col=col)
        fig.update_yaxes(title_text=f'{md[y.name]["description"]}', row=row, col=col)


def process_csv_file_in_folder(csv_data) -> pd.DataFrame:
    thr = 1.0
    df = csv_data.df
    step = df[df["Step name"] == "Trawl"]

    peaks, _ = find_peaks(step["Moment"], height=thr)
    dips, _ = find_peaks(-step["Moment"], height=thr)

    events = np.sort(np.r_[peaks, dips])

    # mask = (step.loc[events, 'KP'] > 6) & (step.loc[events, 'KP'] < 6.6)

    # step.iloc[events][(step["KP"] > 6) & (step["KP"] < 6.8)][["KP", "Node label"]]
    fig = go.Figure()
    plot_results(fig, step["StepTime"], step["Moment"], csv_data.metadata, csv_data.sim_info, events)

    # ind = step.iloc[events][(step["KP"] > 6) & (step["KP"] < 6.8)][
    #     ["KP", "Node label"]
    # ].index[1]
    fig.show()
    print("hei")

    return pd.DataFrame()


if __name__ == "__main__":
    default_folder = r"\\osl5207.verit.dnv.com\beegfs-hpc_lagu_rp_osl\sign\mareie\PD20_trawl\modelA\CSV\processed"
    selected_input = get_input_from_args_or_dialog(default_folder)

    if not selected_input:
        print("No input selected. Exiting.")
    else:
        main(selected_input)
