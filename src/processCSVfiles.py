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
import matplotlib.pyplot as plt
import pandas as pd
import datetime

from utils.readAndWrite import get_input_from_args_or_dialog, check_input_and_get_files
from utils.utils import write_to_csv, extract_info_from_name

from scipy.signal import find_peaks, step
from modules.csv_data import CsvData

debug = False


def main(input_path_or_files):
    outName = datetime.datetime.now().strftime("%Y-%m-%d") + ".csv"
    current_folder = os.getcwd()

    filtered_files = check_input_and_get_files(input_path_or_files, outName)

    out_csv = os.path.join(current_folder, outName)
    out_df = pd.DataFrame()
    list_of_csvs =[]
    for file in filtered_files:

        csv_data = CsvData.from_file(os.path.join(file))
        # df = csv_data.df
        # process_csv_files_in_folder(csv_data)
        list_of_csvs.append(csv_data)



    process_csv_files_in_folder(list_of_csvs)
    # out_df = out_df.sort_values(by=['D/t', 'Qh', 'YS', 'TS', 'WT', 'lf', 'af', 'T Ratio', 'RestartID'])
    # write_to_csv(out_csv, out_df)

    print("Done")


def process_csv_file_in_folder(csv_data) -> pd.DataFrame:
    thr = 1.0
    df = csv_data.df
    step = df[df["Step name"] == "Trawl"]

    peaks, _ = find_peaks(step["Moment"], height=thr)
    dips, _ = find_peaks(-step["Moment"], height=thr)

    events = np.sort(np.r_[peaks, dips])

    # mask = (step.loc[events, 'KP'] > 6) & (step.loc[events, 'KP'] < 6.6)

    # step.iloc[events][(step["KP"] > 6) & (step["KP"] < 6.8)][["KP", "Node label"]]
    plot_results(step["StepTime"], step["Moment"], csv_data.metadata, events)

    # ind = step.iloc[events][(step["KP"] > 6) & (step["KP"] < 6.8)][
    #     ["KP", "Node label"]
    # ].index[1]
    plt.show()
    print("hei")

    return pd.DataFrame()

def process_csv_files_in_folder(list_of_csvs) -> pd.DataFrame:
    out_df = pd.DataFrame()
    fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(10, 6))
    for csv_data in list_of_csvs:
        thr = 1.0
        df = csv_data.df
        step = df[df["Step name"] == "Trawl"]

        peaks, _ = find_peaks(step["Moment"], height=thr)
        dips, _ = find_peaks(-step["Moment"], height=thr)

        events = np.sort(np.r_[peaks, dips])

        # mask = (step.loc[events, 'KP'] > 6) & (step.loc[events, 'KP'] < 6.6)

        # step.iloc[events][(step["KP"] > 6) & (step["KP"] < 6.8)][["KP", "Node label"]]
        plot_results(ax[0], step["Displacement"], step["End1 RF1 Force"], csv_data.metadata, csv_data.sim_info, events)

        thr = 1.0

        plot_results(ax[1], step["Wire force"], step["Moment"], csv_data.metadata, csv_data.sim_info, events)
        plot_results(ax[2], step["ESF1"], step["Moment"], csv_data.metadata, csv_data.sim_info, events)



        out_df = pd.concat([out_df, pd.DataFrame()])
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[2].legend(loc="best")
    ax[0].grid()
    ax[1].grid()
    ax[2].grid()
    plt.show()

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


def plot_results(ax, x, y, md, sim_info, peaks):

    ax.plot(x, y, label=f"{sim_info['ODB name'].rsplit('_Main')[0]}")
    for peak in peaks:
        ax.annotate(
            f"y: {y.iloc[peak]:.2f}",
            (x.iloc[peak], y.iloc[peak]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
        )
    ax.scatter(x.iloc[peaks], y.iloc[peaks], color="red")
    ax.set_xlabel(f'{md[x.name]["description"]}')
    ax.set_ylabel(f'{md[y.name]["description"]}')
    ax.set_title(f"{x.name} vs {y.name}")




if __name__ == "__main__":
    default_folder = r"\\osl5207.verit.dnv.com\beegfs-hpc_lagu_rp_osl\sign\mareie\PD20_trawl\modelA\CSV\processed"
    selected_input = get_input_from_args_or_dialog(default_folder)

    if not selected_input:
        print("No input selected. Exiting.")
    else:
        main(selected_input)




