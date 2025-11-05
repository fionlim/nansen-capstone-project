# components/pfl_counterparty_network.py
from collections import defaultdict
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import networkx as nx

from nansen_client import NansenClient

def _short_addr(a: str) -> str:
    return a[:8] + "…" + a[-4:] if isinstance(a, str) and len(a) > 12 else str(a)

def _first_label(x):
    if isinstance(x, (list, tuple)) and len(x):
        return str(x[0])
    if isinstance(x, str) and x:
        return x
    return None

def _arrow_annotations_from_graph(G, pos, *, color_map, width_key=("w","vol"),
                                  base_dual_dir_offset=0.03, group_step=0.04, standoff_px=10):
    anns = []
    same_dir_groups = defaultdict(list)
    for u, v, data in G.edges(data=True):
        same_dir_groups[(u, v)].append(data)

    undirected_to_dirs = defaultdict(set)
    for (u, v) in same_dir_groups.keys():
        undirected_to_dirs[frozenset((u, v))].add((u, v))

    raw_vals = []
    for _, _, data in G.edges(data=True):
        val = None
        for k in width_key:
            if k in data and data[k] is not None:
                try:
                    val = float(data[k])
                except Exception:
                    val = None
                break
        raw_vals.append(val if (val is not None and np.isfinite(val)) else 1.0)

    if raw_vals:
        w = np.array(raw_vals, dtype=float)
        if len(w) > 1:
            w_min, w_max = np.percentile(w, 5), np.percentile(w, 95)
        else:
            w_min, w_max = w.min(), w.max()
    else:
        w_min, w_max = (1.0, 1.0)
    if not np.isfinite(w_min): w_min = 1.0
    if not np.isfinite(w_max): w_max = 1.0
    same_span = (w_max <= w_min + 1e-12)

    for (u, v), edge_list in same_dir_groups.items():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        dx, dy = (x1 - x0), (y1 - y0)
        L = max(np.hypot(dx, dy), 1e-9)
        px, py = (-dy / L, dx / L)

        m = len(edge_list)
        same_dir_offsets = [((i - (m - 1) / 2.0) * group_step) for i in range(m)]
        both_dirs_present = len(undirected_to_dirs[frozenset((u, v))]) > 1
        base_bias = 0.03 if (both_dirs_present and (hash((u, v)) % 2 == 0)) else (-0.03 if both_dirs_present else 0.0)

        for idx, data in enumerate(edge_list):
            color_key = data.get("direction", data.get("cat", "other"))
            edge_color = color_map.get(color_key, "#888")

            val = None
            for k in width_key:
                if k in data and data[k] is not None:
                    try:
                        val = float(data[k])
                    except Exception:
                        val = None
                    break
            if val is None or not np.isfinite(val):
                val = 1.0

            if same_span:
                width_px = 2.0
            else:
                val_clamped = float(np.clip(val, w_min, w_max))
                width_px = float(np.interp(val_clamped, [w_min, w_max], [1.0, 5.0]))
            width_px = max(0.1, width_px)

            off = same_dir_offsets[idx] + base_bias
            sx, sy = x0 + px * off, y0 + py * off
            tx, ty = x1 + px * off, y1 + py * off

            anns.append(dict(
                x=tx, y=ty, xref="x", yref="y",
                ax=sx, ay=sy, axref="x", ayref="y",
                showarrow=True,
                arrowhead=3, arrowsize=1,
                arrowwidth=width_px, arrowcolor=edge_color,
                standoff=standoff_px,
            ))
    return anns

def render_counterparty_network(client: NansenClient, address: str, chain_all: str, from_iso: str, to_iso: str):
    st.subheader("Top 10 Counterparties network")
    st.text("Node size = total volume; edge direction: in/out; thicker = bigger flow.")
    try:
        payload = {
            "address": address,
            "chain": chain_all,
            "source_input": "Combined",
            "group_by": "wallet",
            "date": {"from": from_iso, "to": to_iso},
            "order_by": [{"field": "total_volume_usd", "direction": "DESC"}],
            "pagination": {"page": 1, "per_page": 10},
        }
        rows = client.profiler_address_counterparties(payload) 
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("No counterparty interactions found for the selected range.")
            return

        for col in ["total_volume_usd", "volume_in_usd", "volume_out_usd", "interaction_count"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["label"] = df["counterparty_address_label"].apply(_first_label)
        df["label"] = np.where(df["label"].isna(), df["counterparty_address"].apply(_short_addr), df["label"])

        G = nx.DiGraph()
        G.add_node(address, kind="wallet", label=_short_addr(address), total_vol=float(df["total_volume_usd"].sum()))
        for r in df.itertuples(index=False):
            cp = r.counterparty_address
            G.add_node(cp, kind="counterparty", label=r.label,
                       total_vol=float(r.total_volume_usd), interactions=int(r.interaction_count))
            if r.volume_out_usd > 0:
                G.add_edge(address, cp, vol=float(r.volume_out_usd), direction="out")
            if r.volume_in_usd > 0:
                G.add_edge(cp, address, vol=float(r.volume_in_usd), direction="in")

        pos = nx.spring_layout(G, k=0.6, seed=42)

        node_x, node_y, node_text, node_size = [], [], [], []
        for n in G.nodes():
            x, y = pos[n]
            node_x.append(x); node_y.append(y)
            node_text.append(G.nodes[n].get("label", _short_addr(n)))
            total_vol = float(G.nodes[n].get("total_vol", 0.0))
            node_size.append(30 if n == address else 10 + (30 if total_vol > 0 else 0))

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_text, textposition="top center",
            hoverinfo="text",
            marker=dict(size=node_size, color="#f5f5f5", line=dict(color="#333", width=1)),
            showlegend=False
        )

        edge_color_map = {"in": "green", "out": "orange"}
        legend_traces = [
            go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="green", width=3),
                       name="Inflow (counterparty → target)"),
            go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="orange", width=3),
                       name="Outflow (target → counterparty)"),
        ]

        anns = _arrow_annotations_from_graph(G, pos, color_map=edge_color_map, width_key=("vol",), base_dual_dir_offset=0.03, group_step=0.04, standoff_px=10)
        fig = go.Figure(data=[*legend_traces, node_trace])
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=anns,
            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
            margin=dict(t=100, l=10, r=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        counterparty_options = df["label"].tolist()
        col1, col2 = st.columns(2)
        with col1:
            selected_label = st.selectbox("Select a counterparty to view in Profiler", counterparty_options)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("View Profile", key=f"counterparty_{selected_label}"):
                selected_row = df.loc[df["label"] == selected_label].iloc[0]
                selected_address = selected_row["counterparty_address"]

                st.session_state["selected_wallet"] = selected_address
                st.session_state["selected_wallet_label"] = selected_label
                st.rerun()
    except Exception as e:
        st.error(f"Failed to load Counterparties Network: {e}")
