import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file
import os
import numpy as np

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)
    show_graphs = st.checkbox("Show Column Graphs", True)
    show_corr = st.checkbox("Show Correlation Analysis", True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"]
)

if uploaded_file:

    # ---------- LOAD FILE ----------
    if uploaded_file.name.endswith(".csv"):
        df_preview = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df_preview = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df_preview = pd.read_json(uploaded_file)
    else:
        df_preview = pd.DataFrame()

    # ---------- FILE PREVIEW ----------
    if not df_preview.empty:
        st.markdown("## 🔍 File Preview")
        st.dataframe(df_preview.head(preview_rows), use_container_width=True)

    # ---------- GENERATE ----------
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

        # ---------- BASIC METRICS ----------
        rows, cols = df_preview.shape
        numeric_cols = df_preview.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df_preview.select_dtypes(exclude=np.number).columns.tolist()

        completeness = round((df_preview.notna().sum().sum() / (rows * cols)) * 100, 2)
        duplicate_pct = round((df_preview.duplicated().sum() / rows) * 100, 2)

        # ---------- METRIC CARDS ----------
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", rows)
        c2.metric("Columns", cols)
        c3.metric("Numeric", len(numeric_cols))
        c4.metric("Categorical", len(categorical_cols))

        # ---------- OVERALL DATA HEALTH SCORE ----------
        health_score = round(
            (completeness * 0.5) +
            ((100 - duplicate_pct) * 0.2) +
            (min(len(numeric_cols) / cols, 1) * 100 * 0.15) +
            (min(len(categorical_cols) / cols, 1) * 100 * 0.15),
            2
        )

        st.markdown("## 🏥 Overall Data Health Score")
        st.progress(health_score / 100)
        st.metric("Health Score", f"{health_score} / 100")

        # ---------- WARNINGS ----------
        st.markdown("## ⚠ Data Health Warnings")
        high_missing_cols = []
        for col in df_preview.columns:
            miss = df_preview[col].isna().mean() * 100
            if miss > 50:
                high_missing_cols.append(col)
                st.warning(f"{col} has {round(miss,2)}% missing values")

        if not high_missing_cols:
            st.success("🎉 No major data quality issues detected")

        # ---------- COLUMN STATISTICS ----------
        with st.expander("📌 Column Statistics", expanded=False):
            grid = st.columns(3)
            i = 0
            for col in numeric_cols:
                with grid[i % 3]:
                    st.markdown(
                        f"""
                        <div style="padding:15px;border-radius:14px;
                        background:linear-gradient(135deg,#1d2671,#c33764);
                        color:white;">
                        <h4>{col}</h4>
                        <p>⬇ Min: {df_preview[col].min()}</p>
                        <p>⬆ Max: {df_preview[col].max()}</p>
                        <p>📊 Avg: {round(df_preview[col].mean(),2)}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                i += 1

        # ---------- COLUMN GRAPHS ----------
        if show_graphs and numeric_cols:
            with st.expander("📈 Column Graphs", expanded=False):
                for col in numeric_cols:
                    fig = px.line(df_preview, y=col, title=f"{col} Trend")
                    st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION ----------
        strong_corrs = []
        if show_corr and len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Analysis", expanded=False):
                corr = df_preview[numeric_cols].corr().round(3)
                fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("📋 Correlation Table", expanded=False):
                st.dataframe(corr, use_container_width=True)

            for i in corr.columns:
                for j in corr.columns:
                    if i != j and abs(corr.loc[i, j]) > 0.7:
                        strong_corrs.append((i, j, corr.loc[i, j]))

        # ---------- STRONG CORRELATIONS ----------
        if strong_corrs:
            with st.expander("🔗 Strong Correlations (> 0.7)", expanded=False):
                for a, b, v in strong_corrs:
                    st.warning(f"{a} ↔ {b} : {v}")

        # ---------- RADAR CHART ----------
        st.markdown("## 🕸 Data Health Radar")
        radar_labels = ["Completeness", "Low Missing", "Low Duplicates", "Numeric Balance", "Categorical Balance"]
        radar_values = [
            completeness,
            100 - (len(high_missing_cols) / cols * 100 if cols else 0),
            100 - duplicate_pct,
            min((len(numeric_cols) / cols) * 100, 100),
            min((len(categorical_cols) / cols) * 100, 100)
        ]

        radar_fig = go.Figure(
            go.Scatterpolar(r=radar_values, theta=radar_labels, fill='toself')
        )
        radar_fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])))
        st.plotly_chart(radar_fig, use_container_width=True)

        # ---------- AUTO INSIGHTS ----------
        st.markdown("## 🤖 Auto Insights")
        insights = []
        recommendations = []

        if completeness < 80:
            insights.append("Dataset has low completeness.")
            recommendations.append("Consider imputing or removing missing values.")

        if strong_corrs:
            insights.append("Strong correlations detected.")
            recommendations.append("Check multicollinearity before modeling.")

        if duplicate_pct > 5:
            recommendations.append("Remove duplicate rows to improve data quality.")

        for i in insights:
            st.info(i)

        st.markdown("### 🛠 Auto Recommendations")
        for r in recommendations:
            st.success(r)

        # ---------- BIG DOWNLOAD PDF ----------
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            st.markdown("## 📥 Export Report")
            st.download_button(
                label="⬇️ DOWNLOAD FULL PDF REPORT",
                data=open(pdf_path, "rb").read(),
                file_name="Auto_Documenter_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
