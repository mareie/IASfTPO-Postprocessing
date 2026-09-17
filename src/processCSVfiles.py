"""
Post-processing script for summarizing results from processed trawling analysis.
Reads in all CSV files in a specified folder, processes the data, and generates a summary CSV file.
The script performs the following steps:
1. Reads in CSV files containing time history data for trawling simulations.
2. Extracts relevant information from the file names and CSV content, including simulation parameters and time history data.
"""
import datetime
import os

from modules.csv_data import CsvData
from modules.csv_processing import process_csv_files
from utils.readAndWrite import (
    check_input_and_get_files,
    get_input_from_args_or_dialog,
    write_to_csv,
)

debug = False


def main(input_path_or_files):
    outName = datetime.datetime.now().strftime("%Y-%m-%d") + "_summary_Mmax" ".csv"

    filtered_files = check_input_and_get_files(input_path_or_files, outName)
    list_of_csvs = [CsvData.from_file(file) for file in filtered_files]

    out_df = process_csv_files(list_of_csvs)


    current_folder = os.getcwd()
    out_csv = os.path.join(current_folder,'output', outName)
    out_df = out_df.sort_values(by=['D/t', 'Qh', 'Ls', 'Lr'])
    write_to_csv(out_csv, out_df)

    print("Done")



if __name__ == "__main__":
    default_folder = r"\\osl5207.verit.dnv.com\beegfs-hpc_lagu_rp_osl\sign\mareie\IAS\CSV"
    selected_input = get_input_from_args_or_dialog(default_folder)

    if not selected_input:
        print("No input selected. Exiting.")
    else:
        main(selected_input)
