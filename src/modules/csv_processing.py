import os

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from modules.plotting import plot_csv_data
from utils.utils import add_general_info_from_file_name


def process_csv_files(list_of_csvs) -> pd.DataFrame:
    """ Processes a list of CSV data objects and generates a summary DataFrame and plots. """
    summary_df = pd.DataFrame()

    for csv_data in list_of_csvs:
        add_general_info_from_file_name(csv_data)
        processed_df = process_csv_file(csv_data)
        summary_df = pd.concat([summary_df, processed_df])

    plot_csv_data(list_of_csvs)


    return summary_df


def process_csv_file(csv_data, savefile=False) -> pd.DataFrame:
    """ Selects the rows at the peaks and dips of the 'Moment' column within the 'Trawl' step of the CSV data.
    Returns the line at the peaks and dips of the 'Moment' column within the 'Trawl' step. """

    df = csv_data.df
    step = df[df["Step name"] == "Trawl"]

    thr = None
    peaks, _ = find_peaks(step["Moment"], height=thr)
    # dips, _ = find_peaks(-step["Moment"], height=thr)

    # csv_data.peak_index = np.sort(np.r_[peaks, dips])
    csv_data.peak_index = peaks

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

