import re
import plotly.graph_objects as go


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
