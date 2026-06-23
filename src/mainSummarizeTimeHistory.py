#%%
"""
Post-processing script for summarizing results from processed trawling analysis.
Reads in all CSV files in a specified folder, processes the data, and generates a summary CSV file.
The script performs the following steps:
1. Reads in CSV files containing time history data for trawling simulations.
2. Extracts relevant information from the file names and CSV content, including simulation parameters and time history data.
"""
#%%
import sys
import os
# import copy
import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime

from utils.readAndWrite import get_input_from_args_or_dialog, check_input_and_get_files
from utils.utils import read_in_csv_results, write_to_csv, extract_info_from_name

from scipy.signal import find_peaks, step

debug = False
def main(input_path_or_files):
    outName = datetime.datetime.now().strftime("%Y-%m-%d") + '.csv'
    current_folder = os.getcwd()

    filtered_files = check_input_and_get_files(input_path_or_files, outName)


    out_csv = os.path.join(current_folder, outName)
    out_df = pd.DataFrame()

    for file in filtered_files:

        df = read_in_csv_results(os.path.join(file))
        process_csv_files_in_folder(df)

    # out_df = out_df.sort_values(by=['D/t', 'Qh', 'YS', 'TS', 'WT', 'lf', 'af', 'T Ratio', 'RestartID'])
    # write_to_csv(out_csv, out_df)

    print("Done")

def process_csv_files_in_folder(df) -> pd.DataFrame:
    thr = 1.0

    step = df[df['Step name'] == 'Operationalatdesignconditions']

    peaks, _ = find_peaks(step['Lateral displacement'], height=thr)
    dips, _ = find_peaks(-step['Lateral displacement'], height=thr)

    events = np.sort(np.r_[peaks, dips])

    # mask = (step.loc[events, 'KP'] > 6) & (step.loc[events, 'KP'] < 6.6)

    step.iloc[events][(step['KP']>6) & (step['KP']<6.8)][['KP', 'Node label']]
    plot_results(step['KP'], step['Lateral displacement'], events)

    print("hei")


    return pd.DataFrame()



def extract_and_rename_peaks_to_dataframe(df, peak_indices, governing=False):
    """
    Extract peak data as a single row with multiple peaks across columns.

    Returns one row per simulation with columns like: Peak1_ESF1, Peak2_ESF1, etc.
    """
    peak_name = lambda n, col: f'Peak{n}_{col}'
    gov_name = lambda _, col: f'Gov_{col}'
    name_fn = gov_name if governing else peak_name

    peaks_df = df.iloc[peak_indices].reset_index(drop=True)
    peaks_df.index += 1
    peaks_df = (
        peaks_df
        .stack()
        .to_frame()
        .T
        .pipe(lambda x: x.set_axis([name_fn(n, col) for n, col in x.columns], axis=1))
    )

    return peaks_df



def plot_results(x, y, peaks):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(x, y, label='Moment')
    for peak in peaks:
        ax1.annotate(f'{x.iloc[peak]:.2f}s', (x.iloc[peak], y.iloc[peak]), textcoords="offset points", xytext=(0,10), ha='center')
    ax1.scatter(x.iloc[peaks], y.iloc[peaks], color='orange', label='Peaks')
    # ax2 = ax1.twinx()
    # ax2.plot(x, df['grad(M/LE.LE11)'], label='Grad(M/LE.LE11)', color='r')
    ax1.set_xlabel(f'{x.name}')
    ax1.set_ylabel(f'{y.name}')
    # ax2.set_ylabel('Grad (M/LE.LE11) [-]')
    # ymax = df['grad(M/LE.LE11)'].quantile([0.5])
    # ax2.set_ylim(-ymax.values[0], ymax.values[0])
    ax1.set_title(f'Title')
    ax1.legend(loc='best')
    # ax2.legend(loc='upper right')
    ax1.grid()
    plt.show()


if __name__ == '__main__':
    default_folder = r'\\osl5207.verit.dnv.com\beegfs-hpc_lagu_rp_osl\sign\mareie\PD20_trawl\modelA\CSV\processed'
    selected_input = get_input_from_args_or_dialog(default_folder)

    if not selected_input:
        print("No input selected. Exiting.")
    else:
        main(selected_input)

