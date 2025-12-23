import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Auto Data Analyzer", layout="wide")

st.title("📊 Auto Dataset Analyzer")

# -------------------------
# Helper Functions
# -------------------------

def convert_year_month(col):
    try:
        s = col.astype(str)
        if s.str.match(r"^\d{4}\.\d{1,2}$").all():
            return pd.to_datetime(s, format="%Y.%m")
    except:
        pass
    return col


def ml_readiness_score(df):
    score = 0
    notes = []

    if len(df) >= 100:
        score += 25
    else:
        notes.append("Dataset is small")

    missing_ratio = df.isna().mean().mean()
    if missing_ratio < 0.1:
        score += 25
    else:
        notes.append("High missing values")

    numeric_cols = df.select_dtypes(include=np.number).columns
    if len(numeric_cols) >= 3:
        score += 25
    else:
        notes.append("Few numeric features")

    if df.duplicated().sum() == 0:
        score += 25
    else:
        notes.append("Duplicate rows found")

    return score, notes


def suggest_algorithms(df):
    numeric_cols = df.select_dtypes(include=np.number).columns
    cat_cols = df.select_dtypes(include="object").columns

    algos = []
    if len(numeric_cols) >= 3:
        algos.extend(["Linear Regression", "Random Forest", "XGBoost"])
    if len(cat_cols) > 0:
        algos.append("Decision Tree")
    if len(df) > 500:
        algos.append("Neural Network")

    return list(set(algos))


# -------------------------
# File Upload
# -------------------------

file = st.file_uploader("Upload CSV file", type=["csv"])

if file:
    df = pd.read_csv(file)

    # Convert YYYY.MM floats to datetime
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = convert_year_month(df[c])

    st.success("File loaded successfully")

    # -------------------------
    # Column Datatypes
    # -------------------------

    st.subheader("🧱 Column Datatypes")

    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(df[c].dtype) for c in df.columns]
    })

    st.dataframe(dtype_df, use_container_width=True)

    # -------------------------
    # Dataset Metrics
    # -------------------------

    st.subheader("📌 Dataset Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", df.shape[0])
    col2.metric("Columns", df.shape[1])
    col3.metric("Missing %", f"{df.isna().mean().mean()*100:.2f}%")

    # -------------------------
    # Numeric Column Selection
    # -------------------------

    numeric_cols = [
        c for c in df.select_dtypes(include=np.number).columns
        if df[c].nunique(dropna=True) > 1 and df[c].isna().mean() < 0.9
    ]

    # -------------------------
    # Min / Max / Avg Section
    # -------------------------

    st.subheader("📈 Min / Max / Avg (Numeric Columns)")

    for col in numeric_cols:
        min_val = float(df[col].min())
        max_val = float(df[col].max())
        avg_val = float(df[col].mean())

        st.markdown(f"**{col}**")
        st.write(f"Min: {min_val} | Max: {max_val} | Avg: {avg_val}")

        bar_range = max_val - min_val if max_val != min_val else 1

        st.progress((avg_val - min_val) / bar_range)

    # -------------------------
    # Column Graphs
    # -------------------------

    st.subheader("📊 Column Graphs")

    selected_col = st.selectbox("Select a numeric column", numeric_cols)

    fig_line = px.line(df, y=selected_col, title=f"{selected_col} Trend")
    st.plotly_chart(fig_line, use_container_width=True)

    # -------------------------
    # Correlation Section
    # -------------------------

    st.subheader("🔥 Correlation Analysis")

    corr = df[numeric_cols].corr()
    corr_clean = corr.fillna(0)

    fig_heat = px.imshow(
        corr_clean,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        title="Correlation Heatmap"
    )

    st.plotly_chart(fig_heat, use_container_width=True)
    st.dataframe(corr, use_container_width=True)

    # -------------------------
    # ML Readiness
    # -------------------------

    st.subheader("🤖 ML Readiness Score")

    score, notes = ml_readiness_score(df)

    st.markdown(f"### Score: {score} / 100")

    st.progress(score / 100)

    if notes:
        st.warning("⚠ Issues:")
        for n in notes:
            st.write("-", n)
    else:
        st.success("Dataset is ML-ready")

    # -------------------------
    # Algorithm Suggestions
    # -------------------------

    st.subheader("🧠 Suggested ML Algorithms")

    algos = suggest_algorithms(df)
    for a in algos:
        st.write("•", a)
