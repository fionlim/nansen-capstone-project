# components/pfl_related_wallet_network.py
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

def _arrow_annotations_from_graph(G, pos, *, color_map, width_key=("w",), base_dual_dir_offset=0.03, group_step=0.04, standoff_px=10):
    anns = []
    from collections import defaultdict
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
            color_key = data.get("cat", "other")
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

def render_related_wallet_network(client: NansenClient, address: str, chain_tx: str):
    st.subheader("Top 10 Related wallets network")
    st.text("Colour = relation; arrows=direction; thicker=more recent.")

    try:
        payload = {
            "address": address,
            "chain": chain_tx,   # now uses the selected tx chain
            "pagination": {"page": 1, "per_page": 10},
            "order_by": [{"field": "order", "direction": "ASC"}],
        }
        resp = client.profiler_address_related_wallets(payload)
        df = df = pd.DataFrame(resp)
        if df.empty:
            st.info("No related wallets found.")
            return

        df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], errors="coerce")
        df["label"] = df["address_label"].apply(_first_label)
        df["label"] = np.where(df["label"].isna(), df["address"].apply(_short_addr), df["label"])

        def classify_relation(rel: str):
            r = (rel or "").lower()
            if "funder" in r or "fund" in r or "first funder" in r:
                return "funding", "in"
            if "multisig" in r or "signer" in r:
                return "multisig", "in"
            if "deployed via" in r:
                return "factory", "in"
            if "deployed contract" in r:
                return "deploy", "out"
            return "other", "in"

        df[["cat", "dir"]] = df["relation"].apply(lambda x: pd.Series(classify_relation(x)))

        if df["block_timestamp"].notna().any():
            tmin, tmax = df["block_timestamp"].min(), df["block_timestamp"].max()
            span = (tmax - tmin).total_seconds() if pd.notna(tmax) and pd.notna(tmin) else 1
            df["recency_w"] = df["block_timestamp"].apply(
                lambda t: 0.5 + 4.5 * ((t - tmin).total_seconds() / (span + 1e-9)) if pd.notna(t) else 1.0
            )
        else:
            df["recency_w"] = 1.0

        cat_importance = {"funding": 1.0, "multisig": 0.9, "factory": 0.7, "deploy": 0.5, "other": 0.6}
        cat_color = {"funding": "green", "multisig": "purple", "factory": "blue", "deploy": "orange", "other": "gray"}

        G2 = nx.DiGraph()
        G2.add_node(address, kind="target", label=_short_addr(address), importance=1.2)

        for r in df.itertuples(index=False):
            n = r.address
            G2.add_node(n, kind=r.cat, label=r.label, importance=cat_importance.get(r.cat, 0.6))
            if r.dir == "in":
                G2.add_edge(n, address, cat=r.cat, w=float(r.recency_w))
            else:
                G2.add_edge(address, n, cat=r.cat, w=float(r.recency_w))

        pos2 = nx.spring_layout(G2, k=0.7, seed=42)
        nxs, nys, ntexts, nsizes = [], [], [], []
        for n in G2.nodes():
            x, y = pos2[n]
            nxs.append(x); nys.append(y)
            ntexts.append(G2.nodes[n].get("label", _short_addr(n)))
            imp = float(G2.nodes[n].get("importance", 0.6))
            nsizes.append(28 if n == address else 12 + 26 * imp)

        node_trace2 = go.Scatter(
            x=nxs, y=nys,
            mode="markers+text",
            text=ntexts, textposition="top center",
            hoverinfo="text",
            marker=dict(size=nsizes, color="#ffffff", line=dict(color="#333", width=1)),
            showlegend=False
        )

        present_cats = sorted({data.get("cat", "other") for _, _, data in G2.edges(data=True)})
        legend_traces2 = [
            go.Scatter(x=[None], y=[None], mode="lines",
                       line=dict(color=cat_color[c], width=3),
                       name=c.capitalize())
            for c in present_cats
        ]

        anns2 = _arrow_annotations_from_graph(G2, pos2, color_map=cat_color, width_key=("w",), base_dual_dir_offset=0.03, group_step=0.04, standoff_px=10)
        fig_rel = go.Figure(data=[*legend_traces2, node_trace2])
        fig_rel.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=anns2,
            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
            margin=dict(t=100, l=10, r=10, b=10),
        )
        st.plotly_chart(fig_rel, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load Related Wallets Network: {e}")
