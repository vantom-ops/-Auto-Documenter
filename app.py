import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📄 Auto-Documenter", page_icon="📊", layout="wide")

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload CSV, Excel, or JSON to view dataset insights.")

# ---------- SIDEBAR ----------
with st.sidebar:
    preview_rows = st.slider("Preview Rows", 5, 50, 10)
    show_graphs = st.checkbox("Show Column Graphs", True)
    show_corr = st.checkbox("Show Correlation Analysis", True)

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
    col_types_df = pd.DataFrame({'Column': df.columns, 'Type': df.dtypes.astype(str)})
    st.table(col_types_df)

    # ---------- MIN/MAX/AVG NON-INTERACTIVE BARS ----------
    st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
    for col in numeric_cols:
        min_val = df[col].min()
        avg_val = df[col].mean()
        max_val = df[col].max()

        # Non-interactive gradient bar using st.progress with description text
        bar_total = max_val if max_val != 0 else 1
        st.markdown(f"**{col}**")
        st.progress(min_val / bar_total)  # Red portion
        st.progress(avg_val / bar_total)  # Yellow portion
        st.progress(max_val / bar_total)  # Green portion
        st.text("Red: Min, Yellow: Avg, Green: Max")  # descriptive text only

    # ---------- INTERACTIVE COLUMN GRAPHS ----------
    if show_graphs and numeric_cols:
        st.markdown("## 📊 Column Graphs")
        for col in numeric_cols:
            fig = px.line(df, y=col, title=f"{col} Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    # ---------- INTERACTIVE CORRELATION HEATMAP ----------
    if show_corr and len(numeric_cols) > 1:
        st.markdown("## 🔗 Correlation Heatmap")
        corr = df[numeric_cols].corr().round(2)
        fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Correlation Table")
        st.dataframe(corr, use_container_width=True)

    # ---------- MISSING VALUE WARNINGS ----------
    st.markdown("## ⚠ Missing Values % per Column")
    missing_pct = (df.isna().sum() / len(df) * 100).round(2)
    st.dataframe(missing_pct, use_container_width=True)

    # ---------- ML READINESS SCORE NON-INTERACTIVE ----------
    completeness = round(100 - missing_pct.mean(), 2)
    duplicate_pct = round(df.duplicated().mean() * 100, 2)
    ml_ready_score = round(
        (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
        (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
        (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15), 2
    )

    st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
    st.progress(ml_ready_score / 100)  # non-interactive
    st.text(f"ML Readiness Score: {ml_ready_score}/100")
    st.markdown("- Regression: Linear Regression, Random Forest, Gradient Boosting")
    st.markdown("- Classification: Decision Tree, Random Forest, XGBoost, Logistic Regression")
    st.markdown("- Unsupervised/Clustering: KMeans, DBSCAN, Hierarchical Clustering")
