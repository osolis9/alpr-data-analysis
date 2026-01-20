# run this app locally by running this in your terminal:
# streamlit run streamlit_survey_dashboard.py
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title="ALPR Survey Explorer", layout="wide")
# ---------- Load data ----------
CSV_PATH = "ALPR General Survey Results v2.csv"  # change if needed
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    # Standardize column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]
    # Add a canonical ZIP column alias
    zip_col_candidates = [
        "What is your ZIP code? (7bepp7b)",
        "ZIP",
        "Zip",
        "Zip Code",
        "ZIP Code",
    ]
    zip_col = next((c for c in zip_col_candidates if c in df.columns), None)
    if zip_col is None:
        st.warning("ZIP column not found. Expected 'What is your ZIP code? (7bepp7b)'.")
        # Create an empty placeholder to avoid downstream errors
        df["_ZIP_FALLBACK_"] = np.nan
        zip_col = "_ZIP_FALLBACK_"
    # Normalize ZIP values as strings, keep original for display if needed
    df["_ZIP_NORM_"] = (
        df[zip_col]
        .astype(str)
        .str.strip()
        .str.replace(r"[^0-9A-Za-z\- ]", "", regex=True)
        .replace({"nan": np.nan})
    )
    return df, zip_col

df, real_zip_col = load_data(CSV_PATH)

st.title("ALPR Survey Explorer")
st.caption("Filter by **City (Oakland preset)** or **ZIP code**, then visualize responses for any question.")

# ---------- Define city ZIP presets ----------
OAKLAND_ZIPS = [
    "94552", "94546", "94605", "94621", "94619" ,"94577", "94501", 
    "94607", "94578", "94602", "94516", "94705", "94708", "94611",
    "94580", "94601", "94579", "94608", "94603", "94502", "94618"
]

CITY_ZIP_MAP = {
    "Oakland": set(z.strip() for z in OAKLAND_ZIPS)
}

# ---------- Helper: question columns ----------
def guess_question_columns(all_cols):
    excluded = {real_zip_col, "_ZIP_NORM_"}
    q_cols = [c for c in all_cols if c not in excluded and ("?" in c)]
    if not q_cols:
        q_cols = [c for c in all_cols if c not in excluded and df[c].dtype == "object"]
    return q_cols


question_cols = guess_question_columns(df.columns)
if not question_cols:
    st.error("No likely question columns found. Please verify your CSV.")
    st.stop()

question_cols.extend([
    'It’s okay for police to track and store the location data of people who haven’t done anything wrong. (nd9oynf)',
    'Surveillance technologies such as ALPRs increase public safety. (u84m4pd)',
    'age',
    'gender',
    'education',
    'educationScore',
    'politicalViews',
    'householdIncomeEstimate',
])

question_cols.remove('testing question? (8vufenf)')

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Filters")
    city_choice = st.selectbox("City preset", ["All cities"] + list(CITY_ZIP_MAP.keys()))

    # Base ZIP options given city choice
    if city_choice == "All cities":
        allowed_zips = sorted([z for z in df["_ZIP_NORM_"].dropna().unique().tolist() if z != ""],
                              key=lambda x: (len(str(x)), str(x)))
    else:
        allowed_zips = sorted(CITY_ZIP_MAP[city_choice])

    zip_options = ["All ZIP codes"] + allowed_zips
    selected_zip = st.selectbox("ZIP code", zip_options, index=0,
                                help="If a city is selected, this list only includes that city's ZIPs.")

    st.markdown("---")
    st.header("Chart options")
    sort_mode = st.radio("Sort bars by", ["Count (desc)", "Response (A→Z)"], index=0)
    show_pct = st.checkbox("Show percentages instead of counts", value=False)
    split_multi = st.checkbox("Split multi-select answers (common delimiters)", value=True)
    top_n = st.slider("Limit to top N responses (0 = show all)", min_value=0, max_value=50, value=0, step=1)

# ---------- Apply filters ----------
filtered = df.copy()

if city_choice != "All cities":
    filtered = filtered[filtered["_ZIP_NORM_"].isin(CITY_ZIP_MAP[city_choice])]

if selected_zip != "All ZIP codes":
    filtered = filtered[filtered["_ZIP_NORM_"] == selected_zip]

if filtered.empty:
    st.warning("No rows match the current City/ZIP filter. Try expanding your filters.")

# ---------- Question selection ----------
question = st.selectbox("Select question", question_cols)

# ---------- Prepare counts ----------
series = filtered[question].dropna().astype(str).str.strip()

if split_multi:
    split_seps = r";|\||,"
    exploded = (
        series.str.split(split_seps)
        .explode()
        .str.strip()
        .replace("", np.nan)
        .dropna()
    )
    counts = exploded.value_counts(dropna=False)
else:
    counts = series.value_counts(dropna=False)

if top_n and top_n > 0:
    counts = counts.head(top_n)

if sort_mode == "Response (A→Z)":
    counts = counts.sort_index()
else:
    counts = counts.sort_values(ascending=False)

total_n = int(counts.sum())
pct = (counts / total_n * 100).round(1) if total_n else counts*0

# ---------- Header / metrics ----------
left, right = st.columns([2,1])
with left:
    loc_label = "All cities" if city_choice == "All cities" else city_choice
    if selected_zip != "All ZIP codes":
        loc_label += f" · ZIP {selected_zip}"
    st.subheader(f"Distribution — {loc_label}")
with right:
    st.metric("Responses counted", f"{total_n:,}")

# ---------- Plot ----------
data = pd.DataFrame({
    "Response": counts.index.astype(str),
    "Count": counts.values,
    "Percent": pct.values
})

y_field = "Percent" if show_pct else "Count"
title_suffix = " (%)" if show_pct else " (count)"
chart = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x=alt.X("Response:N", sort=list(data["Response"])),
        y=alt.Y(f"{y_field}:Q"),
        tooltip=["Response:N", "Count:Q", "Percent:Q"]
    )
    .properties(height=420, title=f"{question}{title_suffix}")
)
st.altair_chart(chart, use_container_width=True)

# ---------- Table & downloads ----------
st.markdown("#### Data table")
st.dataframe(data, use_container_width=True, hide_index=True)

@st.cache_data
def to_csv_bytes(df_in: pd.DataFrame) -> bytes:
    return df_in.to_csv(index=False).encode("utf-8")

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button(
        "Download counts (CSV)",
        data=to_csv_bytes(data),
        file_name="counts.csv",
        mime="text/csv"
    )
with c2:
    cols = [question]
    if real_zip_col in filtered.columns:
        cols.append(real_zip_col)
    st.download_button(
        "Download filtered rows (CSV)",
        data=to_csv_bytes(filtered[cols]),
        file_name="filtered_rows.csv",
        mime="text/csv"
    )
with c3:
    st.download_button(
        "Download full filtered dataset (CSV)",
        data=to_csv_bytes(filtered),
        file_name="filtered_dataset.csv",
        mime="text/csv"
    )

with st.expander("Notes & Tips"):
    st.markdown(
        f"""
- **Filter precedence:** *City* filters the dataset first. *ZIP* (if chosen) further narrows within that city.
- **Multi-select answers:** Enable *Split multi-select answers* to count each selected option separately.
"""
    )
