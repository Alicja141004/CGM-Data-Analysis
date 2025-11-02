import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
from utils.filters import apply_filters, init_global_filters, sidebar_filters
from utils.load import load_glucose

st.set_page_config(page_title="CGM Dashboard", layout="wide")
st.title("CGM Dashboard")

g = load_glucose()
init_global_filters(g)
filters = sidebar_filters(g, key_prefix='main')
g_f = apply_filters(g, filters)

st.divider()

# TIR Pie
hypo = (g_f['Conc'] < 70).sum()
hyper = (g_f['Conc'] > 180).sum()
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

st.subheader("Key Glucose Metrics")
c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    st.plotly_chart(fig, use_container_width=False)
with c2:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.metric(
            "Mean glycemia",
            f"{mean_glycemia:0.1f}mg/L",
            delta=f"{mean_glycemia - mean_glycemia_1st_month:0.1f}mg/L",
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
    
st.divider()

# line chart
st.subheader("Daily Glucose Trends")
st.line_chart(g_f.set_index("Time")["Conc"])

