import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📄 Auto-Documenter", page_icon="📊", layout="wide")

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload CSV, Excel, or JSON to generate interactive dataset insights.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # Load dataframe
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    # ---------- FILE PREVIEW ----------
    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- DATASET METRICS ----------
    st.markdown("## 📊 Dataset Metrics")
    rows, cols = df.shape
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", rows)
    c2.metric("Columns", cols)
    c3.metric("Numeric Columns", len(numeric_cols))
    c4.metric("Categorical Columns", len(categorical_cols))

    # ---------- COLUMN DATATYPES ----------
    st.markdown("## 📌 Column Datatypes")
    col_types = pd.Series(df.dtypes).astype(str)
    for col, dtype in col_types.items():
        st.write(f"- **{col}**: {dtype}")

    # ---------- MISSING VALUES ----------
    st.markdown("## ⚠ Missing Values % per Column")
    missing_pct = (df.isna().sum() / len(df) * 100).round(2)
    st.dataframe(missing_pct, use_container_width=True)

    # ---------- ML READINESS SCORE ----------
    completeness = round(100 - missing_pct.mean(), 2)
    duplicate_pct = round(df.duplicated().mean() * 100, 2)
    ml_ready_score = round(
        (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
        (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
        (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15),
        2
    )
    st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
    st.metric("ML Readiness Score", f"{ml_ready_score}/100")
    if numeric_cols and len(numeric_cols) > 1:
        st.write("- Regression: Linear Regression, Random Forest Regressor, Gradient Boosting")
    if categorical_cols:
        st.write("- Classification: Decision Tree, Random Forest, XGBoost, Logistic Regression")
    if numeric_cols and not categorical_cols:
        st.write("- Clustering: KMeans, DBSCAN, Hierarchical Clustering")

    # ---------- COLUMN GRAPHS ----------
    st.markdown("## 📈 Column Graphs (Min, Max, Avg)")
    for col in numeric_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        col_avg = round(df[col].mean(), 2)

        st.markdown(f"### {col}: Min={col_min}, Max={col_max}, Avg={col_avg}")
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(df[col], marker='o', linestyle='-', label=col)
        ax.axhline(col_min, color='red', linestyle='--', label=f'Min={col_min}')
        ax.axhline(col_max, color='green', linestyle='--', label=f'Max={col_max}')
        ax.axhline(col_avg, color='blue', linestyle='-.', label=f'Avg={col_avg}')
        ax.set_title(f"{col} Min/Max/Avg")
        ax.set_xlabel("Index")
        ax.set_ylabel(col)
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)

    # ---------- CORRELATION HEATMAP ----------
    if len(numeric_cols) > 1:
        st.markdown("## 🔗 Correlation Heatmap")
        corr = df[numeric_cols].corr().round(2)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
        st.pyplot(fig)
        plt.close(fig)
