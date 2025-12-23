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
def convert_year_month(series):
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
        st.error("Unsupported file type!")
        st.stop()

    # ---------- FIX YYYY.MM ----------
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = convert_year_month(df[col])

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)

        if "error" in result:
            st.error(result["error"])
            st.stop()

        st.success("✅ Documentation generated successfully!")

        # ---------- METRICS ----------
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", df.shape[0])
        c2.metric("Columns", df.shape[1])
        c3.metric("Numeric Columns", df.select_dtypes(include=np.number).shape[1])
        c4.metric("Categorical Columns", df.select_dtypes(exclude=np.number).shape[1])

        # ---------- DATATYPES ----------
        st.markdown("## 📌 Column Datatypes")
        type_df = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str)
        })
        st.dataframe(type_df, use_container_width=True)

        # ---------- FILTER BAD COLUMNS ----------
        numeric_cols = [
            c for c in df.select_dtypes(include=np.number).columns
            if df[c].nunique(dropna=True) > 1 and df[c].isna().mean() < 0.9
        ]

        categorical_cols = [
            c for c in df.select_dtypes(exclude=np.number).columns
            if df[c].isna().mean() < 0.9
        ]

        # ---------- MIN / AVG / MAX ----------
        st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
        for col in numeric_cols:
            min_val = round(df[col].min(), 2)
            avg_val = round(df[col].mean(), 2)
            max_val = round(df[col].max(), 2)

            st.markdown(f"**{col}**")
            st.markdown(f"""
            <div style="display:flex; gap:6px; margin-bottom:4px;">
                <div style="flex:1; background:#ff4b4b; height:18px;"></div>
                <div style="flex:1; background:#ffd700; height:18px;"></div>
                <div style="flex:1; background:#00cc66; height:18px;"></div>
            </div>
            <div style="margin-bottom:12px;">
                Min: {min_val} | Avg: {avg_val} | Max: {max_val}
            </div>
            """, unsafe_allow_html=True)

        # ---------- GRAPHS ----------
        with st.expander("📊 Column Graphs (Interactive)"):
            for col in numeric_cols:
                fig = px.line(df, y=col, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION ----------
        if len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Heatmap (Interactive)"):
                corr = df[numeric_cols].corr().round(2)
                st.dataframe(corr, use_container_width=True)
                fig = px.imshow(
                    corr,
                    text_auto=True,
                    color_continuous_scale="RdBu_r"
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- MISSING VALUES ----------
        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().mean() * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        # ---------- ML READINESS ----------
        completeness = 100 - missing_pct.mean()
        duplicate_pct = df.duplicated().mean() * 100

        ml_ready_score = round(
            completeness * 0.4 +
            (100 - duplicate_pct) * 0.3 +
            min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15 +
            min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15,
            2
        )

        st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
        st.markdown(f"""
        <div style="background:linear-gradient(to right,#ff4b4b,#ffd700,#00cc66);
                    height:28px; border-radius:6px; position:relative;">
            <div style="position:absolute; left:{ml_ready_score}%;
                        transform:translateX(-50%);
                        font-weight:bold; color:black;">
                {ml_ready_score}/100
            </div>
        </div>

        <div style="margin-top:8px;">
        <b>Suggested Algorithms:</b><br>
        • Regression → Linear Regression, Random Forest, Gradient Boosting<br>
        • Classification → Logistic Regression, Random Forest, XGBoost<br>
        • Unsupervised → KMeans, DBSCAN
        </div>
        """, unsafe_allow_html=True)
