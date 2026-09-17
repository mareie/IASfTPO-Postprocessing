import re


def extract_info(simID: str) -> dict:
    """Extracts general information from the simulation ID string.

    Args:
        simID (str): The simulation ID string from which to extract information.

    Returns:
        dict: A dictionary containing the extracted information.
    """
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


def add_general_info_from_file_name(csv_data):
    """Adds general information extracted from the file name to the CSV data object.

    Args:
        csv_data: The CSV data object to which the general information will be added.
    """
    clean_file_name = csv_data.filepath.name.rsplit("_Main")[0]
    general_info = extract_info(clean_file_name)
    general_info["Sim ID"] = clean_file_name
    csv_data.add_general_info(**general_info)