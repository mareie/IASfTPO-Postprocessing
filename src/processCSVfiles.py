"""
Post-processing script for summarizing results from processed trawling analysis.
Reads in all CSV files in a specified folder, processes the data, and generates a summary CSV file.
The script performs the following steps:
1. Reads in CSV files containing time history data for trawling simulations.
2. Extracts relevant information from the file names and CSV content, including simulation parameters and time history data.
"""
import datetime
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots
from scipy.signal import find_peaks

from modules.csv_data import CsvData
from utils.readAndWrite import check_input_and_get_files, get_input_from_args_or_dialog
from utils.utils import extract_info, write_to_csv

debug = False


def main(input_path_or_files):
    outName = datetime.datetime.now().strftime("%Y-%m-%d") + "_summary_Mmax" ".csv"

    filtered_files = check_input_and_get_files(input_path_or_files, outName)
    list_of_csvs = [CsvData.from_file(os.path.join(file)) for file in filtered_files]

    out_df = process_csv_files_in_folder(list_of_csvs)


    current_folder = os.getcwd()
    out_csv = os.path.join(current_folder,'output', outName)
    # out_df = out_df.sort_values(by=['D/t', 'Qh', 'YS', 'TS', 'WT', 'lf', 'af', 'T Ratio', 'RestartID'])
    write_to_csv(out_csv, out_df)

    print("Done")




def process_csv_files_in_folder(list_of_csvs) -> pd.DataFrame:
    """ Processes a list of CSV data objects and generates a summary DataFrame and plots. """
    summary_df = pd.DataFrame()
    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.08)
    colors = qualitative.Plotly
    color_map = {}

    for csv_data in list_of_csvs:
        add_info_from_name(csv_data)
        simulation_name = csv_data.header_info["ODB name"].rsplit("_Main")[0]
        if simulation_name not in color_map:
            color_map[simulation_name] = colors[len(color_map) % len(colors)]

        processed_df = process_csv_file_in_folder(
            csv_data,
            fig,
            color_map[simulation_name],
        )

        summary_df = pd.concat([summary_df, processed_df])


    fig.update_layout(height=1600, width=1600)
    fig.show()

    return summary_df


def process_csv_file_in_folder(csv_data, fig, color) -> pd.DataFrame:
    """ Selects the rows at the peaks and dips of the 'Moment' column within the 'Trawl' step of the CSV data.
    Returns the line at the peaks and dips of the 'Moment' column within the 'Trawl' step. """

    df = csv_data.df


    step = df[df["Step name"] == "Trawl"]

    thr = None
    peaks, _ = find_peaks(step["Moment"], height=thr)
    dips, _ = find_peaks(-step["Moment"], height=thr)

    csv_data.peak_index = np.sort(np.r_[peaks, dips])

    line_at_peak = df.iloc[csv_data.peak_index].copy()
    plot_results(fig, step["Displacement"], step["End1 RF1 Force"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color, row=1, col=1)
    plot_results(fig, step["Wire force"], step["Moment"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color, row=2, col=1)
    plot_results(fig, step["ESF1"], step["Moment"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color, row=3, col=1)

    info_df = pd.DataFrame(
        [csv_data.general_info] * len(line_at_peak),
        index=line_at_peak.index,
    )
    return_line = pd.concat([info_df, line_at_peak], axis=1)

    return return_line


def plot_results(fig, x, y, md, header_info, peaks, color, row=None, col=None):

    trace_name = f"{header_info['ODB name'].rsplit('_Main')[0]}"
    trace = go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name=trace_name,
        line={"color": color},
        legendgroup=trace_name,
        hovertemplate=f"x: %{{x}}<br>y: %{{y}}<extra>{trace_name}</extra>",
        showlegend=row is None or row == 1,
    )
    if row is None or col is None:
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)

    peak_trace = go.Scatter(
        x=x.iloc[peaks],
        y=y.iloc[peaks],
        # mode="markers+text",
        marker={"color": "red"},
        # text=[f"y: {y.iloc[peak]:.0f}" for peak in peaks],
        # textposition="top center",
        name="Peaks",
        hovertemplate=f"x: %{{x}}<br>y: %{{y}}<extra>{trace_name}</extra>",
        legendgroup=trace_name,
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


def add_info_from_name(csv_data):
    general_info = extract_info(csv_data.header_info["ODB name"])
    general_info["Sim ID"] = csv_data.header_info["ODB name"].rsplit("_Main")[0]
    csv_data.add_general_info(**general_info)


if __name__ == "__main__":
    default_folder = r"\\osl5207.verit.dnv.com\beegfs-hpc_lagu_rp_osl\sign\mareie\IAS\CSV"
    selected_input = get_input_from_args_or_dialog(default_folder)

    if not selected_input:
        print("No input selected. Exiting.")
    else:
        main(selected_input)






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