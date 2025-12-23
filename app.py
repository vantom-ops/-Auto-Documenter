import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from parser import analyze_file

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate interactive documentation.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

# ---------- HELPERS ----------
def fix_year_month(series):
    try:
        s = series.astype(str)
        if s.str.match(r"^\d{4}\.\d{1,2}$").all():
            return pd.to_datetime(s, format="%Y.%m")
    except:
        pass
    return series

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type")
        st.stop()

    # Fix YYYY.MM columns
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = fix_year_month(df[col])

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            analyze_file(temp_path)

        st.success("✅ Documentation generated successfully!")

        # ---------- DATASET METRICS ----------
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", df.shape[0])
        c2.metric("Columns", df.shape[1])
        c3.metric("Numeric Columns", df.select_dtypes(include=np.number).shape[1])
        c4.metric("Categorical Columns", df.select_dtypes(exclude=np.number).shape[1])

        # ---------- COLUMN DATATYPES ----------
        st.markdown("## 📌 Column Datatypes")
        st.dataframe(
            pd.DataFrame({
                "Column": df.columns,
                "Data Type": df.dtypes.astype(str)
            }),
            use_container_width=True
        )

        # ---------- VALID NUMERIC COLUMNS ----------
        numeric_cols = []
        for col in df.select_dtypes(include=np.number).columns:
            if df[col].isna().mean() < 0.9 and df[col].nunique(dropna=True) > 1:
                numeric_cols.append(col)

        # ---------- MIN / AVG / MAX ----------
        st.markdown("## 📈 Min / Avg / Max (All Numeric Columns)")
        for col in numeric_cols:
            min_val = round(df[col].min(), 3)
            avg_val = round(df[col].mean(), 3)
            max_val = round(df[col].max(), 3)

            st.markdown(f"**{col}**")
            st.markdown(f"""
            <div style="display:flex; gap:6px;">
                <div style="flex:1; height:18px; background:#ff4b4b;"></div>
                <div style="flex:1; height:18px; background:#ffd700;"></div>
                <div style="flex:1; height:18px; background:#00cc66;"></div>
            </div>
            <div style="margin-bottom:10px;">
                Min: {min_val} | Avg: {avg_val} | Max: {max_val}
            </div>
            """, unsafe_allow_html=True)

        # ---------- COLUMN GRAPHS ----------
        with st.expander("📊 Column Graphs (Interactive)"):
            for col in numeric_cols:
                fig = px.line(df, y=col, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION HEATMAP ----------
        if len(numeric_cols) >= 2:
            with st.expander("🔥 Correlation Heatmap (Interactive)"):
                corr = df[numeric_cols].corr().round(2)
                st.dataframe(corr, use_container_width=True)
                fig = px.imshow(
                    corr,
                    text_auto=True,
                    color_continuous_scale="RdBu_r"
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- ML READINESS ----------
        missing_pct = df.isna().mean() * 100
        completeness = 100 - missing_pct.mean()
        duplicate_pct = df.duplicated().mean() * 100

        ml_score = round(
            completeness * 0.4 +
            (100 - duplicate_pct) * 0.3 +
            min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.3,
            2
        )

        st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
        st.markdown(f"""
        <div style="background:linear-gradient(to right,#ff4b4b,#ffd700,#00cc66);
                    height:28px; border-radius:6px; position:relative;">
            <div style="position:absolute; left:{ml_score}%;
                        transform:translateX(-50%);
                        font-weight:bold;">
                {ml_score}/100
            </div>
        </div>

        <div style="margin-top:8px;">
        <b>Suggested Algorithms</b><br>
        Regression → Linear, Random Forest, XGBoost<br>
        Classification → Logistic, Random Forest<br>
        Clustering → KMeans, DBSCAN
        </div>
        """, unsafe_allow_html=True)
