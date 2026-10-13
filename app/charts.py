"""Plotly charts. Palette checked with the dataviz skill's validator (see PROGRESS.md)."""
import plotly.graph_objects as go

from metrics import GROUPS

# Slides' green / amber / red / grey. Colour is never the only cue: each group also has
# its own marker shape, a label with its count, a hover tooltip and a table view.
# Grey is deliberately recessive (the large "nothing happens" group).
_STYLE = {
    "called_readmitted": ("#1a7f4b", "circle"),
    "called_not": ("#d37b00", "square"),
    "not_called_readmitted": ("#c0392b", "diamond"),
    "not_called_not": ("#8a95a5", "circle-open"),
}
NAVY = "#091747"
_COLS = 40


def icon_array(outcomes: dict, title: str | None = None) -> go.Figure:
    """1,000 markers (40 x 25), one per 1,000 discharges, grouped by outcome."""
    fig = go.Figure()
    start = 0
    for key, label in GROUPS:
        count = outcomes[key]
        idx = range(start, start + count)
        colour, symbol = _STYLE[key]
        fig.add_trace(
            go.Scatter(
                x=[i % _COLS for i in idx],
                y=[-(i // _COLS) for i in idx],
                mode="markers",
                name=f"{label}: {count}",
                marker=dict(color=colour, symbol=symbol, size=9, line=dict(width=1.5, color=colour)),
                hovertemplate=f"{label}<extra></extra>",
            )
        )
        start += count
    fig.update_layout(
        title=title,
        height=430,
        margin=dict(l=0, r=0, t=40 if title else 10, b=0),
        xaxis=dict(visible=False, range=[-1, _COLS]),
        yaxis=dict(visible=False, scaleanchor="x", range=[-25, 1]),
        legend=dict(orientation="h", yanchor="top", y=-0.02, x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Lexend, sans-serif", color=NAVY),
    )
    return fig


def importance_bar(importance: dict, features: dict, top: int = 10, title: str | None = None) -> go.Figure:
    """Global importance: mean absolute SHAP contribution in percentage points, one hue."""
    items = list(importance.items())[:top][::-1]
    names = [features[k]["display"] for k, _ in items]
    values = [v for _, v in items]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color=NAVY,
            text=[f"{v:.1f}" for v in values],
            textposition="outside",
            hovertemplate="%{y}: %{x:.2f} percentage points<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=60 + 34 * len(items),
        margin=dict(l=0, r=30, t=40 if title else 10, b=40),
        xaxis=dict(title="Average push on predicted risk (percentage points)", rangemode="tozero"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Lexend, sans-serif", color=NAVY),
        bargap=0.45,
    )
    return fig
