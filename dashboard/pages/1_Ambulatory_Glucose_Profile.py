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

filters = sidebar_filters(g, key_prefix="agp") 

g_f = apply_filters(g, filters)

st.subheader("Daily Glucose Profile")
g_f['hour'] = g_f['Time'].dt.hour
g_f_mean = g_f.groupby('hour').mean().reset_index()
g_f['weekday_name'] = g_f['Time'].dt.day_name()

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
g_f['weekday_name'] = pd.Categorical(g_f['Time'].dt.day_name(), categories=days_order, ordered=True)

pivot = g_f.pivot_table(index='hour', columns='weekday_name', values='Conc', aggfunc='mean')

percentiles = (
    g_f.groupby('hour')['Conc']
    .quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    .unstack()
    .reset_index()
)
percentiles.columns = ['hour', 'p10', 'p25', 'median', 'p75', 'p90']

fig = go.Figure()

fig.add_scatter(x=percentiles.index, y=percentiles["p90"], mode="lines", line=dict(width=0), showlegend=False)
fig.add_scatter(x=percentiles.index, y=percentiles["p10"], mode="lines", fill="tonexty", name="10–90%", line=dict(width=0, color="#B4E3FF"))

fig.add_scatter(x=percentiles.index, y=percentiles["p75"], mode="lines", line=dict(width=0), showlegend=False)
fig.add_scatter(x=percentiles.index, y=percentiles["p25"], mode="lines", fill="tonexty", name="25–75%", line=dict(width=0, color="#65C3FA"))

fig.add_scatter(x=percentiles.index, y=percentiles["median"], mode="lines", name="Median", line=dict(width=3, color="#35B4FE"))

fig.update_layout(
    xaxis_title="Hour of Day",
    yaxis_title="Glucose (mg/dL)",
    hovermode="x unified",
    template="plotly_white",
    legend_title_text=""
)
fig.update_xaxes(dtick=2)


st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Heatmap of Deviations from Median")

fig, ax = plt.subplots(figsize=(10, 5))
sns.heatmap(pivot, cmap="coolwarm", annot=True, fmt=".0f", ax=ax)
ax.set_xlabel("Day of Week")
ax.set_ylabel("Hour of Day")
st.pyplot(fig)