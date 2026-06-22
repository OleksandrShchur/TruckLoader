"""3D truck cargo visualization — geometry at origin, turntable camera on floor."""

from __future__ import annotations

import hashlib

import plotly.graph_objects as go

PALETTE = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
]

_BOX_I = [0, 1, 1, 2, 2, 6, 0, 3, 4, 6, 0, 0]
_BOX_J = [1, 2, 2, 6, 3, 3, 3, 7, 7, 4, 1, 5]
_BOX_K = [3, 3, 5, 5, 6, 7, 4, 4, 6, 5, 5, 4]

# Geometry anchor — front-left floor corner.
_ORIGIN = dict(x=0, y=0, z=0)
# Camera turntable pivot — centre of the floor (floor stays level, spins like a lazy Susan).
_FLOOR_PIVOT = dict(x=0.5, y=0.5, z=0)
_WORLD_UP = dict(x=0, y=0, z=1)

_DEFAULT_EYE = dict(x=1.55, y=0.95, z=0.42)

PLOTLY_CHART_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "doubleClick": "reset",
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
}


def _default_camera() -> dict:
    return {
        "eye": dict(
            x=_FLOOR_PIVOT["x"] + _DEFAULT_EYE["x"] - 0.5,
            y=_FLOOR_PIVOT["y"] + _DEFAULT_EYE["y"] - 0.5,
            z=_FLOOR_PIVOT["z"] + _DEFAULT_EYE["z"],
        ),
        "center": dict(_FLOOR_PIVOT),
        "up": dict(_WORLD_UP),
    }


def box_type_key(box: dict) -> str:
    return f"{box['length']}×{box['width']}×{box['height']}"


def color_for_key(key: str) -> str:
    idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(PALETTE)
    return PALETTE[idx]


def _box_vertices(x0: float, y0: float, z0: float, dx: float, dy: float, dz: float) -> list[list[float]]:
    return [
        [x0, y0, z0], [x0 + dx, y0, z0], [x0 + dx, y0 + dy, z0], [x0, y0 + dy, z0],
        [x0, y0, z0 + dz], [x0 + dx, y0, z0 + dz], [x0 + dx, y0 + dy, z0 + dz], [x0, y0 + dy, z0 + dz],
    ]


def _add_box_mesh(
    fig: go.Figure,
    x0: float, y0: float, z0: float,
    dx: float, dy: float, dz: float,
    color: str,
    opacity: float,
    hovertemplate: str | None = None,
) -> None:
    vertices = _box_vertices(x0, y0, z0, dx, dy, dz)
    x, y, z = zip(*vertices)
    kwargs: dict = dict(
        x=x, y=y, z=z, i=_BOX_I, j=_BOX_J, k=_BOX_K,
        color=color,
        opacity=opacity,
        flatshading=True,
        lighting=dict(ambient=0.8, diffuse=0.9, specular=0.15, roughness=0.85),
        showlegend=False,
    )
    if hovertemplate:
        kwargs["hovertemplate"] = hovertemplate
    else:
        kwargs["hoverinfo"] = "skip"
    fig.add_trace(go.Mesh3d(**kwargs))


def _edge_lines(
    fig: go.Figure,
    edges: list[tuple[list[float], list[float], list[float]]],
    color: str,
    width: int = 4,
) -> None:
    for ex, ey, ez in edges:
        fig.add_trace(go.Scatter3d(
            x=ex, y=ey, z=ez, mode="lines",
            line=dict(color=color, width=width),
            hoverinfo="skip", showlegend=False,
        ))


def _norm(value: float, size: float) -> float:
    return value / size if size else 0.0


def _add_origin_gizmo(fig: go.Figure) -> None:
    length = 0.16
    _edge_lines(fig, [([0, length], [0, 0], [0, 0])], "#ef4444", 5)
    _edge_lines(fig, [([0, 0], [0, length], [0, 0])], "#22c55e", 5)
    _edge_lines(fig, [([0, 0], [0, 0], [0, length])], "#2563eb", 6)
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers",
        marker=dict(size=5, color="#0f172a", symbol="circle"),
        hovertemplate="Origin (0,0,0)<br>Front · left · floor<extra></extra>",
        showlegend=False,
    ))


def _add_truck_body(fig: go.Figure) -> None:
    floor_h = 0.008
    _add_box_mesh(fig, 0, 0, 0, 1, 1, floor_h, color="#94a3b8", opacity=0.45)

    outline = [
        ([0, 1], [0, 0], [0, 0]), ([0, 1], [1, 1], [0, 0]),
        ([0, 0], [0, 1], [0, 0]), ([1, 1], [0, 1], [0, 0]),
        ([0, 1], [0, 0], [1, 1]), ([0, 1], [1, 1], [1, 1]),
        ([0, 0], [0, 1], [1, 1]), ([1, 1], [0, 1], [1, 1]),
        ([0, 0], [0, 0], [0, 1]), ([1, 1], [0, 0], [0, 1]),
        ([1, 1], [1, 1], [0, 1]), ([0, 0], [1, 1], [0, 1]),
    ]
    _edge_lines(fig, outline, "#1e3a5f", width=5)

    rear_frame = [
        ([1, 1], [0, 1], [0, 0]),
        ([1, 1], [0, 0], [0, 1]),
        ([1, 1], [1, 1], [0, 1]),
        ([1, 1], [0, 1], [1, 1]),
    ]
    _edge_lines(fig, rear_frame, "#2563eb", width=7)


def _add_cargo_box(fig: go.Figure, box: dict, truck: dict, color: str) -> None:
    L, W, H = truck["length"], truck["width"], truck["height"]
    x0, y0, z0 = box["x"], box["y"], box["z"]
    dx, dy, dz = box["length"], box["width"], box["height"]
    hover = (
        f"<b>{box.get('type', 'Box')}</b><br>"
        f"Position: ({x0:.0f}, {y0:.0f}, {z0:.0f}) cm<br>"
        f"Size: {dx:.0f} × {dy:.0f} × {dz:.0f} cm<extra></extra>"
    )
    _add_box_mesh(
        fig,
        _norm(x0, L), _norm(y0, W), _norm(z0, H),
        _norm(dx, L), _norm(dy, W), _norm(dz, H),
        color=color, opacity=0.93, hovertemplate=hover,
    )


def _axis_cm(size_cm: float, title: str) -> dict:
    ticks = [0.0, 0.25, 0.5, 0.75, 1.0]
    return dict(
        title=dict(text=title, font=dict(size=11)),
        range=[0, 1],
        tickmode="array",
        tickvals=ticks,
        ticktext=[str(int(t * size_cm)) for t in ticks],
        showbackground=True,
        backgroundcolor="rgba(248, 250, 252, 0.55)",
        gridcolor="#94a3b8",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="#64748b",
        zerolinewidth=2,
        showspikes=False,
    )


def _aspect_ratio(truck: dict) -> dict:
    L, W, H = truck["length"], truck["width"], truck["height"]
    floor = 0.38
    return dict(x=1.0, y=max(W / L, floor), z=max(H / L, floor))


def draw_truck_3d_interactive(truck: dict, placed_boxes: list[dict]) -> go.Figure:
    L, W, H = truck["length"], truck["width"], truck["height"]
    fig = go.Figure()

    _add_truck_body(fig)
    _add_origin_gizmo(fig)

    for box in placed_boxes:
        key = box.get("type", box_type_key(box))
        _add_cargo_box(fig, box, truck, color_for_key(key))

    cam = _default_camera()

    fig.update_layout(
        scene=dict(
            xaxis=_axis_cm(L, "Length (cm) — 0 = front"),
            yaxis=_axis_cm(W, "Width (cm) — 0 = left"),
            zaxis=_axis_cm(H, "Height (cm) — 0 = floor"),
            bgcolor="#e8edf3",
            aspectmode="manual",
            aspectratio=_aspect_ratio(truck),
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
            camera=cam,
            dragmode="orbit",
        ),
        margin=dict(l=0, r=0, b=0, t=45),
        height=620,
        paper_bgcolor="#ffffff",
        title=dict(
            text=f"Cargo bay {L} × {W} × {H} cm — floor fixed, turntable rotation",
            font=dict(size=14, color="#0f172a"),
            x=0.5,
            xanchor="center",
        ),
        hovermode=False,
    )
    return fig
