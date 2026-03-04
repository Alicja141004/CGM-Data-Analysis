import streamlit as st
import pandas as pd
from datetime import timedelta
from utils.load import load_all
import numpy as np
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title("Daily Profiles")
st.divider()

dfs = load_all()
g = dfs.get("glucose", pd.DataFrame())
infusion = dfs.get("infusion", pd.DataFrame())
meal = dfs.get("meal", pd.DataFrame())

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

        col_prev, col_date, col_next = st.columns([1, 4, 1])
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
        # aggregate CHO per day (sum); use meal timestamps to build masks
    if not meal.empty and 'Time' in meal.columns:
        meal_times = pd.to_datetime(meal['Time'], errors='coerce')
        meal_dates = meal_times.dt.date
        mask_meal_today = meal_dates == selected_day
        mask_meal_prev = meal_dates == prev_day
    else:
        mask_meal_today = pd.Series([False] * len(meal)) if not meal.empty else pd.Series(dtype=bool)
        mask_meal_prev = pd.Series([False] * len(meal)) if not meal.empty else pd.Series(dtype=bool)

    CHO_today_series = meal.loc[mask_meal_today, 'CHO'] if 'CHO' in meal.columns else pd.Series(dtype=float)
    CHO_prev_series = meal.loc[mask_meal_prev, 'CHO'] if 'CHO' in meal.columns else pd.Series(dtype=float)
    CHO_today = CHO_today_series.sum() if not CHO_today_series.empty else np.nan
    CHO_prev = CHO_prev_series.sum() if not CHO_prev_series.empty else np.nan

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
        color_discrete_map={'hypoglycemia': 'red', 'hyperglycemia': '#F59127', 'normoglycemia': '#53C257'}
    )
    fig.update_layout(width=300, height=300)

    c1, c2, c3, c4, c5 = st.columns(5, gap="medium")
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
    with c5:
        st.metric(
            "CHO",
            f"{CHO_today} g" if pd.notna(CHO_today) else "no data",
            delta=(f"{CHO_today - CHO_prev} g" if pd.notna(CHO_prev) else ""),
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

    meal_day = meal.copy()
    if not meal_day.empty and "Time" in meal_day.columns and not pd.api.types.is_datetime64_any_dtype(meal_day["Time"]):
        meal_day["Time"] = pd.to_datetime(meal_day["Time"], errors="coerce")
    meal_day = meal_day.dropna(subset=["Time"])
    meal_day = meal_day.loc[meal_day["Time"].dt.date == selected_day]

    st.subheader("Daily Glucose & Insulin Profile")
    if infusion_day.empty:
        st.info("No infusion data for the selected day.")
    else:
        col_to_plot = "Units"
        infusion_day = infusion_day.sort_values("Time").reset_index(drop=True)

        td = infusion_day["Time"].shift(-1) - infusion_day["Time"]
        td = td.fillna(pd.Timedelta(minutes=5))
        widths = td.dt.total_seconds() * 1000

        glucose_x = df_today.index
        glucose_y = df_today["Conc"]

        fig_bar = make_subplots(specs=[[{"secondary_y": True}]])

        fig_bar.add_trace(go.Bar(
            x=infusion_day["Time"],
            y=infusion_day[col_to_plot].astype(float),
            width=widths,
            marker_color="rgba(100,100,200,0.6)",
            hovertemplate="%{x}<br>" + col_to_plot + ": %{y}<br>duration: %{customdata}",
            customdata=td.astype(str),
            name="Infusion"
        ), secondary_y=True)

        fig_bar.add_trace(go.Scatter(
            x=df_today.index,
            y=df_today['Conc'],
            mode="lines",
            name="Glucose",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6)
        ), secondary_y=False)

        fig_bar.update_layout(
            xaxis=dict(type="date"),
            yaxis_title="Glucose (mg/dL)",
            bargap=0,
        )

        fig_bar.update_yaxes(title_text='Units (U/h)', secondary_y=True, range=[0, 3], showgrid=False)
        fig_bar.add_hline(y=70, line_dash="dash", line_color="red")
        fig_bar.add_hline(y=180, line_dash="dash", line_color="orange")

        y_base = df_today['Conc'].max()
        offset_step = 15
        meal_day = meal_day.sort_values("Time").reset_index(drop=True)
        label_y = y_base + offset_step
        for row in meal_day.itertuples():
            time_val = row.Time
            cho = getattr(row, "CHO", None)
            fig_bar.add_vline(x=time_val, line_width=2, line_dash="dash", line_color="purple")
            fig_bar.add_annotation(
                x=time_val,
                y=label_y,
                yref="y",
                text=f"{cho} g" if cho is not None else "meal",
                showarrow=False,
                yanchor="bottom"
            )

        st.plotly_chart(fig_bar, use_container_width=True)
st.divider()
# --- Post-Meal Metrics (0–2h after each meal) -----------------------------
st.subheader("Post-Meal Metrics")

if meal_day.empty or df_today.empty:
    st.info("No meal or glucose data available for post-meal analysis.")
else:
    # przygotuj dane (df_today ma index Time)
    g_today = df_today.reset_index()[["Time", "Conc"]].sort_values("Time").copy()
    m_today = meal_day[["Time", "CHO"]].sort_values("Time").copy()

    window_minutes = 120
    baseline_lookback_minutes = 15
    min_points_in_window = 6  # ~30 min przy próbkowaniu co 5 min (ustaw wg swoich danych)

    # baseline = ostatni pomiar w 15 minut przed posiłkiem
    baseline = pd.merge_asof(
        m_today,
        g_today,
        on="Time",
        direction="backward",
        tolerance=pd.Timedelta(minutes=baseline_lookback_minutes),
    ).rename(columns={"Conc": "Baseline"})
    rows = []
    for r in baseline.itertuples(index=False):
        meal_time = r.Time
        cho = r.CHO if hasattr(r, "CHO") else np.nan
        base = r.Baseline

        end_time = meal_time + pd.Timedelta(minutes=window_minutes)
        window = g_today[(g_today["Time"] >= meal_time) & (g_today["Time"] <= end_time)]

        n_points = len(window)

        # jeśli brak baseline albo za mało punktów w oknie → wpisz NaN
        if pd.isna(base) or n_points < min_points_in_window:
            rows.append({
                "Meal time": meal_time,
                "CHO (g)": cho,
                "Baseline (mg/dL)": base if pd.notna(base) else np.nan,
                "Peak (mg/dL)": np.nan,
                "Δ Glucose 2h (mg/dL)": np.nan,
                "Time to peak (min)": np.nan
            })
            continue

        peak_idx = window["Conc"].idxmax()
        peak_val = float(window.loc[peak_idx, "Conc"])
        peak_time = window.loc[peak_idx, "Time"]

        delta = peak_val - float(base)
        ttp = (peak_time - meal_time).total_seconds() / 60.0

        rows.append({
            "Meal time": meal_time,
            "CHO (g)": float(cho) if pd.notna(cho) else np.nan,
            "Baseline (mg/dL)": float(base),
            "Peak (mg/dL)": peak_val,
            "Δ Glucose 2h (mg/dL)": delta,
            "Time to peak (min)": ttp
        })

    post_meal = pd.DataFrame(rows).sort_values("Meal time")

    # format do dashboardu
    post_meal["Meal time"] = post_meal["Meal time"].dt.strftime("%Y-%m-%d %H:%M")
    num_cols = ["CHO (g)", "Baseline (mg/dL)", "Peak (mg/dL)", "Δ Glucose 2h (mg/dL)", "Time to peak (min)"]
    post_meal[num_cols] = post_meal[num_cols].round(1)

    st.dataframe(
        post_meal[["Meal time", "CHO (g)", "Δ Glucose 2h (mg/dL)", "Time to peak (min)", "Baseline (mg/dL)", "Peak (mg/dL)"]],
        use_container_width=True,
        hide_index=True
    )

    # małe KPI pod tabelką (opcjonalnie, ale wygląda mega profesjonalnie)
    valid = post_meal.dropna(subset=["Δ Glucose 2h (mg/dL)", "Time to peak (min)"])
    if not valid.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg 2h Δ Glucose", f"{valid['Δ Glucose 2h (mg/dL)'].mean():.1f} mg/dL")
        c2.metric("Median Time to Peak", f"{valid['Time to peak (min)'].median():.0f} min")
        c3.metric("% Meals with Peak > 180", f"{(valid['Peak (mg/dL)'] > 180).mean()*100:.0f}%")