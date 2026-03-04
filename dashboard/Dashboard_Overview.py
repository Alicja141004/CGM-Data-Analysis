import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
from utils.filters import apply_filters, init_global_filters, sidebar_filters
from utils.load import load_glucose
import altair as alt

st.set_page_config(page_title="CGM Dashboard", layout="wide")
st.title("CGM Dashboard")

g = load_glucose()
init_global_filters(g)
filters, df_plot = sidebar_filters(g, key_prefix='main')
g_f = apply_filters(g, filters)
st.divider()

# Metric data
first_month = g['Time'].min().month
first_year = g['Time'].min().year
mask = (g['Time'].dt.year == first_year) & (g['Time'].dt.month == first_month)
mean_glycemia = g_f['Conc'].mean()
mean_glycemia_1st_month = g.loc[mask, 'Conc'].mean()
GMI = 3.31+0.02392*mean_glycemia
GMI_1st_month = 3.31+0.02392*mean_glycemia_1st_month
CV = np.std(g_f['Conc']) / mean_glycemia * 100
CV_1st_month = np.std(g.loc[mask, 'Conc']) / mean_glycemia_1st_month * 100

# TIR Pie
hypo = (g_f['Conc'] < 70).sum()
hypo_1st = ((g.loc[mask, 'Conc'] < 70)).sum()
tbr = (g_f['Conc'] < 70).mean() * 100
tbr_1st = (g.loc[mask, 'Conc'] < 70).mean() * 100
hyper = (g_f['Conc'] > 180).sum()
hyper_1st = (g.loc[mask, 'Conc'] > 180).sum()
tar = hyper / (g_f['Conc']).count() * 100
tar_1st = hyper_1st / (g.loc[mask, 'Conc']).count() * 100
normal = len(g_f) - hyper - hypo
data = pd.DataFrame({
    'Kategoria': ['hypoglycemia', 'hyperglycemia', 'normoglycemia'],
    'Wartość': [hypo, hyper, normal]
})
fig = px.pie(data, values='Wartość', names='Kategoria', title='Time in Range',
             color = 'Kategoria',
             color_discrete_map={'hypoglycemia':'red',
                                 'hyperglycemia': '#F59127',
                                 'normoglycemia':'#53C257'},)
fig.update_layout(width=300, height=300)


st.subheader("Key Glucose Metrics")
c1, c2, c3, c4, c5, c6 = st.columns(6, gap="medium")
with c1:
    st.plotly_chart(fig, use_container_width=False)
with c2:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.metric(
            "Mean glycemia",
            f"{mean_glycemia:0.1f}mg/dL",
            delta=f"{mean_glycemia - mean_glycemia_1st_month:0.1f}mg/dL",
            delta_color="inverse"
        )
with c3:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.metric(
            "GMI",
            f"{GMI:0.1f}%",
            delta=f"{GMI - GMI_1st_month:0.1f}%",
            delta_color="inverse"
        )
with c4:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.metric(
            "CV",
            f"{CV:0.1f}%",
            delta=f"{CV - CV_1st_month:0.1f}%",
            delta_color="inverse"
        )
with c5:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.metric(
            "TAR",
            f"{tar:0.1f}%",
            delta=f"{tar - tar_1st:0.1f}%",
            delta_color="inverse"
        )
with c6:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.metric(
            "TBR",
            f"{tbr:0.1f}%",
            delta=f"{tbr - tbr_1st:0.1f}%",
            delta_color="inverse"
        )
st.divider()

st.subheader("Daily Glucose Trends")

y_scale = alt.Scale(domain=[40, 350])

base = alt.Chart(df_plot).encode(
    x=alt.X('Time:T', axis=alt.Axis(title='Time')),
    y=alt.Y('Conc:Q', scale=y_scale, axis=alt.Axis(title='Glucose (mg/dL)'))
)

line = base.mark_line(color='blue')

hypo_area = alt.Chart(pd.DataFrame({"y1":[40], "y2":[70]})).mark_rect(opacity=0.10, color='red').encode(
    y='y1:Q', y2='y2:Q'
).properties(width='container')

target_area = alt.Chart(pd.DataFrame({"y1":[70], "y2":[180]})).mark_rect(opacity=0.06, color='green').encode(
    y='y1:Q', y2='y2:Q'
).properties(width='container')

hyper_area = alt.Chart(pd.DataFrame({"y1":[180], "y2":[350]})).mark_rect(opacity=0.08, color='orange').encode(
    y='y1:Q', y2='y2:Q'
).properties(width='container')


st.altair_chart(hypo_area + target_area + hyper_area + line, use_container_width=True)