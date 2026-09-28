import os

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from modules.PointLoad import calculate_utilization_g_hat
from modules.plotting import plot_csv_data, plot_path_csv_data
from modules.process_time_history import process_time_history_g_hat, convert_units
from utils.utils import extract_general_info_from_file_name, interpolate_one_column
from modules.pipe import Pipe

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

def process_time_csv_file(csv_data, savefile=False) -> pd.DataFrame:
    """ Selects the rows at the peaks and dips of the 'Moment' column within the 'Trawl' step of the CSV data.
    Returns the line at the peaks and dips of the 'Moment' column within the 'Trawl' step. """

    df = csv_data.df
    # df = convert_units(df)
    step = df[df["Step name"] == "Trawl"]
    pipe = Pipe(
        outer_diameter=273.1 / 1000,  # HARDCODED
        wall_thickness=15.88 / 1000,  # HARDCODED
        yield_strength=450e6,  # HARDCODED
        tensile_strength=535e6,  # HARDCODED
        ys_ts=450e6 / 535e6,  # HARDCODED
        d_over_t=csv_data.general_info["D/t"],
        qh=csv_data.general_info["Qh"],
    )
    pipe.calculate_capacity_parameters()



    thr = None
    peaks, _ = find_peaks(step["Moment"], height=thr)
    csv_data.peak_index = peaks

    g_hat = process_time_history_g_hat(step["Moment"] * 1000, step["Wire force"], pipe)
    csv_data.add_column(name='g_hat', values=g_hat, info="g^ calculation", description="Utilization")

    gradient = np.gradient(df['Moment'], df['LE.LE11']) # Gradient is better than diff due to same length of values and better handling of noise. Might change to savgol filter later if we want to smooth it out more.
    csv_data.add_column(
        name='grad(M/LE.LE11)',
        values=gradient,
        info="Gradient of Moment with respect to LE.LE11",
        description="'Hardening'"
    )

    line_at_peaks = process_peaks(df, csv_data.general_info['Qh'], csv_data.peak_index)
    # Find g_hat = 1.0 and extract the corresponding information
    columns_to_exctract_at_peak = ['StepTime', 'Wire force', 'ESF1', 'Moment', 'Max ovalization in sections', 'LE.LE11', 'g_hat']
    g_hat_row = extract_g_hat_failure_info(df, columns_to_extract_at_g_hat_1=columns_to_exctract_at_peak)


    info_df = pd.DataFrame(
        [csv_data.general_info] * len(line_at_peaks),
        index=line_at_peaks.index,
    )
    return_line = pd.concat([info_df, line_at_peaks, g_hat_row], axis=1)

    save_columns = ['SimID','RestartID', 'D/t', 'Qh', 'YS', 'TS', 'WT', 'lf', 'af', 'T Ratio', 'OD', 'Nom WT', 'Nom YS', 'Nom TS', 'Nom Qh', 'Temperature_1', 'ESF1', 'Moment', 'Lateral Displacement', 'Nom LCC Utilization']

    if savefile:
        outname = csv_data.filepath.stem + "_processed.csv"
        outpath = os.path.join(csv_data.filepath.parent, "processed")  # Ensure the file path is available
        csv_data.save_to_csv(os.path.join(outpath, outname))


    return return_line

def process_peaks(df, qh, peak_indices) -> pd.DataFrame:
    LOOK_AHEAD = { 'Qh_cutoff': 0.4, 'steps_ahead_low_qh': 5, 'steps_ahead_high_qh': 20 }   # Dictionary to determine look-ahead steps based on Qh value
    if qh < LOOK_AHEAD['Qh_cutoff']:
        steps_ahead = LOOK_AHEAD['steps_ahead_low_qh']
    else:
        steps_ahead = LOOK_AHEAD['steps_ahead_high_qh']


    columns_to_exctract_at_peak = ['StepTime', 'Wire force', 'ESF1', 'Moment', 'Max ovalization in sections', 'LE.LE11', 'g_hat']

    if peak_indices.size == 0:
        print(f"No peaks found for {df['SimID'].iloc[0]}.")
        # save_file_df = df[save_columns].iloc[0:1]
        # row_at_value_of_interest = pd.concat([save_file_df], axis=1)
        # return pd.DataFrame(row_at_value_of_interest)

    peak_values_df = extract_and_rename_peaks_to_dataframe(df[columns_to_exctract_at_peak], peak_indices)

    governing_results = pd.DataFrame()
    for index, peak in enumerate(peak_indices, 1):
        if check_future_trend(df['grad(M/LE.LE11)'], peak, look_ahead=steps_ahead):
            governing_results = extract_and_rename_peaks_to_dataframe(df[columns_to_exctract_at_peak], [peak], governing=True)
            governing_results['PeakNumber'] = index
            break
        governing_results = extract_and_rename_peaks_to_dataframe(df[columns_to_exctract_at_peak], [peak], governing=True)
        governing_results['PeakNumber'] = 'None'


    row_at_value_of_interest = pd.concat([governing_results, peak_values_df], axis=1) # best to include g_hat_row before peak_values_df because peak_values_df changes in size

    return row_at_value_of_interest


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

def check_future_trend(df, location, look_ahead=5) -> bool:
    future_vals = df.iloc[location + 1: location + 1 + look_ahead]
    # True only if current + all next look_ahead points are < 0
    return (future_vals < 0).all()


def extract_g_hat_failure_info(df, columns_to_extract_at_g_hat_1: list[str]):
    """
    Extract information where g_hat = 1.0, using interpolation.
    Returns a DataFrame with relevant data corresponding to g_hat = 1.0.
    """
    g_hat_row = pd.Series(dtype='float64')
    for col in columns_to_extract_at_g_hat_1:
        g_hat_row[f'g_hat_{col}'] = interpolate_one_column(df[col], df['g_hat'], 1.0)
    return pd.DataFrame([g_hat_row])

