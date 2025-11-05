import streamlit as st
import pandas as pd
from utils.load import load_all

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title("Day After Day")

dfs = load_all()
g = dfs.get("glucose", pd.DataFrame())

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
        selected_day = st.date_input("Select day", value=min_date, min_value=min_date, max_value=max_date, key="dad_date")

if g.empty or selected_day is None:
    st.warning("Brak danych do wyświetlenia.")
else:
    mask = g["Time"].dt.date == selected_day
    g_f = g.loc[mask].copy()
    if g_f.empty:
        st.warning(f"Brak pomiarów dla dnia {selected_day}.")
    else:
        st.write(f"Wierszy w wybranym dniu: {len(g_f)}")
        st.dataframe(g_f.reset_index(drop=True))
