import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file
import os
import numpy as np
from fpdf import FPDF
import io
import base64

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
            (min(len(numeric_cols)/cols,1)*100*0.15) +
            (min(len(categorical_cols)/cols,1)*100*0.15),
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
        with st.expander("📌 Column Statistics (Min, Max, Avg)", expanded=False):
            grid = st.columns(3)
            for i, col in enumerate(numeric_cols):
                col_min = df_preview[col].min()
                col_max = df_preview[col].max()
                col_avg = round(df_preview[col].mean(), 2)
                with grid[i % 3]:
                    st.markdown(
                        f"""
                        <div style="padding:15px;border-radius:14px;
                        background:linear-gradient(135deg,#1d2671,#c33764);
                        color:white;">
                        <h4>{col}</h4>
                        <p>⬇ Min: {col_min}</p>
                        <p>⬆ Max: {col_max}</p>
                        <p>📊 Avg: {col_avg}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

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
            for i in corr.columns:
                for j in corr.columns:
                    if i != j and abs(corr.loc[i,j]) > 0.7:
                        strong_corrs.append((i,j,corr.loc[i,j]))

        # ---------- PDF REPORT ----------
        st.markdown("## 📝 Full PDF Report")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "", 12)

        pdf.cell(0, 10, "Auto-Documenter Report", ln=True, align="C")
        pdf.ln(5)
        pdf.multi_cell(0, 6, f"Rows: {rows}\nColumns: {cols}\nNumeric: {len(numeric_cols)}\nCategorical: {len(categorical_cols)}")
        pdf.ln(3)
        pdf.multi_cell(0,6,f"Data Health Score: {health_score} / 100")
        pdf.ln(2)
        pdf.multi_cell(0,6,"Column Statistics (Min/Max/Avg):")
        for col in numeric_cols:
            pdf.multi_cell(0,6,f"- {col}: Min={df_preview[col].min()}, Max={df_preview[col].max()}, Avg={round(df_preview[col].mean(),2)}")
        pdf.ln(2)
        if strong_corrs:
            pdf.multi_cell(0,6,"Strong Correlations:")
            for a,b,v in strong_corrs:
                pdf.multi_cell(0,6,f"- {a} ↔ {b}: {v}")

        # Export PDF to BytesIO
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        st.download_button(
            label="📥 Download Full PDF Report",
            data=pdf_buffer,
            file_name="Auto_Documenter_Full_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
