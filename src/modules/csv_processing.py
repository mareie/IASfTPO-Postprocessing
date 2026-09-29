import pandas as pd

from modules.pipe import Pipe
from modules.plotting import plot_csv_data, plot_path_csv_data
from modules.process_time_history import process_time_csv_file
from utils.utils import extract_general_info_from_file_name

# Pipe configuration data
PIPE_INFO = {
    17.2: {"OD": 273.1, "WT": 15.88, "YS": 450, "TS": 535},
    32: {"OD": 0.9144, "WT": 28.6, "YS": 480, "TS": 550},
    15.1: {"OD": 0.2032, "WT": 13.5, "YS": 480, "TS": 550},
}


def process_time_csv_files(list_of_csvs) -> pd.DataFrame:
    """Processes a list of CSV data objects and generates a summary DataFrame and plots."""
    summary_df = pd.DataFrame()

    for csv_data in list_of_csvs:
        csv_data = prepare_csv_data_object(csv_data)
        processed_df = process_time_csv_file(csv_data)
        summary_df = pd.concat([summary_df, processed_df])

    if False:  # Replace with an actual condition if needed
        plot_csv_data(list_of_csvs)
    return summary_df


def process_path_csv_files(list_of_csvs) -> pd.DataFrame:
    """Processes a list of CSV data objects and generates a summary DataFrame and plots."""
    summary_df = pd.DataFrame()

    for csv_data in list_of_csvs:
        general_info = extract_general_info_from_file_name(csv_data)
        csv_data.add_general_info(**general_info)
        plot_path_csv_data(csv_data)
        # processed_df = process_csv_file(csv_data)
        # summary_df = pd.concat([summary_df, processed_df])

    return summary_df


def prepare_csv_data_object(csv_data):
    general_info = extract_general_info_from_file_name(csv_data)
    general_info.update(add_pipe_properties_based_on_dt_ratio(general_info["D/t"]))
    csv_data.add_general_info(**general_info)
    pipe = Pipe(
        outer_diameter=csv_data.general_info["OD"] / 1000,
        wall_thickness=csv_data.general_info["WT"] / 1000,
        yield_strength=csv_data.general_info["YS"] * 1e6,
        tensile_strength=csv_data.general_info["TS"] * 1e6,
        ys_ts=csv_data.general_info["YS"] / csv_data.general_info["TS"],
        d_over_t=csv_data.general_info["D/t"],
        qh=csv_data.general_info["Qh"],
    )
    pipe.calculate_capacity_parameters_STF101()
    csv_data.attach_pipe(pipe)
    return csv_data


def add_pipe_properties_based_on_dt_ratio(dt_ratio: float) -> dict:
    for ratio, properties in PIPE_INFO.items():
        if dt_ratio == ratio:
            return {
                "OD": properties["OD"],
                "WT": properties["WT"],
                "YS": properties["YS"],
                "TS": properties["TS"],
            }
    return {}
