import os
import re


def extract_info(simID: str) -> dict:
    patterns = {
        "D/t": r"Dt([^_]+)",
        "Qh": r"qh([^_]+)",
        "Ls": r"ls([^_]+)",
        "Lr": r"lr([^_]+)",
    }

    extracted_info = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, simID, flags=re.IGNORECASE)

        if match is None:
            raise ValueError(f"Could not find {key} in {simID}")

        value = match.group(1)

        try:
            extracted_info[key] = float(value)
        except ValueError:
            extracted_info[key] = value

    return extracted_info




def write_to_csv(out_csv, df, sep=";", mode="x"):
    try:
        df.to_csv(out_csv, index=False, sep=sep, mode=mode)
        print("File written successfully")

    except FileExistsError:
        input(
            "The csv file already exists. Press enter to confirm overwrite. (ctrl + c to exit script)"
        )
        write_to_csv(out_csv, df, sep=sep, mode="w")

    except EnvironmentError:
        input(
            "The csv file is open, please close it and press enter. (ctrl + c to exit script)"
        )
        write_to_csv(out_csv, df, sep=sep, mode=mode)


def write_csv_preserve_skipped_rows(
    in_csv, out_csv, df, header_row=2, skiprows=(3, 4), sep=";", new_col_info=None
):
    with open(in_csv, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    original_cols = len(lines[header_row].split(sep))
    new_cols = len(df.columns)
    extra = new_cols - original_cols

    prefix = lines[:header_row]
    skipped = []
    for idx, i in enumerate(skiprows):
        if i < len(lines):
            line = lines[i].rstrip("\n").rstrip("\r")
            if new_col_info and extra > 0:
                line += sep + new_col_info[idx]
            skipped.append(line + "\n")

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(prefix)
        f.write(sep.join(map(str, df.columns)) + "\n")
        f.writelines(skipped)
        df.to_csv(f, index=False, sep=sep, header=False, lineterminator="\n")
