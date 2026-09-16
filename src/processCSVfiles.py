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
from plotly.colors import qualitative
from plotly.subplots import make_subplots
from scipy.signal import find_peaks

from modules.csv_data import CsvData
from utils.readAndWrite import (
    check_input_and_get_files,
    get_input_from_args_or_dialog,
    write_to_csv,
)
from utils.utils import extract_info, plot_results

debug = False


def main(input_path_or_files):
    outName = datetime.datetime.now().strftime("%Y-%m-%d") + "_summary_Mmax" ".csv"

    filtered_files = check_input_and_get_files(input_path_or_files, outName)
    list_of_csvs = [CsvData.from_file(file) for file in filtered_files]

    out_df = process_csv_files_in_folder(list_of_csvs)


    current_folder = os.getcwd()
    out_csv = os.path.join(current_folder,'output', outName)
    out_df = out_df.sort_values(by=['D/t', 'Qh', 'Ls', 'Lr'])
    write_to_csv(out_csv, out_df)

    print("Done")




def process_csv_files_in_folder(list_of_csvs) -> pd.DataFrame:
    """ Processes a list of CSV data objects and generates a summary DataFrame and plots. """
    summary_df = pd.DataFrame()

    for csv_data in list_of_csvs:
        add_general_info_from_file_name(csv_data)
        processed_df = process_csv_file_in_folder(csv_data)
        summary_df = pd.concat([summary_df, processed_df])

    plot_csv_data(list_of_csvs)


    return summary_df


def process_csv_file_in_folder(csv_data, savefile=False) -> pd.DataFrame:
    """ Selects the rows at the peaks and dips of the 'Moment' column within the 'Trawl' step of the CSV data.
    Returns the line at the peaks and dips of the 'Moment' column within the 'Trawl' step. """

    df = csv_data.df
    step = df[df["Step name"] == "Trawl"]

    thr = None
    peaks, _ = find_peaks(step["Moment"], height=thr)
    dips, _ = find_peaks(-step["Moment"], height=thr)

    csv_data.peak_index = np.sort(np.r_[peaks, dips])

    line_at_peak = df.iloc[csv_data.peak_index].copy()

    info_df = pd.DataFrame(
        [csv_data.general_info] * len(line_at_peak),
        index=line_at_peak.index,
    )
    return_line = pd.concat([info_df, line_at_peak], axis=1)


    if savefile:
        outname = csv_data.filepath.stem + "_processed.csv"
        outpath = os.path.join(csv_data.filepath.parent, "processed")  # Ensure the file path is available
        csv_data.save_to_csv(os.path.join(outpath, outname))


    return return_line




def add_general_info_from_file_name(csv_data):
    clean_file_name = csv_data.filepath.name.rsplit("_Main")[0]
    general_info = extract_info(clean_file_name)
    general_info["Sim ID"] = clean_file_name
    csv_data.add_general_info(**general_info)


def plot_csv_data(list_of_csvs):

    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.08)
    colors = qualitative.Plotly
    color_map = {}

    for csv_data in list_of_csvs:
        simulation_name = csv_data.general_info["Sim ID"]
        step = csv_data.df[csv_data.df["Step name"] == "Trawl"]

        if simulation_name not in color_map:
            color_map[simulation_name] = colors[len(color_map) % len(colors)]

        plot_results(fig, step["Displacement"], step["End1 RF1 Force"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color_map[simulation_name], row=1, col=1)
        plot_results(fig, step["Wire force"], step["Moment"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color_map[simulation_name], row=2, col=1)
        plot_results(fig, step["ESF1"], step["Moment"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color_map[simulation_name], row=3, col=1)

    fig.update_layout(height=1600, width=1600)
    fig.show()


if __name__ == "__main__":
    default_folder = r"\\osl5207.verit.dnv.com\beegfs-hpc_lagu_rp_osl\sign\mareie\IAS\CSV"
    selected_input = get_input_from_args_or_dialog(default_folder)

    if not selected_input:
        print("No input selected. Exiting.")
    else:
        main(selected_input)
