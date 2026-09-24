import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots


def plot_csv_data(list_of_csvs):


    fig = make_subplots(rows=3, cols=3, vertical_spacing=0.08)
    colors = qualitative.G10
    color_map = {}

    for csv_data in list_of_csvs:
        if csv_data.general_info['D/t'] == 22.6:
            continue
        simulation_name = csv_data.general_info["Sim ID"]
        step = csv_data.df[csv_data.df["Step name"] == "Trawl"]
        peaks = csv_data.peak_index
        if peaks.size != 0:
            end_index = min(int(peaks[-1]) + 40, len(step))
            step = step.iloc[:end_index]
            peaks = peaks[peaks < len(step)]
        if simulation_name not in color_map:
            color_map[simulation_name] = colors[len(color_map) % len(colors)]

        plot_results(fig, step["Displacement"], step["Moment"], csv_data.metadata, csv_data.header_info, peaks, color_map[simulation_name], row=1, col=1)
        plot_results(fig, step["Displacement"], step["End1 RF1 Force"], csv_data.metadata, csv_data.header_info, peaks, color_map[simulation_name], row=2, col=1)
        plot_results(fig, step["ESF1"], step["Moment"], csv_data.metadata, csv_data.header_info, peaks, color_map[simulation_name], row=1, col=2)
        plot_results(fig, step["Wire force"], step["Moment"], csv_data.metadata, csv_data.header_info, peaks, color_map[simulation_name], row=1, col=3)
        plot_results(fig, step["Wire force"], step["Max ovalization in sections"], csv_data.metadata, csv_data.header_info, peaks, color_map[simulation_name], row=2, col=3)

    fig.update_layout(height=1600, width=1800)
    fig.show()


def plot_results(fig, x, y, md, header_info, peaks, color, row=None, col=None):

    trace_name = f"{header_info['ODB name'].rsplit('_Main')[0]}"
    showlegend = not any(
        trace.legendgroup == trace_name and trace.showlegend for trace in fig.data
    )
    trace = go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name=trace_name,
        line={"color": color},
        legendgroup=trace_name,
        hovertemplate=f"x: %{{x}}<br>y: %{{y}}<extra>{trace_name}</extra>",
        showlegend=showlegend,
    )
    if row is None or col is None:
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)

    peak_trace = go.Scatter(
        x=x.iloc[peaks],
        y=y.iloc[peaks],
        mode="markers",
        marker={"color": "red"},
        # text=[f"y: {y.iloc[peak]:.0f}" for peak in peaks],
        # textposition="top center",
        name="Peaks",
        hovertemplate=f"x: %{{x}}<br>y: %{{y}}<extra>{trace_name}</extra>",
        legendgroup=trace_name,
        showlegend=False,
    )
    if row is None or col is None:
        fig.add_trace(peak_trace)
        fig.update_layout(
            xaxis_title=f'{md[x.name]["description"]}',
            yaxis_title=f'{md[y.name]["description"]}',
            title=f"{x.name} vs {y.name}",
        )
    else:
        fig.add_trace(peak_trace, row=row, col=col)
        fig.update_xaxes(title_text=f'{md[x.name]["description"]}', row=row, col=col)
        fig.update_yaxes(title_text=f'{md[y.name]["description"]}', row=row, col=col)
