import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from parser import analyze_file
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

st.title("📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate **interactive documentation**.")
st.divider()

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
    else:
        df = pd.read_json(uploaded_file)

    st.subheader("🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- GENERATE ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Analyzing dataset..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)

        st.success("✅ Documentation generated")

        # ---------- DATASET METRICS ----------
        st.subheader("📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", df.shape[0])
        c2.metric("Columns", df.shape[1])

        # ---------- FIX YEAR.MONTH ISSUE ----------
        for col in df.columns:
            if df[col].dtype in ["float64", "int64"]:
                sample = df[col].dropna().astype(str).head(5)
                if sample.str.match(r"\d{4}\.\d{1,2}").all():
                    try:
                        df[col] = pd.to_datetime(df[col].astype(str), format="%Y.%m")
                    except:
                        pass

        # ---------- COLUMN DATATYPES ----------
        st.subheader("📌 Column Datatypes")
        dtype_df = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str)
        })
        st.dataframe(dtype_df, use_container_width=True)

        # ---------- NUMERIC COLUMN FILTERING ----------
        numeric_cols = []
        for col in df.select_dtypes(include=np.number).columns:
            if df[col].nunique() > 1 and df[col].isna().mean() < 0.9:
                numeric_cols.append(col)

        c3.metric("Numeric Columns", len(numeric_cols))
        c4.metric("Categorical Columns", df.shape[1] - len(numeric_cols))

        # ---------- MIN / AVG / MAX ----------
        st.subheader("📈 Column Statistics (Min / Avg / Max)")
        for col in numeric_cols:
            min_v = df[col].min()
            avg_v = round(df[col].mean(), 2)
            max_v = df[col].max()

            st.markdown(f"**{col}**")
            st.markdown(
                f"""
                <div style="display:flex;height:22px;border-radius:6px;overflow:hidden;">
                    <div style="width:33%;background:#ff4b4b;"></div>
                    <div style="width:34%;background:#ffd700;"></div>
                    <div style="width:33%;background:#2ecc71;"></div>
                </div>
                <div style="margin-bottom:12px;">
                    Min: {min_v} | Avg: {avg_v} | Max: {max_v}
                </div>
                """,
                unsafe_allow_html=True
            )

        # ---------- COLUMN GRAPHS ----------
        with st.expander("📊 Column Graphs"):
            for col in numeric_cols:
                fig = px.line(df, y=col, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION HEATMAP ----------
        if len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Heatmap"):
                corr = df[numeric_cols].corr().round(2)
                corr = corr.fillna(0)

                st.dataframe(corr, use_container_width=True)

                fig = px.imshow(
                    corr,
                    text_auto=True,
                    color_continuous_scale="RdBu_r",
                    title="Correlation Heatmap"
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- ML READINESS ----------
        missing_pct = df.isna().mean() * 100
        completeness = 100 - missing_pct.mean()
        duplicate_pct = df.duplicated().mean() * 100

        ml_score = round(
            (completeness * 0.4)
            + ((100 - duplicate_pct) * 0.3)
            + (len(numeric_cols) / df.shape[1] * 100 * 0.3),
            2
        )

        st.subheader("🤖 ML Readiness Score & Suggested Algorithms")
        st.markdown(
            f"""
            <div style="background:linear-gradient(to right,#ff4b4b,#ffd700,#2ecc71);
                        height:28px;border-radius:6px;position:relative;">
                <div style="position:absolute;left:{ml_score}%;
                            transform:translateX(-50%);
                            font-weight:bold;color:black;">
                    {ml_score}/100
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            **Suggested Algorithms**
            - Regression: Linear Regression, Random Forest, Gradient Boosting  
            - Classification: Logistic Regression, Decision Tree, Random Forest  
            - Unsupervised: KMeans, DBSCAN, Hierarchical Clustering
            """
        )
