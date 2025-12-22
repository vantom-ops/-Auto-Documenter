import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from parser import analyze_file  # or your phraiser.py
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate dataset insights.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- METRICS ----------
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    st.markdown("## 📊 Dataset Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Numeric Columns", len(numeric_cols))
    c4.metric("Categorical Columns", len(categorical_cols))

    # ---------- COLUMN DATATYPES ----------
    st.markdown("## 📌 Column Datatypes")
    col_df = pd.DataFrame({"Column": df.columns, "Datatype": df.dtypes.astype(str)})
    st.dataframe(col_df, use_container_width=True)

    # ---------- MIN / AVG / MAX GRADIENT BAR ----------
    st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
    for col in numeric_cols:
        min_val = df[col].min()
        avg_val = df[col].mean()
        max_val = df[col].max()

        min_norm = 0.33
        avg_norm = 0.33
        max_norm = 0.34

        st.markdown(f"**{col}**")
        st.markdown(f"""
        <div style="display:flex; gap:4px; margin-bottom:4px;">
            <div style="flex:{min_norm}; background:linear-gradient(to right, #ff4b4b, #ff9999); height:20px;"></div>
            <div style="flex:{avg_norm}; background:linear-gradient(to right, #ffea00, #ffd700); height:20px;"></div>
            <div style="flex:{max_norm}; background:linear-gradient(to right, #00ff4b, #00cc33); height:20px;"></div>
        </div>
        <div style="margin-bottom:10px;">Red: Min | Yellow: Avg | Green: Max</div>
        """, unsafe_allow_html=True)

    # ---------- COLUMN GRAPHS (INTERACTIVE) ----------
    with st.expander("📊 Column Graphs", expanded=False):
        for col in numeric_cols:
            fig = px.line(df, y=col, title=f"{col} Trend")
            st.plotly_chart(fig, use_container_width=True)

    # ---------- CORRELATION ----------
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr().round(2)
        with st.expander("🔥 Correlation Heatmap & Table", expanded=False):
            st.markdown("### Correlation Heatmap")
            fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Correlation Table")
            st.dataframe(corr, use_container_width=True)

    # ---------- WARNINGS ----------
    st.markdown("## ⚠ Warnings (% Missing Values)")
    missing_pct = (df.isna().sum() / len(df) * 100).round(2)
    st.dataframe(missing_pct, use_container_width=True)

    # ---------- ML READINESS SCORE & ALGORITHMS ----------
    st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
    completeness = 100 - missing_pct.mean()
    duplicate_pct = df.duplicated().mean() * 100
    ml_score = round(
        (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
        (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
        (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15), 2
    )

    st.markdown(f"""
    <div style="background:linear-gradient(to right, #00ccff, #0066ff); width:100%; height:20px; border-radius:5px; margin-bottom:5px;"></div>
    <p>ML Readiness Score: {ml_score}/100</p>
    <p>Suggested Algorithms:</p>
    <ul>
        {"<li>Regression: Linear Regression, Random Forest, Gradient Boosting</li>" if numeric_cols else ""}
        {"<li>Classification: Decision Tree, Random Forest, XGBoost, Logistic Regression</li>" if categorical_cols else ""}
        {"<li>Clustering: KMeans, DBSCAN, Hierarchical Clustering</li>" if numeric_cols and not categorical_cols else ""}
    </ul>
    """, unsafe_allow_html=True)
