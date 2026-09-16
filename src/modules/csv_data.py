from pathlib import Path

import pandas as pd


class CsvData:
    def __init__(self, df, filename=None, metadata=None, header_info=None, general_info=None):
        self.df = df
        self.filename = filename
        self.metadata = metadata
        self.header_info = header_info
        self.general_info = general_info or {}

    @classmethod
    def from_file(cls, filepath, sep=";", headers=True):
        filename = Path(filepath).name
        if not headers:
            df = cls._read_data_no_headers(filepath, sep=sep)
            metadata = {}
            header_info = {}
            return cls(df=df, filename=filename, metadata=metadata, header_info=header_info)

        header_info = cls._read_header_info(filepath, sep=sep)
        metadata = cls._read_metadata(filepath, sep=sep)
        df = cls._read_data(filepath, sep=sep)

        return cls(df=df, filename=filename, metadata=metadata, header_info=header_info, general_info={})

    @staticmethod
    def _read_header_info(filepath, sep=";"):
        header_info_df = CsvData._read_csv(filepath, sep=sep, header=0, nrows=1)
        row = header_info_df.iloc[0]
        return {str(col): row[col] for col in header_info_df.columns}

    @staticmethod
    def _read_metadata(filepath, sep=";"):
        metadata_df = CsvData._read_csv(filepath, sep=sep, header=2, nrows=2)
        return {
            str(col): {
                "info": metadata_df[col].iloc[0],
                "description": metadata_df[col].iloc[1],
            }
            for col in metadata_df.columns
        }

    @staticmethod
    def _read_data(filepath, sep=";"):
        return CsvData._read_csv(filepath, sep=sep, header=2, skiprows=[3, 4])

    @staticmethod
    def _read_data_no_headers(filepath, sep=";"):
        return CsvData._read_csv(filepath, sep=sep, header=0)

    @staticmethod
    def _read_csv(filepath, sep=";", **kwargs):
        return pd.read_csv(
            filepath,
            sep=sep,
            encoding="utf-8-sig",
            **kwargs,
        )

    def get_column_metadata(self, column_name):
        return self.metadata[column_name]

    def add_general_info(self, **kwargs):
        self.general_info.update(kwargs)

    def set_general_info(self, info_dict):
        self.general_info = dict(info_dict)

    def add_column(self, name, values, info="", description=""):
        self.df[name] = values
        self.metadata[name] = {
            "info": info,
            "description": description,
        }

    def save_to_csv(self, output_path, sep=";"):
        cols = list(self.df.columns)

        sim_header = list(self.header_info.keys())
        sim_values = [self.header_info[k] for k in sim_header]

        info_row = [self.metadata.get(c, {}).get("info", "") for c in cols]
        desc_row = [self.metadata.get(c, {}).get("description", "") for c in cols]

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(sep.join(map(str, sim_header)) + "\n")
            f.write(sep.join(map(str, sim_values)) + "\n")
            f.write(sep.join(map(str, cols)) + "\n")
            f.write(sep.join(map(str, info_row)) + "\n")
            f.write(sep.join(map(str, desc_row)) + "\n")
            self.df.to_csv(
                f, index=False, header=False, sep=sep, lineterminator="\n"
            )
