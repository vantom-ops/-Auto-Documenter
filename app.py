import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
from fpdf import FPDF
import io
from phraiser import analyze_file

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
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.DataFrame()

    if not df.empty:
        st.markdown("## 🔍 File Preview")
        st.dataframe(df.head(preview_rows), use_container_width=True)

        # ---------- METRICS ----------
        rows, cols = df.shape
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        completeness = round(df.notna().sum().sum() / (rows * cols) * 100, 2)
        duplicate_pct = round(df.duplicated().sum() / rows * 100, 2)

        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", rows)
        c2.metric("Columns", cols)
        c3.metric("Numeric", len(numeric_cols))
        c4.metric("Categorical", len(categorical_cols))

        # ---------- WARNINGS ----------
        st.markdown("## ⚠ Warnings")
        high_missing_cols = []
        for col in df.columns:
            miss_pct = df[col].isna().mean() * 100
            if miss_pct > 50:
                high_missing_cols.append((col, round(miss_pct, 2)))
                st.warning(f"{col} has {round(miss_pct,2)}% missing values")
        if not high_missing_cols:
            st.success("No major data quality issues detected")

        # ---------- ML Readiness Score ----------
        ml_score = round(
            (completeness * 0.4) +
            ((100 - duplicate_pct) * 0.3) +
            (min(len(numeric_cols)/cols,1)*100*0.15) +
            (min(len(categorical_cols)/cols,1)*100*0.15),
            2
        )
        st.markdown("## 🤖 ML Readiness")
        st.metric("ML Readiness Score", f"{ml_score}/100")

        # ---------- Suggested Algorithms ----------
        st.markdown("### Suggested Algorithms")
        if numeric_cols:
            st.write("- Regression: Linear Regression, Random Forest Regressor, Gradient Boosting")
        if categorical_cols:
            st.write("- Classification: Decision Tree, Random Forest Classifier, XGBoost, Logistic Regression")
        if numeric_cols and not categorical_cols:
            st.write("- Clustering: KMeans, DBSCAN, Hierarchical Clustering")

        # ---------- CORRELATION ----------
        strong_corrs = []
        if show_corr and len(numeric_cols) > 1:
            st.markdown("## 🔥 Correlation Analysis")
            corr = df[numeric_cols].corr().round(3)
            fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            st.plotly_chart(fig, use_container_width=True)
            for i in corr.columns:
                for j in corr.columns:
                    if i != j and abs(corr.loc[i,j]) > 0.7:
                        strong_corrs.append((i,j,corr.loc[i,j]))

        # ---------- COLUMN STATS + GRAPHS ----------
        st.markdown("## 📌 Column Statistics (Min/Max/Avg)")
        column_data = []
        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            col_avg = round(df[col].mean(),2)
            column_data.append((col, col_min, col_max, col_avg))
            st.write(f"{col}: Min={col_min}, Max={col_max}, Avg={col_avg}")
            if show_graphs:
                fig = px.line(df, y=col, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- PDF REPORT ----------
        st.markdown("## 📝 Generate Full PDF")
        if st.button("⬇️ Download Full PDF Report", key="pdf_button"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Auto-Documenter Report", ln=True, align="C")
            pdf.ln(5)
            pdf.set_font("Arial", "", 12)

            pdf.cell(0, 8, f"Rows: {rows}", ln=True)
            pdf.cell(0, 8, f"Columns: {cols}", ln=True)
            pdf.cell(0, 8, f"Numeric Columns: {len(numeric_cols)}", ln=True)
            pdf.cell(0, 8, f"Categorical Columns: {len(categorical_cols)}", ln=True)
            pdf.cell(0, 8, f"ML Readiness Score: {ml_score}/100", ln=True)
            pdf.ln(3)

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Column Statistics", ln=True)
            pdf.set_font("Arial", "", 12)
            for col, mn, mx, avg in column_data:
                pdf.multi_cell(0, 7, f"{col}: Min={mn}, Max={mx}, Avg={avg}")

            if strong_corrs:
                pdf.ln(3)
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Strong Correlations (>0.7)", ln=True)
                pdf.set_font("Arial", "", 12)
                for a,b,v in strong_corrs:
                    pdf.cell(0, 7, f"{a} ↔ {b}: {v}", ln=True)

            if high_missing_cols:
                pdf.ln(3)
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Warnings", ln=True)
                pdf.set_font("Arial", "", 12)
                for col, pct in high_missing_cols:
                    pdf.cell(0, 7, f"{col} missing: {pct}%", ln=True)

            pdf_bytes = io.BytesIO()
            pdf.output(pdf_bytes)
            pdf_bytes.seek(0)

            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name="Auto_Documenter_Full_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
