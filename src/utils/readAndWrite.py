import sys
import os
import tkinter as tk
from tkinter import filedialog

def get_input_from_args_or_dialog(default_folder):
    if len(sys.argv) > 1:
        arg_paths = [os.path.abspath(p) for p in sys.argv[1:]]
        if len(arg_paths) == 1 and os.path.isdir(arg_paths[0]):
            return arg_paths[0]

        selected_files = []
        for path in arg_paths:
            if os.path.isdir(path):
                selected_files.extend(
                    [
                        os.path.join(path, f)
                        for f in os.listdir(path)
                    ]
                )
            elif os.path.isfile(path):
                selected_files.append(path)

        return selected_files

    user_input = input(
        'Select input type: [d] folder (default), [f] files, [n] use default folder. '
        'Press enter for folder selection. (ctrl + c to exit script) '
    ).strip().lower()

    if user_input == 'n':
        return default_folder

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    root.after(10, lambda: root.focus_force())

    if user_input == 'f':
        selected_files = list(
            filedialog.askopenfilenames(
                title="Select CSV file(s)",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        )
        root.destroy()
        return selected_files

    selected_folder = filedialog.askdirectory(title="Select CSV folder")
    root.destroy()
    return selected_folder


def check_input_and_get_files(input_path_or_files, outName):
    """
    Check if the input is a folder or a list of files. If it's a folder,
    filter the files based on the exclusion and inclusion criteria. If it's a list of files, return them directly.
    """
    if isinstance(input_path_or_files, (list, tuple)):
        filtered_files = list(input_path_or_files)
        if not filtered_files:
            print("No CSV files selected.")
            return
        folder = os.path.dirname(filtered_files[0])
        print(f"Processing {len(filtered_files)} selected CSV file(s).")
    else:
        folder = input_path_or_files
        print("Processing CSV files in folder:", folder)

        exclusion_files = [outName, 'summary.csv', 'processed.csv']  # Exclude the output file and any already processed files
        inclusion_files = [".csv"]# e.g. "beamTrawlingRes" to only include files with this string in the name
        filtered_files = filter_files(folder, exclusion_files, inclusion_files)

    if not filtered_files:
        print("No matching CSV files found.")
        return

    return filtered_files

def filter_files(folder, exclusion_files, inclusion_files=None):
    return [os.path.join(folder, file) for file in os.listdir(folder) if file not in exclusion_files and (inclusion_files is None or any(inc in file for inc in inclusion_files))]