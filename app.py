import io
from pathlib import Path

import pandas as pd
import streamlit as st
from py3dbp import Bin, Item, Packer

from visualization import (
    PLOTLY_CHART_CONFIG,
    box_type_key,
    color_for_key,
    draw_truck_3d_interactive,
)

# ---------------------------------------------------------------------------
# Page & styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Truck Loader",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS_PATH = Path(__file__).parent / "static" / "styles.css"
st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Presets & constants
# ---------------------------------------------------------------------------

TRUCK_PRESETS = {
    "Standard curtain-side (EU)": {"length": 1360, "width": 248, "height": 270},
    "Medium box truck": {"length": 480, "width": 220, "height": 220},
    "Small delivery van": {"length": 240, "width": 160, "height": 140},
    "Custom": None,
}

CARGO_PRESETS = {
    "Demo — mixed pallets & boxes": (
        "120,100,80,2\n"
        "110,90,70,3\n"
        "100,100,100,2\n"
        "80,80,80,4\n"
        "60,50,40,6"
    ),
    "Uniform euro pallets": "120,80,144,8",
    "Retail cartons": "40,30,30,20\n60,40,35,10\n50,50,50,5",
}

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def parse_boxes(data: str) -> tuple[list[dict], list[str]]:
    boxes = []
    errors = []
    for line in data.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 4:
                raise ValueError("expected 4 values")
            length, width, height, count = map(int, parts)
            if min(length, width, height, count) < 1:
                raise ValueError("dimensions and count must be positive")
            boxes.append({"length": length, "width": width, "height": height, "count": count})
        except (ValueError, TypeError):
            errors.append(line)
    return boxes, errors


def _as_float(value) -> float:
    return float(value)


def optimize_with_py3dbp(truck: dict, boxes: list[dict]) -> list[dict]:
    packer = Packer()
    packer.add_bin(Bin("Truck", truck["length"], truck["width"], truck["height"], 100_000))

    for box in boxes:
        label = box_type_key(box)
        for i in range(box["count"]):
            packer.add_item(
                Item(f"{label}_{i}", box["length"], box["width"], box["height"], 1)
            )

    packer.pack()

    placed = []
    for b in packer.bins:
        for item in b.items:
            placed.append({
                "x": _as_float(item.position[0]),
                "y": _as_float(item.position[1]),
                "z": _as_float(item.position[2]),
                "length": _as_float(item.width),
                "width": _as_float(item.height),
                "height": _as_float(item.depth),
                "type": item.name.rsplit("_", 1)[0],
            })
    return placed


def compute_stats(truck: dict, boxes: list[dict], placed: list[dict]) -> dict:
    truck_vol = truck["length"] * truck["width"] * truck["height"]
    cargo_vol = sum(b["length"] * b["width"] * b["height"] * b["count"] for b in boxes)
    placed_vol = sum(b["length"] * b["width"] * b["height"] for b in placed)
    total_items = sum(b["count"] for b in boxes)
    unique_types = len({box_type_key(b) for b in boxes})

    space_util = (placed_vol / truck_vol * 100) if truck_vol else 0.0
    packing_eff = (placed_vol / cargo_vol * 100) if cargo_vol else 0.0

    return {
        "truck_volume": truck_vol,
        "cargo_volume": cargo_vol,
        "placed_volume": placed_vol,
        "space_utilization": _as_float(space_util),
        "packing_efficiency": _as_float(packing_eff),
        "placed_count": len(placed),
        "total_count": total_items,
        "unplaced_count": total_items - len(placed),
        "unique_types": unique_types,
    }


def placed_boxes_dataframe(placed: list[dict]) -> pd.DataFrame:
    rows = []
    for i, b in enumerate(placed, 1):
        rows.append({
            "#": i,
            "Type": b.get("type", "—"),
            "X (cm)": b["x"],
            "Y (cm)": b["y"],
            "Z (cm)": b["z"],
            "L (cm)": b["length"],
            "W (cm)": b["width"],
            "H (cm)": b["height"],
            "Volume (cm³)": b["length"] * b["width"] * b["height"],
        })
    return pd.DataFrame(rows)


def cargo_summary_dataframe(boxes: list[dict]) -> pd.DataFrame:
    rows = []
    for b in boxes:
        vol = b["length"] * b["width"] * b["height"]
        rows.append({
            "Dimensions (L×W×H)": box_type_key(b),
            "Qty": b["count"],
            "Unit vol. (m³)": round(vol / 1_000_000, 3),
            "Total vol. (m³)": round(vol * b["count"] / 1_000_000, 3),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Configuration")
    st.caption("Set truck size and cargo list, then run optimization.")

    if "truck_l" not in st.session_state:
        default = TRUCK_PRESETS["Standard curtain-side (EU)"]
        st.session_state.truck_l = default["length"]
        st.session_state.truck_w = default["width"]
        st.session_state.truck_h = default["height"]
        st.session_state.last_truck_preset = "Standard curtain-side (EU)"

    preset_name = st.selectbox("Truck template", list(TRUCK_PRESETS.keys()), index=0)
    preset = TRUCK_PRESETS[preset_name]
    if preset and preset_name != st.session_state.last_truck_preset:
        st.session_state.truck_l = preset["length"]
        st.session_state.truck_w = preset["width"]
        st.session_state.truck_h = preset["height"]
        st.session_state.last_truck_preset = preset_name
    elif not preset:
        st.session_state.last_truck_preset = "Custom"

    st.markdown("**Truck dimensions (cm)**")
    c1, c2, c3 = st.columns(3)
    truck_length = c1.number_input("Length", min_value=1, key="truck_l")
    truck_width = c2.number_input("Width", min_value=1, key="truck_w")
    truck_height = c3.number_input("Height", min_value=1, key="truck_h")

    truck_vol_m3 = truck_length * truck_width * truck_height / 1_000_000
    st.info(f"Cargo space: **{truck_vol_m3:.2f} m³**")

    st.divider()

    if "cargo_text" not in st.session_state:
        st.session_state.cargo_text = CARGO_PRESETS["Demo — mixed pallets & boxes"]
    if "last_cargo_preset" not in st.session_state:
        st.session_state.last_cargo_preset = "Demo — mixed pallets & boxes"

    cargo_preset = st.selectbox("Cargo preset", ["Custom"] + list(CARGO_PRESETS.keys()), index=1)
    if cargo_preset != "Custom" and cargo_preset != st.session_state.last_cargo_preset:
        st.session_state.cargo_text = CARGO_PRESETS[cargo_preset]
        st.session_state.last_cargo_preset = cargo_preset
    elif cargo_preset == "Custom":
        st.session_state.last_cargo_preset = "Custom"

    st.markdown("**Cargo list**")
    st.caption("One line per type: `length,width,height,quantity`")
    box_data = st.text_area(
        "Cargo input",
        key="cargo_text",
        height=180,
        label_visibility="collapsed",
        placeholder="120,100,80,2",
    )

    optimize = st.button("Optimize loading", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🚛 Truck Loader</h1>
        <p>Plan cargo placement with 3D bin packing — maximize space, minimize guesswork.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

boxes, parse_errors = parse_boxes(box_data)

if parse_errors:
    st.error(f"Could not parse {len(parse_errors)} line(s). Use format: length,width,height,count")
    with st.expander("Show invalid lines"):
        for line in parse_errors:
            st.code(line)

if not optimize:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            '<div class="metric-card"><div class="label">Truck</div>'
            f'<div class="value">{truck_length}×{truck_width}×{truck_height}</div>'
            '<div class="sub">cm (L × W × H)</div></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        total_items = sum(b["count"] for b in boxes)
        st.markdown(
            '<div class="metric-card"><div class="label">Cargo items</div>'
            f'<div class="value">{total_items}</div>'
            f'<div class="sub">{len(boxes)} type(s) defined</div></div>',
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            '<div class="metric-card"><div class="label">Status</div>'
            '<div class="value">Ready</div><div class="sub">Click Optimize in the sidebar</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">📦</div>
            <strong>Configure your load and click <em>Optimize loading</em></strong><br>
            <span style="font-size:0.9rem;">Use presets for a quick demo, or enter your own truck and cargo data.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if boxes:
        st.subheader("Cargo summary")
        st.dataframe(cargo_summary_dataframe(boxes), use_container_width=True, hide_index=True)

else:
    if not boxes:
        st.warning("Add at least one valid cargo line before optimizing.")
        st.stop()

    truck = {"length": truck_length, "width": truck_width, "height": truck_height}
    placed_boxes = optimize_with_py3dbp(truck, boxes)
    stats = compute_stats(truck, boxes, placed_boxes)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Items placed", f"{stats['placed_count']} / {stats['total_count']}")
    k2.metric("Space utilization", f"{stats['space_utilization']:.1f}%", help="Placed volume ÷ truck volume")
    k3.metric("Packing rate", f"{stats['packing_efficiency']:.1f}%", help="Placed volume ÷ total cargo volume")
    k4.metric("Unplaced", stats["unplaced_count"], delta=None if stats["unplaced_count"] == 0 else f"-{stats['unplaced_count']}")

    if stats["unplaced_count"] > 0:
        st.warning(
            f"**{stats['unplaced_count']}** item(s) could not fit. "
            "Try a larger truck, fewer items, or smaller box types."
        )
    else:
        st.success("All cargo items were placed successfully.")

    fill_pct = min(stats["space_utilization"], 100.0)
    st.progress(int(fill_pct), text=f"Truck fill: {stats['space_utilization']:.1f}%")

    tab_viz, tab_cargo, tab_details = st.tabs(["3D visualization", "Cargo overview", "Placement details"])

    with tab_viz:
        fig = draw_truck_3d_interactive(truck, placed_boxes)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=PLOTLY_CHART_CONFIG,
        )
        st.caption(
            "Floor stays level — drag to orbit · scroll to zoom · double-click to reset · "
            "origin (0,0,0) = front-left corner"
        )

        legend_cols = st.columns(min(len(boxes), 5) or 1)
        seen = set()
        col_idx = 0
        for b in boxes:
            key = box_type_key(b)
            if key in seen:
                continue
            seen.add(key)
            with legend_cols[col_idx % len(legend_cols)]:
                st.markdown(
                    f'<div class="viz-legend">'
                    f'<span style="display:inline-block;width:14px;height:14px;background:{color_for_key(key)};'
                    f'border-radius:3px;margin-right:6px;vertical-align:middle;"></span>'
                    f'<span style="vertical-align:middle;">{key} cm</span></div>',
                    unsafe_allow_html=True,
                )
            col_idx += 1

    with tab_cargo:
        st.dataframe(cargo_summary_dataframe(boxes), use_container_width=True, hide_index=True)

    with tab_details:
        df = placed_boxes_dataframe(placed_boxes)
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            "Download placement CSV",
            data=csv_buf.getvalue(),
            file_name="truck_load_plan.csv",
            mime="text/csv",
        )

st.divider()
st.caption("Truck Loader · 3D bin packing powered by py3dbp · Built for logistics planning demos")
