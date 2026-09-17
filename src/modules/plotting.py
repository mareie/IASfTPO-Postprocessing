import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots


def plot_csv_data(list_of_csvs):


    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.08)
    colors = qualitative.G10
    color_map = {}

    for csv_data in list_of_csvs:
        simulation_name = csv_data.general_info["Sim ID"]
        step = csv_data.df[csv_data.df["Step name"] == "Trawl"]

        if simulation_name not in color_map:
            color_map[simulation_name] = colors[len(color_map) % len(colors)]

        plot_results(fig, step["Displacement"], step["End1 RF1 Force"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color_map[simulation_name], row=1, col=1)
        plot_results(fig, step["Wire force"], step["Moment"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color_map[simulation_name], row=2, col=1)
        plot_results(fig, step["ESF1"], step["Moment"], csv_data.metadata, csv_data.header_info, csv_data.peak_index, color_map[simulation_name], row=3, col=1)

    fig.update_layout(height=1600, width=1600)
    fig.show()


def plot_results(fig, x, y, md, header_info, peaks, color, row=None, col=None):

    trace_name = f"{header_info['ODB name'].rsplit('_Main')[0]}"
    trace = go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name=trace_name,
        line={"color": color},
        legendgroup=trace_name,
        hovertemplate=f"x: %{{x}}<br>y: %{{y}}<extra>{trace_name}</extra>",
        showlegend=row is None or row == 1,
    )
    if row is None or col is None:
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)

    peak_trace = go.Scatter(
        x=x.iloc[peaks],
        y=y.iloc[peaks],
        # mode="markers+text",
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
