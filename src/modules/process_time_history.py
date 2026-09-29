import os
from dataclasses import asdict

import numpy as np
import pandas as pd

from modules.code_check import calculate_utilization_factor_STF101
from modules.peak_processing import process_peaks
from modules.PointLoad import calculate_utilization_g_hat
from utils.utils import interpolate_one_column

# Constants
MM_TO_M = 1e-3
MPA_TO_PA = 1e6
kN_TO_N = 1e3
kNm_TO_NM = 1e3


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



def process_time_csv_file(csv_data, savefile=True) -> pd.DataFrame:
    """ Selects the rows at the peaks and dips of the 'Moment' column within the 'Trawl' step of the CSV data.
    Returns the line at the peaks and dips of the 'Moment' column within the 'Trawl' step. """
    df = csv_data.df
    pipe = csv_data.pipe
    capacity = pipe.capacity

    derived_df = calculate_derived_columns(df, pipe, capacity)
    add_derived_columns(csv_data, derived_df)

    line_at_peaks = process_peaks(df, csv_data.general_info['Qh'], csv_data.peak_index)


    columns_to_extract_at_g_hat = ['StepTime', 'Wire force', 'ESF1', 'Moment', 'Max ovalization in sections', 'LE.LE11', 'Lateral Displacement', 'LCC utilization', 'g_hat']
    g_hat_row = extract_g_hat_failure_info(df, columns_to_extract_at_g_hat_1=columns_to_extract_at_g_hat)


    info_df = pd.DataFrame(
        [csv_data.general_info] * len(line_at_peaks),
        index=line_at_peaks.index,
    )


    if savefile:
        save_processed_file(csv_data)

    save_columns = ['Temperature_1', 'ESF1', 'Moment', 'Lateral Displacement', 'LCC utilization']
    save_file_df = df[save_columns].iloc[0:1]

    return_line = pd.concat([info_df, save_file_df, line_at_peaks, g_hat_row], axis=1)

    return return_line


def process_time_history_g_hat(moment, wire_force, pipe, capacity):
    """
    returns a new pd.DataFrame with only the derived parameters and the calculated g_hat, which can be merged with the original time history dataframe if needed.
    """


    Ry_kN = 3.9 * pipe.ys * pipe.wt**2 / 1000  # default is inplace = False, so this creates a new dataframe with the new column, which is what we want here to avoid modifying the original dataframe

    #th_df['Ry_kN'] = 3.9 * pipe_info['YS'] * pipe_info['WT']**2 / 1000
    q_kN = wire_force                    # multiply by 2 to get total force on pipe, not just force on one side
    q_by_ry = q_kN / Ry_kN

    moment_term = moment / pipe.mpc
    g_hat = calculate_utilization_g_hat(moment_term, q_by_ry, capacity.D_t, capacity.delta_P_Pb)

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


def calculate_derived_columns(df, pipe, capacity) -> pd.DataFrame:
    g_hat = process_time_history_g_hat(df["Moment"] * 1000, df["Wire force"], pipe, capacity)

    gradient = np.gradient(df['Moment'], df['LE.LE11']) # Gradient is better than diff due to same length of values and better handling of noise. Might change to savgol filter later if we want to smooth it out more.

    moment_term = df['Moment'] * 1000 / capacity.mpc
    force_term = df['ESF1'] * 1000 / capacity.spc
    pressure_term = capacity.delta_p_pbc * capacity.gamma_p
    LCC_utilization = calculate_utilization_factor_STF101(moment_term=moment_term, force_term=force_term, pressure_term=pressure_term)


    return pd.DataFrame(
        {
            "g_hat": g_hat,
            "grad(M/LE.LE11)": gradient,
            "LCC utilization": LCC_utilization,
        },
        index=df.index,
    )

def add_derived_columns(csv_data, derived_columns):
    metadata = {
        "g_hat": ("g^ calculation", "Utilization"),
        "grad(M/LE.LE11)": (
            "Gradient of Moment with respect to LE.LE11",
            "Hardening",
        ),
        "LCC utilization": (
            "LCC Utilization Factor",
            "Utilization based on LCC",
        ),
    }
    for name in derived_columns.columns:
        info, description = metadata[name]
        csv_data.add_column(
            name=name,
            values=derived_columns[name],
            info=info,
            description=description,
        )

def save_processed_file(csv_data) -> None:
        capacity = csv_data.pipe.capacity
        csv_data.header_info.update(asdict(capacity))  # Complex and confusing formulation, but dont want to pass capacity separately

        # save_columns = ['SimID', 'D/t', 'Qh', 'YS', 'TS', 'WT', 'OD', 'Temperature_1', 'ESF1', 'Moment', 'Lateral Displacement']
        outname = csv_data.filepath.stem + "_processed.csv"
        processed_file_directory = os.path.join(csv_data.filepath.parent, "processed")  # Ensure the file path is available
        csv_data.save_to_csv(os.path.join(processed_file_directory, outname))
        print("Processed CSV saved to:", os.path.join(processed_file_directory, outname))
