import streamlit as st
import pandas as pd
import datetime as dt

def init_global_filters(glucose_df: pd.DataFrame):
    if "filters" not in st.session_state:
        st.session_state.filters = {}

    f = st.session_state.filters

    if not glucose_df.empty and "Time" in glucose_df.columns:
        if not pd.api.types.is_datetime64_any_dtype(glucose_df["Time"]):
            glucose_df["Time"] = pd.to_datetime(glucose_df["Time"], errors="coerce")

        min_date = glucose_df["Time"].min().date()
        max_date = glucose_df["Time"].max().date()
    else:
        today = dt.date.today()
        min_date = max_date = today

    f.setdefault("date_from", min_date)
    f.setdefault("date_to",   max_date)
    f.setdefault("hour_from", dt.time(0, 0))
    f.setdefault("hour_to",   dt.time(23, 59))
    f.setdefault("night_only", False)
    f.setdefault("weekdays", list(range(7)))


def time_in_range(t: dt.time, start: dt.time, end: dt.time) -> bool:
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end

def sidebar_filters(glucose_df: pd.DataFrame, key_prefix: str = "main") -> dict:
    f = st.session_state.filters

    day_labels = ["Pn","Wt","Śr","Cz","Pt","So","Nd"]
    idx_to_label = {i: day_labels[i] for i in range(7)}
    label_to_idx = {v: k for k, v in idx_to_label.items()}
    default_labels = [idx_to_label[i] for i in f["weekdays"] if i in idx_to_label]

    if not glucose_df.empty and "Time" in glucose_df.columns:
        min_date = glucose_df["Time"].min().date()
        max_date = glucose_df["Time"].max().date()
    else:
        min_date = f["date_from"]
        max_date = f["date_to"]

    with st.sidebar:
        st.header("Zakres danych")

        c1, c2, c3, c4 = st.columns(4)
        if c1.button("24h", key=f"{key_prefix}_btn_24h"):
            f["date_from"], f["date_to"] = max_date - dt.timedelta(days=1), max_date
            st.rerun()
        if c2.button("7 dni", key=f"{key_prefix}_btn_7d"):
            f["date_from"], f["date_to"] = max_date - dt.timedelta(days=6), max_date
            st.rerun()
        if c3.button("14 dni", key=f"{key_prefix}_btn_14d"):
            f["date_from"], f["date_to"] = max_date - dt.timedelta(days=13), max_date
            st.rerun()
        if c4.button("30 dni", key=f"{key_prefix}_btn_30d"):
            f["date_from"], f["date_to"] = max_date - dt.timedelta(days=29), max_date
            st.rerun()

        date_from, date_to = st.date_input(
            "Zakres dat",
            value=(f["date_from"], f["date_to"]),
            key=f"{key_prefix}_date_range",
        )
        f["date_from"], f["date_to"] = date_from, date_to

        st.subheader("Zakres godzin")
        night_only = st.checkbox(
            "Tylko noc (00–06)",
            value=f["night_only"],
            key=f"{key_prefix}_night",
        )
        f["night_only"] = night_only

        if night_only:
            hour_from, hour_to = dt.time(0, 0), dt.time(6, 0)
            st.info("Aktywny tryb nocny: 00:00–06:00")
        else:
            hour_from, hour_to = st.slider(
                "Godziny",
                min_value=dt.time(0, 0), max_value=dt.time(23, 59),
                value=(f["hour_from"], f["hour_to"]),
                step=dt.timedelta(minutes=5),
                key=f"{key_prefix}_hours",
            )
        f["hour_from"], f["hour_to"] = hour_from, hour_to

        st.subheader("Dni tygodnia")
        selected_labels = st.multiselect(
            "Wybierz dni",
            options=day_labels,
            default=default_labels,
            key=f"{key_prefix}_weekdays",
        )
        f["weekdays"] = [label_to_idx[l] for l in selected_labels]

    return f

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if df is None or df.empty or "Time" not in df.columns:
        return df

    out = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(out["Time"]):
        out["Time"] = pd.to_datetime(out["Time"], errors="coerce")

    dfrom = filters["date_from"]
    dto   = filters["date_to"]
    out = out[(out["Time"].dt.date >= dfrom) & (out["Time"].dt.date <= dto)]
    if out.empty:
        return out

    h_from = filters["hour_from"]
    h_to   = filters["hour_to"]
    out = out[out["Time"].dt.time.apply(lambda t: time_in_range(t, h_from, h_to))]
    if out.empty:
        return out

    weekdays = set(filters["weekdays"])
    out = out[out["Time"].dt.weekday.isin(weekdays)]

    return out


