import pandas as pd
import os
import re



def read_in_csv_results(in_csv):
    return pd.read_csv(
        in_csv,
        header=2,
        skiprows=[3, 4],
        sep=';',
    )

def read_in_summarized_csv_results(in_csv):
    return pd.read_csv(
        in_csv,
        header=0,
        # skiprows=[3, 4],
        sep=';',
    )

def extractInfo(simID):
    info = simID.split('_')
    extracted_info = {
        'D/t': float(re.sub(r'[^\d\.]', '', info[0])),
        'Qh': float(re.sub(r'[^\d\.]', '', info[1])),
        'YS': float(re.sub(r'[^\d\.]', '', info[2])),
        'TS': float(re.sub(r'[^\d\.]', '', info[3])),
        'WT': float(re.sub(r'[^\d\.]', '', info[4])),
        'lf': float(re.sub(r'[^\d\.]', '', info[5])),
        'af': float(re.sub(r'[^\d\.]', '', info[6])),
    }
    return extracted_info

def extract_info_from_name(file_name):
    try:
        if '_Main_shellResTime.csv' in file_name:
            simId = os.path.basename(file_name).rstrip('_Main_shellResTime.csv').lstrip('processed_')
            isRestart = False
        elif '_Restart_shellTrawlingRes.csv' in file_name:
            simId = os.path.basename(file_name).rstrip('_Restart_shellTrawlingRes.csv').lstrip('processed_')
            restartId, simId = simId.split('-')
            isRestart = True
        else:
            print(f"File {file_name} does not match expected naming convention. Skipping.")

        return simId, isRestart
    except Exception as e:
        print(f"Error processing {file_name}: {e}")

def write_to_csv(out_csv, df, sep=';', mode='x'):
    try:
        df.to_csv(out_csv, index=False, sep=sep, mode=mode)
        print("File written successfully")

    except FileExistsError:
        input('The csv file already exists. Press enter to confirm overwrite. (ctrl + c to exit script)')
        write_to_csv(out_csv, df, sep=sep, mode='w')

    except EnvironmentError:
        input('The csv file is open, please close it and press enter. (ctrl + c to exit script)')
        write_to_csv(out_csv, df, sep=sep, mode=mode)


def write_csv_preserve_skipped_rows(in_csv, out_csv, df, header_row=2, skiprows=(3, 4), sep=';', new_col_info=None):
    with open(in_csv, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    original_cols = len(lines[header_row].split(sep))
    new_cols = len(df.columns)
    extra = new_cols - original_cols

    prefix = lines[:header_row]
    skipped = []
    for idx, i in enumerate(skiprows):
        if i < len(lines):
            line = lines[i].rstrip('\n').rstrip('\r')
            if new_col_info and extra > 0:
                line += sep + new_col_info[idx]
            skipped.append(line + '\n')

    with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(prefix)
        f.write(sep.join(map(str, df.columns)) + '\n')
        f.writelines(skipped)
        df.to_csv(f, index=False, sep=sep, header=False, lineterminator='\n')


