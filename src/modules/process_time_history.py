import pandas as pd
from modules.combinedLoading import calculate_load_terms, calculate_capacity_parameters, calculate_utilization_factor_G0
from modules.PointLoad import calculate_utilization_g_hat


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

def process_time_history_G0(df, pipe_info, safety_factor=1):

    calculate_capacity_parameters(pipe_info)
    calculate_load_terms(df, pipe_info)

    calculate_utilization_factor_G0(df)

    return df['G_0']

def process_time_history_L1p2p2(df, pipe_info, safety_factor=1):

    calculate_capacity_parameters(pipe_info)
    calculate_load_terms(df, pipe_info)

    x_data = (
        pipe_info["D/t"],
        df["M_load"] / pipe_info["moment_plastic"], # Moment_term
        df["effective_axial_load"] / pipe_info["axial_load_capacity_plastic"], # Force_term
        pipe_info['delta_P/Pb'], # Pressure_term
        pipe_info["YS/TS"],
    )
    calculate_utilization_factor_L1p2p2(x_data, df)

    return df['L_1p2p2']

# Calculating Moment capacity Mcap.  Could be merged with the above function.
def process_time_history_Mcap(df, pipe_info, safety_factor=1):

    calculate_capacity_parameters(pipe_info)
    calculate_load_terms(df, pipe_info)

    x_data = (
        pipe_info["D/t"],
        df["M_load"] / pipe_info["moment_plastic"], # Moment_term
        df["effective_axial_load"] / pipe_info["axial_load_capacity_plastic"], # Force_term
        pipe_info['delta_P/Pb'], # Pressure_term
        pipe_info["YS/TS"],
    )
    calculate_Mcap_L1p2p2(x_data, df)

    df['Mcap_L_1p2p2_kNm'] = df['Mcap_L_1p2p2'] * pipe_info['moment_plastic'] / 1000 # kNm. remember to multiply with moment_plastic to get the actual moment capacity in Nm
    return df['Mcap_L_1p2p2_kNm']


def process_time_history_g_hat(th_df, pipe_info, th_df_derived) -> pd.DataFrame:
    """
    returns a new pd.DataFrame with only the derived parameters and the calculated g_hat, which can be merged with the original time history dataframe if needed.
    """

    org_columns = th_df.columns.tolist()

    th_df = th_df.assign(Ry_kN = 3.9 * pipe_info['YS'] * pipe_info['WT']**2 / 1000) # default is inplace = False, so this creates a new dataframe with the new column, which is what we want here to avoid modifying the original dataframe

    #th_df['Ry_kN'] = 3.9 * pipe_info['YS'] * pipe_info['WT']**2 / 1000
    th_df['Q_kN'] = 2 * th_df['Wire force']                         # multiply by 2 to get total force on pipe, not just force on one side
    th_df['Q/Ry'] = th_df['Q_kN'] / th_df['Ry_kN']

    moment_term = th_df_derived['M/Mpc']
    th_df['g_hat'] = calculate_utilization_g_hat(moment_term, th_df['Q/Ry'], pipe_info['D/t'], pipe_info['delta_P/Pb'])

    return th_df.drop(columns=org_columns)