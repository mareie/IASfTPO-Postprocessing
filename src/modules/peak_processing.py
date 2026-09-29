import pandas as pd


def process_peaks(df, qh, peak_indices) -> pd.DataFrame:
    LOOK_AHEAD = { 'Qh_cutoff': 0.4, 'steps_ahead_low_qh': 5, 'steps_ahead_high_qh': 20 }   # Dictionary to determine look-ahead steps based on Qh value
    if qh < LOOK_AHEAD['Qh_cutoff']:
        steps_ahead = LOOK_AHEAD['steps_ahead_low_qh']
    else:
        steps_ahead = LOOK_AHEAD['steps_ahead_high_qh']


    columns_to_exctract_at_peak = ['StepTime', 'Wire force', 'ESF1', 'Moment', 'Max ovalization in sections', 'LE.LE11', 'g_hat']

    if peak_indices.size == 0:
        print(f"No peaks found for {df['SimID'].iloc[0]}.")
        # save_file_df = df[save_columns].iloc[0:1]
        # row_at_value_of_interest = pd.concat([save_file_df], axis=1)
        # return pd.DataFrame(row_at_value_of_interest)

    peak_values_df = extract_and_rename_peaks_to_dataframe(df[columns_to_exctract_at_peak], peak_indices)

    governing_results = pd.DataFrame()
    for index, peak in enumerate(peak_indices, 1):
        if check_future_trend(df['grad(M/LE.LE11)'], peak, look_ahead=steps_ahead):
            governing_results = extract_and_rename_peaks_to_dataframe(df[columns_to_exctract_at_peak], [peak], governing=True)
            governing_results['PeakNumber'] = index
            break
        governing_results = extract_and_rename_peaks_to_dataframe(df[columns_to_exctract_at_peak], [peak], governing=True)
        governing_results['PeakNumber'] = 'None'


    row_at_value_of_interest = pd.concat([governing_results, peak_values_df], axis=1) # best to include g_hat_row before peak_values_df because peak_values_df changes in size

    return row_at_value_of_interest


def check_future_trend(df, location, look_ahead=5) -> bool:
    future_vals = df.iloc[location + 1: location + 1 + look_ahead]
    # True only if current + all next look_ahead points are < 0
    return (future_vals < 0).all()


def extract_and_rename_peaks_to_dataframe(df, peak_indices, governing=False):
    """
    Extract peak data as a single row with multiple peaks across columns.

    Returns one row per simulation with columns like: Peak1_ESF1, Peak2_ESF1, etc.
    """
    peak_name = lambda n, col: f'Peak{n}_{col}'
    gov_name = lambda _, col: f'Gov_{col}'
    name_fn = gov_name if governing else peak_name

    peaks_df = df.iloc[peak_indices].reset_index(drop=True)
    peaks_df.index += 1
    peaks_df = (
        peaks_df
        .stack()
        .to_frame()
        .T
        .pipe(lambda x: x.set_axis([name_fn(n, col) for n, col in x.columns], axis=1))
    )

    return peaks_df

