import pandas as pd



class CsvData:
    def __init__(self, filepath, sep=';'):
        self.sep = sep

        self._top_rows = pd.read_csv(
            filepath,
            header=None,
            sep=sep,
            encoding='utf-8-sig',
            nrows=5,
            low_memory=False
        )

        self.sim_info_df = self._create_siminfo_dataframe(self._top_rows)
        self.metadata = self._create_metadata_dataframe(self._top_rows)

        self.df = pd.read_csv(
            filepath,
            header=2,
            skiprows=[3, 4],
            sep=sep,
            encoding='utf-8-sig',
            low_memory=False,
        )

    def _create_siminfo_dataframe(self, top_rows):
        sim_info_df = top_rows.iloc[1:2].copy()
        sim_info_df.columns = top_rows.iloc[0]
        sim_info_df.reset_index(drop=True, inplace=True)
        sim_info_df = sim_info_df.dropna(axis=1)
        return sim_info_df

    def _create_metadata_dataframe(self, top_rows):
        meta_df = top_rows.iloc[3:5].copy()  # Rows 3-4
        meta_df.columns = top_rows.iloc[2]  # Set column names from row 3
        meta_dict = {
            col: {'info': meta_df[col].iloc[0], 'description': meta_df[col].iloc[1]}
            for col in meta_df.columns
        }
        return meta_dict

    def save_to_csv(self, output_path):
        def _to_text(value):
            return '' if pd.isna(value) else str(value)

        def _trim_trailing_nan(values):
            trimmed = list(values)
            while trimmed and pd.isna(trimmed[-1]):
                trimmed.pop()
            return trimmed

        sim_header = _trim_trailing_nan(self._top_rows.iloc[0].tolist())
        sim_values = _trim_trailing_nan(self._top_rows.iloc[1].tolist())

        current_columns = list(self.df.columns)
        metadata_info = [self.metadata.get(col, {}).get('info', '') for col in current_columns]
        metadata_description = [self.metadata.get(col, {}).get('description', '') for col in current_columns]

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(self.sep.join(_to_text(v) for v in sim_header) + '\n')
            f.write(self.sep.join(_to_text(v) for v in sim_values) + '\n')
            f.write(self.sep.join(_to_text(v) for v in current_columns) + '\n')
            f.write(self.sep.join(_to_text(v) for v in metadata_info) + '\n')
            f.write(self.sep.join(_to_text(v) for v in metadata_description) + '\n')
            self.df.to_csv(f, index=False, sep=self.sep, header=False, lineterminator='\n')

    def __repr__(self):
        return f"CsvData(metadata={self.metadata}, df_shape={self.df.shape})"
    def __str__(self):
        return f"CsvData with {len(self.df)} rows and {len(self.df.columns)} columns. Metadata keys: {list(self.metadata.keys())}"