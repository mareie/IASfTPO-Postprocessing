import pandas as pd
import math



def calculate_capacity_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns df in place with calculated capacity parameters based on DNV-ST-F101 expressions, for actual and nominal properties.
    Note that this assumes: fy = ys.
    In reality: fy = alpha_u *(ys - ys_temp)
    This means that alpha = 1.0 is assumed, i.e. linepipe supp. req. U is fulfuill, and no temperature derating.
    """

    # beta is same for actual and nominal
    df['beta'] = (60 - df['D/t']) / 90

    #actual properties from FEA
    df['alpha_c'] = 1 + df['beta'] * (df['YS/TS']**-1 - 1)
    df['Mp'] = df['YS'] * (df['OD'] - df['WT'])**2 * df['WT']
    df['Mpc'] = df['alpha_c'] * df['Mp']

    df['Sp'] = df['YS'] * math.pi * (df['OD'] - df['WT']) * df['WT']
    df['Spc'] = df['alpha_c'] * df['Sp']

    df['delta_P/Pb'] = math.sqrt(3) / 2  * df['Qh']
    df['delta_P/Pbc'] =  df['delta_P/Pb'] / df['alpha_c']

    if df['delta_P/Pb'] <= 2 / 3:
        df['gamma_p'] = 1 - df['beta']
    elif df['delta_P/Pb'] > 2 / 3:
        df['gamma_p'] = 1 - 3 * df['beta'] * (1 - df['delta_P/Pb'])

    # nominal properties:
    df['Nom alpha_c'] = 1 + df['beta'] * (df['Nom YS/TS']**-1 - 1)
    df['Nom Mp'] = df['Nom YS'] * (df['OD'] - df['Nom WT'])**2 * df['Nom WT']
    df['Nom Mpc'] = df['Nom alpha_c'] * df['Nom Mp']

    df['Nom Sp'] = df['Nom YS'] * math.pi * (df['OD'] - df['Nom WT']) * df['Nom WT']
    df['Nom Spc'] = df['Nom alpha_c'] * df['Nom Sp']

    df['Nom delta_P/Pb'] = math.sqrt(3) / 2  * df['Nom Qh']
    df['Nom delta_P/Pbc'] =  df['Nom delta_P/Pb'] / df['Nom alpha_c']

    if df['Nom delta_P/Pb'] <= 2 / 3:
        df['Nom gamma_p'] = 1 - df['beta']
    elif df['Nom delta_P/Pb'] > 2 / 3:
        df['Nom gamma_p'] = 1 - 3 * df['beta'] * (1 - df['Nom delta_P/Pb'])

    return df


def calculate_load_terms(df: pd.DataFrame, pipe_info) -> pd.DataFrame:
    """
    returns NEW df with ONLY calculated load terms based on DNV-ST-F101 expressions, for actual and nominal properties.
    """
    org_columns = df.columns.tolist()

    df = df.assign(Mload = df['Moment']) # default is inplace = False, so this creates a new dataframe with the new column, which is what we want here to avoid modifying the original dataframe

    df['M/Mp'] = df['Mload'] / pipe_info['Mp']
    df['M/Mpc'] = df['Mload'] / pipe_info['Mpc']
    df['Nom M/Mp'] = df['Mload'] / pipe_info['Nom Mp']
    df['Nom M/Mpc'] = df['Mload'] / pipe_info['Nom Mpc']

    df['S'] = df['ESF1']
    df['S/Sp'] = df['S'] / pipe_info['Sp']
    df['S/Spc'] = df['S'] / pipe_info['Spc']
    df['Nom S/Sp'] = df['S'] / pipe_info['Nom Sp']
    df['Nom S/Spc'] = df['S'] / pipe_info['Nom Spc']

    df['pressure_term'] = pipe_info['delta_P/Pb'] * pipe_info['gamma_p'] / pipe_info['alpha_c']
    df['Nom pressure_term'] = pipe_info['Nom delta_P/Pb'] * pipe_info['Nom gamma_p'] / pipe_info['Nom alpha_c']

    return df.drop(columns=org_columns)


def calculate_utilization_factor_G0(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate g_0 utilization factor combining moment, force, and pressure terms.
    """
    df_copy = df.copy()
    df_copy['g_0'] = ((df_copy['Nom M/Mpc'] + df_copy['Nom S/Spc']**2)**2 + (df_copy['pressure_term'])**2).pow(0.5)  # square root of DNV-ST-F101 expression

    return df_copy['g_0']

def girthweld_factor(df: pd.DataFrame) -> None:
    """Calculate girth weld factor alpha_gw based on D/t ratio.

    Args:
        df: Input dataframe to modify in place
    """
    # For D/t < 20, alpha_gw = 1
    df.loc[df['D/t'] < 20, 'alpha_gw'] = 1

    # For 20 < D/t < 60, linear interpolation from 1 to 0.6
    slope = (0.6 - 1) / (60 - 20)
    intercept = 1 - (slope * 20)
    df.loc[(df['D/t'] > 20) & (df['D/t'] < 60), 'alpha_gw'] = df['D/t'] * slope + intercept


def caluclate_Qh(df: pd.DataFrame) -> pd.Series:
    """Calculate actual Qh parameter based on nominal and actual properties.

    Args:
        df: Input dataframe with pipe properties

    Returns:
        Series with calculated Qh values
    """
    df['nominal_WT'] = df['D/t']**-1 * df['D']
    return (df['Qh'] * df['nominal_YS'] / df['YS']) * \
           ((2 * df['nominal_WT']) / (df['D'] - df['nominal_WT'])) * \
           ((df['D'] - df['WT']) / (2 * df['WT']))


def calculate_moment_capacity(alpha_c, f_y, diameter, thickness) -> pd.Series:
    """Calculate characteristic moment capacity

    Args:
        df: Input dataframe with pipe properties and girth weld factor"""

    plastic_moment = f_y * (diameter - thickness)**2 * thickness
    return alpha_c * plastic_moment


def calculate_axial_load_capacity(alpha_c, f_y, diameter, thickness) -> pd.Series:
    """Calculate characteristic axial load capacity

    Args:
        df: Input dataframe with pipe properties and girth weld factor"""


    plastic_axial_load = f_y * math.pi * (diameter - thickness) * thickness
    return alpha_c * plastic_axial_load


def elastic_collapse_pressure(diameter, thickness, youngs_modulus, poisson_ratio) -> pd.Series:
    """Calculate elastic collapse pressure (eq (5.14))

    Args:
        diameter: Pipe diameter
        thickness: Pipe wall thickness
        youngs_modulus: Young's modulus of the material
        poisson_ratio: Poisson's ratio of the material

    Returns:
        Series with calculated elastic collapse pressure values
    """
    return (2 * youngs_modulus * (thickness/diameter)**3) / (1 - poisson_ratio**2)


def plastic_collapse_pressure(f_y, alpha_fab, diameter, thickness) -> pd.Series:
    """Calculate plastic collapse pressure (eq (5.15))

    Args:
        alpha_c: Capacity reduction factor
        f_y: Yield strength of the material
        diameter: Pipe diameter
        thickness: Pipe wall thickness

    Returns:
        Series with calculated plastic collapse pressure values
    """
    return  f_y * alpha_fab * (2 * thickness/diameter)


def ovality(d_max, d_min, diameter) -> pd.Series:
    """Calculate ovality (eq (5.16))

    Args:
        d_max: Maximum diameter of the pipe
        d_min: Minimum diameter of the pipe
        diameter: Nominal diameter of the pipe

    Returns:
        Series with calculated ovality values
    """
    ovality = (d_max - d_min) / diameter
    if ovality * 100 > 5:
        raise ValueError("Ovality is exceeding 5%, which is not acceptable")
    return ovality


def characteristic_collapse_pressure(plastic_collapse_pressure, elastic_collapse_pressure, ovality, diameter, thickness) -> pd.Series:
    """Calculate characteristic collapse pressure (eq (5.13))

    Args:
        plastic_collapse_pressure: Plastic collapse pressure
        elastic_collapse_pressure: Elastic collapse pressure
        ovality: Ovality of the pipe

    Returns:
        Series with calculated characteristic collapse pressure values
    """
    p_c = characteristic_collapse_pressure
    p_p = plastic_collapse_pressure
    p_e = elastic_collapse_pressure
    o = ovality
    d = diameter
    t = thickness

    expression = (p_c - p_e) * (p_c**2 - p_p**2) + ...
    sympy.solve(p_c * p_)
    return min(plastic_collapse_pressure, elastic_collapse_pressure * (1 - 10 * ovality))