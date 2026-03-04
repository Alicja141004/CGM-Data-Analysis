import streamlit as st
import pandas as pd
from utils.filters import init_global_filters, sidebar_filters, apply_filters
from utils.load import load_all
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title("Ambulatory Glucose Profile")
st.divider()

dfs = load_all()
g = dfs["glucose"]

init_global_filters(g)

# get filters and df_plot (df_plot = selected day(s) after sidebar selection)
filters, df_plot = sidebar_filters(g, key_prefix="agp")

# apply global filters and validate
g_f = apply_filters(g, filters)
if g_f is None or g_f.empty:
    st.warning("No glucose data available for selected filters.")
    st.stop()

g_f = g_f.sort_values("Time").copy()

st.subheader("Daily Glucose Profile")

# derive hour and weekday columns
g_f['hour'] = g_f['Time'].dt.hour
g_f['weekday_name'] = g_f['Time'].dt.day_name()

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
g_f['weekday_name'] = pd.Categorical(g_f['weekday_name'], categories=days_order, ordered=True)

# pivot for heatmap
pivot = g_f.pivot_table(index='hour', columns='weekday_name', values='Conc', aggfunc='mean')

percentiles = (
    g_f.groupby('hour')['Conc']
    .quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    .unstack()
    .reset_index()
)
percentiles.columns = ['hour', 'p10', 'p25', 'median', 'p75', 'p90']

fig = go.Figure()

fig.add_hline(y=70, line_dash="dash", line_color="red")
fig.add_hline(y=180, line_dash="dash", line_color="orange")

fig.add_scatter(x=percentiles['hour'], y=percentiles["p90"], mode="lines", line=dict(width=0), showlegend=False)
fig.add_scatter(x=percentiles['hour'], y=percentiles["p10"], mode="lines", fill="tonexty", name="10–90%", line=dict(width=0, color="#B4E3FF"))
fig.add_scatter(x=percentiles['hour'], y=percentiles["p75"], mode="lines", line=dict(width=0), showlegend=False)
fig.add_scatter(x=percentiles['hour'], y=percentiles["p25"], mode="lines", fill="tonexty", name="25–75%", line=dict(width=0, color="#65C3FA"))

fig.add_scatter(x=percentiles['hour'], y=percentiles["median"], mode="lines", name="Median", line=dict(width=3, color="#35B4FE"))

fig.update_layout(
    xaxis_title="Hour of Day",
    yaxis_title="Glucose (mg/dL)",
    hovermode="x unified",
    template="plotly_white",
    legend_title_text=""
)
fig.update_xaxes(dtick=2)

st.plotly_chart(fig)

# metrics from percentiles (hour values)
highest_idx = percentiles["median"].idxmax()
highest_median_hour = int(percentiles.loc[highest_idx, "hour"])
highest_median_value = percentiles["median"].max()
percentiles["variability"] = percentiles["p90"] - percentiles["p10"]
most_var_idx = percentiles["variability"].idxmax()
most_variable_hour = int(percentiles.loc[most_var_idx, "hour"])
most_variable_value = percentiles["variability"].max()

def segment(hour):
    if 6 <= hour < 12:
        return "Morning"
    elif 18 <= hour < 24:
        return "Evening"
    else:
        return "Other"

g_f["Segment"] = g_f["hour"].apply(segment)

morning_mean = g_f.loc[g_f["Segment"] == "Morning", "Conc"].mean()
evening_mean = g_f.loc[g_f["Segment"] == "Evening", "Conc"].mean()

evening_tar = ((g_f["Segment"] == "Evening") & (g_f["Conc"] > 180)).sum()
evening_total = (g_f["Segment"] == "Evening").sum()
evening_tar_pct = (evening_tar / evening_total * 100) if evening_total > 0 else 0.0


st.divider()
st.subheader("Insights")
c1, c2, c3, c4, c5 = st.columns(5, gap="medium")

st.write(
    """
    <style>
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
c1.metric(
    "Highest Median Window",
    f"{highest_median_hour}:00",
    f"{highest_median_value:.1f} mg/dL",
    delta_color="inverse"
)

c2.metric(
    "Most Variable Hour",
    f"{most_variable_hour}:00",
    f"Spread {percentiles['variability'].max():.1f}",
    delta_color="inverse"
)
c3.metric("Morning Mean", f"{morning_mean:.1f} mg/dL")
c4.metric("Evening Mean", f"{evening_mean:.1f} mg/dL")
c5.metric("Evening TAR %", f"{evening_tar_pct:.1f}%")

st.divider()
st.subheader("Median Glucose by Hour and Day")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    fig, ax = plt.subplots(figsize=(6, 6))
    sns.heatmap(
        pivot,
        cmap="coolwarm",
        annot=True,
        fmt=".0f",
        ax=ax
    )
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Hour of Day")
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='y', rotation=0)
    plt.tight_layout()
    st.pyplot(fig)
