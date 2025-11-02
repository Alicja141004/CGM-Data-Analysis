import streamlit as st
import pandas as pd
from utils.filters import init_global_filters, sidebar_filters, apply_filters
from utils.load import load_all

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title("day after day")

dfs = load_all()
g = dfs["glucose"]

init_global_filters(g)

filters = sidebar_filters(g, key_prefix="dad") 

g_f = apply_filters(g, filters)

if g_f.empty:
    st.warning("Brak danych w wybranym zakresie.")
else:
    st.write(f"Wierszy po filtrach: {len(g_f)}")
