import os
from dataclasses import asdict

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from modules.peak_processing import process_peaks
from modules.pipe import Pipe
from modules.PointLoad import calculate_utilization_g_hat
from utils.utils import interpolate_one_column

# Constants
MM_TO_M = 1e-3
MPA_TO_PA = 1e6
kN_TO_N = 1e3
kNm_TO_NM = 1e3

# Pipe configuration data
PIPE_INFO = {
    22.6: {'OD': 0.32385, 'Nominal WT': 14.3, 'Nominal YS': 450, 'Nominal TS': 535},
    32: {'OD': 0.9144, 'Nominal WT': 28.6, 'Nominal YS': 480, 'Nominal TS': 550},
    15.1: {'OD': 0.2032, 'Nominal WT': 13.5, 'Nominal YS': 480, 'Nominal TS': 550},
}

def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    df['Moment'] = df['Moment'] * kNm_TO_NM
    df['ESF1'] = df['ESF1'] * kN_TO_N
    return df

def convert_units_info(df):
    df['YS'] = df['YS'] * MPA_TO_PA
    df['TS'] = df['TS'] * MPA_TO_PA
    df['WT'] = df['WT'] * MM_TO_M
    df['Nom YS'] = df['Nom YS'] * MPA_TO_PA
    df['Nom TS'] = df['Nom TS'] * MPA_TO_PA
    df['Nom WT'] = df['Nom WT'] * MM_TO_M
    return df

def add_pipe_properties(df: pd.DataFrame) -> pd.DataFrame:
    for dt_ratio, properties in PIPE_INFO.items():
        if df['D/t'] == dt_ratio:
            df['OD'] = properties['OD']
            df['Nom WT'] = properties['Nominal WT']
            df['Nom YS'] = properties['Nominal YS']
            df['Nom TS'] = properties['Nominal TS']
    return df

def process_time_csv_file(csv_data, savefile=True) -> pd.DataFrame:
    """ Selects the rows at the peaks and dips of the 'Moment' column within the 'Trawl' step of the CSV data.
    Returns the line at the peaks and dips of the 'Moment' column within the 'Trawl' step. """

    df = csv_data.df
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
    capacity = pipe.calculate_capacity_parameters_STF101()


    csv_data.attach_pipe(pipe)

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

    if savefile:
        save_processed_file(csv_data)



    return return_line


def process_time_history_g_hat(moment, wireforce, pipe):
    """
    returns a new pd.DataFrame with only the derived parameters and the calculated g_hat, which can be merged with the original time history dataframe if needed.
    """


    Ry_kN = 3.9 * pipe.ys * pipe.wt**2 / 1000  # default is inplace = False, so this creates a new dataframe with the new column, which is what we want here to avoid modifying the original dataframe

    #th_df['Ry_kN'] = 3.9 * pipe_info['YS'] * pipe_info['WT']**2 / 1000
    q_kN = wireforce                    # multiply by 2 to get total force on pipe, not just force on one side
    q_by_ry = q_kN / Ry_kN

    moment_term = moment / pipe.mpc
    g_hat = calculate_utilization_g_hat(moment_term, q_by_ry, pipe.D_t, pipe.delta_P_Pb)

    return g_hat


def extract_g_hat_failure_info(df, columns_to_extract_at_g_hat_1: list[str]):
    """
    Extract information where g_hat = 1.0, using interpolation.
    Returns a DataFrame with relevant data corresponding to g_hat = 1.0.
    """
    g_hat_row = pd.Series(dtype='float64')
    for col in columns_to_extract_at_g_hat_1:
        g_hat_row[f'g_hat_{col}'] = interpolate_one_column(df[col], df['g_hat'], 1.0)
    return pd.DataFrame([g_hat_row])


def save_processed_file(csv_data) -> None:
        capacity = csv_data.pipe.capacity
        csv_data.header_info.update(asdict(capacity))  # Complexed and cunfusing formulation, but dont want to pass capacity separately

        # save_columns = ['SimID', 'D/t', 'Qh', 'YS', 'TS', 'WT', 'OD', 'Temperature_1', 'ESF1', 'Moment', 'Lateral Displacement']
        outname = csv_data.filepath.stem + "_processed.csv"
        outpath = os.path.join(csv_data.filepath.parent, "processed")  # Ensure the file path is available
        csv_data.save_to_csv(os.path.join(outpath, outname))
        print("Processed CSV saved to:", os.path.join(outpath, outname))
