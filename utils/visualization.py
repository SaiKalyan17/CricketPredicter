import plotly.graph_objects as go


def probability_bar(names, pa, pb):
    fig = go.Figure(go.Bar(x=[pa, pb], y=list(names), orientation="h",
                           marker_color=["#2a9d8f", "#e76f51"], text=[f"{pa:.1f}%", f"{pb:.1f}%"]))
    fig.update_layout(title="Model-derived support score (not a validated probability)",
                      xaxis=dict(range=[0, 100]), height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def category_chart(names, categories):
    cs = [c for c in categories if c["available"]]
    fig = go.Figure()
    for key, name, color in (("A", names[0], "#2a9d8f"), ("B", names[1], "#e76f51")):
        fig.add_bar(name=name, x=[c["name"] for c in cs], y=[(c[key] or 0) * 100 for c in cs],
                    marker_color=color)
    fig.update_layout(barmode="group", yaxis_title="Support ratio %", height=360,
                      margin=dict(l=10, r=10, t=30, b=10))
    return fig


def radar(names, categories):
    cs = [c for c in categories if c["available"]]
    fig = go.Figure()
    for key, name in (("A", names[0]), ("B", names[1])):
        r = [(c[key] or 0) * 100 for c in cs]
        th = [c["name"] for c in cs]
        fig.add_trace(go.Scatterpolar(r=r + r[:1], theta=th + th[:1], fill="toself", name=name))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=400)
    return fig
