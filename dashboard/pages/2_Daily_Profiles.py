import streamlit as st
import pandas as pd
from datetime import timedelta
from utils.load import load_all
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title("Daily Profiles")
st.divider()

dfs = load_all()
g = dfs.get("glucose", pd.DataFrame())
infusion = dfs.get("infusion", pd.DataFrame())

if not g.empty and "Time" in g.columns and not pd.api.types.is_datetime64_any_dtype(g["Time"]):
    g["Time"] = pd.to_datetime(g["Time"], errors="coerce")
    g = g.dropna(subset=["Time"])

with st.sidebar:
    st.header("Filters")
    if g.empty:
        st.info("No glucose data available.")
        selected_day = None
    else:
        min_date = g["Time"].min().date()
        max_date = g["Time"].max().date()

        st.session_state.setdefault("dad_date", min_date)
    
        if st.session_state["dad_date"] < min_date:
            st.session_state["dad_date"] = min_date
        if st.session_state["dad_date"] > max_date:
            st.session_state["dad_date"] = max_date

        def go_prev():
            st.session_state["dad_date"] = max(min_date, st.session_state["dad_date"] - timedelta(days=1))

        def go_next():
            st.session_state["dad_date"] = min(max_date, st.session_state["dad_date"] + timedelta(days=1))

        col_prev, col_date, col_next = st.columns([1,4,1])
        with col_prev:
            st.button("← Prev", key="prev_day", on_click=go_prev)
        with col_date:
            selected_day = st.date_input(
                "Select day",
                value=st.session_state["dad_date"],
                min_value=min_date,
                max_value=max_date,
                key="dad_date"
            )
        with col_next:
            st.button("Next →", key="next_day", on_click=go_next)

st.subheader("Key Glucose Metrics")

if g.empty or 'selected_day' not in locals() or selected_day is None:
    st.warning("No data or no day selected.")
else:
    mask_today = g['Time'].dt.date == selected_day

    prev_day = selected_day - timedelta(days=1)
    if 'min_date' in locals() and prev_day < min_date:
        prev_day = selected_day
    mask_prev = g['Time'].dt.date == prev_day

    if g.loc[mask_prev].empty:
        mask_prev = mask_today
        prev_day = selected_day

    vals_today = g.loc[mask_today, 'Conc']
    vals_prev = g.loc[mask_prev, 'Conc']

    mean_today = vals_today.mean()
    mean_prev = vals_prev.mean()

    def safe_cv(vals, mean):
        return (np.std(vals) / mean * 100) if (pd.notna(mean) and mean != 0 and len(vals) > 0) else np.nan

    CV_today = safe_cv(vals_today, mean_today)
    CV_prev = safe_cv(vals_prev, mean_prev)

    GMI_today = (3.31 + 0.02392 * mean_today) if pd.notna(mean_today) else np.nan
    GMI_prev = (3.31 + 0.02392 * mean_prev) if pd.notna(mean_prev) else np.nan

    # pie
    hypo = (vals_today < 70).sum()
    hyper = (vals_today > 180).sum()
    normal = vals_today.size - hypo - hyper
    data = pd.DataFrame({
        'category': ['hypoglycemia', 'hyperglycemia', 'normoglycemia'],
        'value': [int(hypo), int(hyper), int(normal)]
    })

    fig = px.pie(
        data, values='value', names='category', title='Time in Range',
        color='category',
        color_discrete_map={'hypoglycemia':'red', 'hyperglycemia':'#F59127', 'normoglycemia':'#53C257'}
    )
    fig.update_layout(width=300, height=300)

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.metric(
            "Mean glycemia",
            f"{mean_today:0.1f} mg/dL" if pd.notna(mean_today) else "no data",
            delta=(f"{mean_today - mean_prev:0.1f} mg/dL" if pd.notna(mean_prev) else ""),
            delta_color="inverse"
        )
    with c3:
        st.metric(
            "GMI",
            f"{GMI_today:0.1f} %" if pd.notna(GMI_today) else "no data",
            delta=(f"{GMI_today - GMI_prev:0.1f} %" if pd.notna(GMI_prev) else ""),
            delta_color="inverse"
        )
    with c4:
        st.metric(
            "CV",
            f"{CV_today:0.1f} %" if pd.notna(CV_today) else "no data",
            delta=(f"{CV_today - CV_prev:0.1f} %" if pd.notna(CV_prev) else ""),
            delta_color="inverse"
        )

    st.divider()
    df_today = g.loc[mask_today].copy()
    df_today = df_today.set_index("Time").sort_index()

    infusion_day = infusion.copy()
    if not infusion_day.empty and "Time" in infusion_day.columns and not pd.api.types.is_datetime64_any_dtype(infusion_day["Time"]):
        infusion_day["Time"] = pd.to_datetime(infusion_day["Time"], errors="coerce")
    infusion_day = infusion_day.dropna(subset=["Time"])

    infusion_day = infusion_day.loc[infusion_day["Time"].dt.date == selected_day]

    st.subheader("Daily Glucose & Insulin Profile")
    if infusion_day.empty:
        st.info("No infusion data for the selected day.")
    else:
        for preferred in ("Units", "Rate", "Value"):
            if preferred in infusion_day.columns:
                col_to_plot = preferred
                break
        else:
            numeric_cols = infusion_day.select_dtypes(include="number").columns.tolist()
            col_to_plot = numeric_cols[0] if numeric_cols else None

        if col_to_plot is None:
            st.info("No numeric infusion column (Units/Rate/Value) found to plot.")
        else:
            infusion_day = infusion_day.sort_values("Time").reset_index(drop=True)

            td = infusion_day["Time"].shift(-1) - infusion_day["Time"]
            td = td.fillna(pd.Timedelta(minutes=5))
            widths = td.dt.total_seconds() * 1000

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=infusion_day["Time"],
                y=infusion_day[col_to_plot].astype(float),
                width=widths,
                marker_color="rgba(100,100,200,0.6)",
                hovertemplate="%{x}<br>" + col_to_plot + ": %{y}<br>duration: %{customdata}",
                customdata=td.astype(str),
                name="Infusion"
            ))

            fig_bar.update_layout(
                xaxis=dict(type="date"),
                yaxis_title=col_to_plot,
                bargap=0,
                title=f"Infusion ({col_to_plot}) — {selected_day.isoformat()}"
            )

            st.plotly_chart(fig_bar, use_container_width=True)