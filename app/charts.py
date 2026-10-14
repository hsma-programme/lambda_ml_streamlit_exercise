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
        height=520,
        margin=dict(l=0, r=0, t=40 if title else 10, b=0),
        xaxis=dict(visible=False, range=[-1, _COLS]),
        yaxis=dict(visible=False, scaleanchor="x", range=[-25, 1]),
        legend=dict(orientation="v", yanchor="top", y=-0.02, x=0),
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


def friday_bars(friday: dict) -> go.Figure:
    """Readmission rate, Friday vs other days: all patients, then within elderly care / other wards."""
    groups = [
        ("All patients", friday["friday"]["rate"], friday["other_days"]["rate"]),
        ("Elderly care wards", friday["elderly_care"]["friday"]["rate"], friday["elderly_care"]["other_days"]["rate"]),
        ("All other wards", friday["other_wards"]["friday"]["rate"], friday["other_wards"]["other_days"]["rate"]),
    ]
    names = [g[0] for g in groups]
    fig = go.Figure()
    for label, idx, colour in (("Discharged on a Friday", 1, "#2a78d6"), ("Discharged on another day", 2, "#eb6834")):
        vals = [g[idx] * 100 for g in groups]
        fig.add_trace(
            go.Bar(
                x=names,
                y=vals,
                name=label,
                marker_color=colour,
                text=[f"{v:.1f}%" for v in vals],
                textposition="outside",
                hovertemplate="%{x}, " + label.lower() + ": %{y:.1f}%<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="group",
        height=360,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(title="Readmitted within 30 days (%)", rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Lexend, sans-serif", color=NAVY),
        bargap=0.35,
    )
    return fig


def waterfall(expl: dict) -> go.Figure:
    """SHAP waterfall in percentage points. Red pushes towards readmission, blue away."""
    steps = list(expl["shown"])
    if expl["other"]:
        steps.append(expl["other"])
    labels = ["Average patient"] + [s["label"] for s in steps] + ["This patient"]
    values = [expl["base"]] + [s["value"] for s in steps] + [expl["fx"]]
    measure = ["absolute"] + ["relative"] * len(steps) + ["total"]
    texts = [f"{expl['base']:.1f}%"] + [f"{s['value']:+.1f}" for s in steps] + [f"{expl['fx']:.1f}%"]
    fig = go.Figure(
        go.Waterfall(
            orientation="h",
            y=labels,
            x=values,
            measure=measure,
            text=texts,
            textposition="outside",
            increasing=dict(marker=dict(color="#c0392b")),
            decreasing=dict(marker=dict(color="#2a78d6")),
            totals=dict(marker=dict(color=NAVY)),
            connector=dict(line=dict(color="#8a95a5", width=1)),
            hovertemplate="%{y}: %{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=120 + 38 * len(labels),
        margin=dict(l=0, r=40, t=10, b=40),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(title="Predicted risk of readmission (%). Red raises it, blue lowers it. Changes in percentage points."),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Lexend, sans-serif", color=NAVY),
        showlegend=False,
    )
    return fig
