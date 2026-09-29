import os


import numpy as np
import pandas as pd

from modules.plotting import plot_csv_data, plot_path_csv_data
from modules.process_time_history import process_time_csv_file
from utils.utils import extract_general_info_from_file_name


def process_time_csv_files(list_of_csvs) -> pd.DataFrame:
    """ Processes a list of CSV data objects and generates a summary DataFrame and plots. """
    summary_df = pd.DataFrame()

    for csv_data in list_of_csvs:
        general_info = extract_general_info_from_file_name(csv_data)
        csv_data.add_general_info(**general_info)
        processed_df = process_time_csv_file(csv_data)
        summary_df = pd.concat([summary_df, processed_df])

    # plot_csv_data(list_of_csvs)
    return summary_df


def process_path_csv_files(list_of_csvs) -> pd.DataFrame:
    """ Processes a list of CSV data objects and generates a summary DataFrame and plots. """
    summary_df = pd.DataFrame()

    for csv_data in list_of_csvs:
        general_info = extract_general_info_from_file_name(csv_data)
        csv_data.add_general_info(**general_info)
        plot_path_csv_data(csv_data)
        # processed_df = process_csv_file(csv_data)
        # summary_df = pd.concat([summary_df, processed_df])

    return summary_df







