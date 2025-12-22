import streamlit as st
import pandas as pd
import numpy as np
from parser import analyze_file  # your phraiser.py or parser.py
import io
import os
from textwrap import wrap

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate documentation and PDF report.")
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

    # ---------- GENERATE METRICS & PDF ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            # Save temp file for parser
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call parser
            result = analyze_file(temp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        # ---------- DISPLAY METRICS ----------
        st.success("✅ Documentation generated successfully!")

        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", result['numeric_count'])
        c4.metric("Categorical Columns", result['categorical_count'])

        st.markdown("## 📌 Column Datatypes")
        col_types = pd.Series(df.dtypes).astype(str)
        for col, dtype in col_types.items():
            st.write(f"- **{col}**: {dtype}")

        # ---------- PDF REPORT ----------
        st.markdown("## 📝 PDF Report")
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Auto-Documenter Report", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Dataset Metrics:", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 7, f"Rows: {result['summary']['rows']}", ln=True)
        pdf.cell(0, 7, f"Columns: {result['summary']['columns']}", ln=True)
        pdf.cell(0, 7, f"Numeric Columns: {result['numeric_count']}", ln=True)
        pdf.cell(0, 7, f"Categorical Columns: {result['categorical_count']}", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Column Datatypes:", ln=True)
        pdf.set_font("Arial", "", 12)
        for col, dtype in col_types.items():
            line = f"{col}: {dtype}"
            wrapped = wrap(line, width=90)
            for wl in wrapped:
                pdf.multi_cell(0, 6, wl)
        pdf.ln(5)

        # ---------- Column Min/Max/Avg ----------
        if 'dataframe' in result:
            numeric_cols = result['dataframe'].select_dtypes(include=[np.number]).columns
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, "Column Min/Max/Avg:", ln=True)
            pdf.set_font("Arial", "", 12)
            for col in numeric_cols:
                min_val = result['dataframe'][col].min()
                max_val = result['dataframe'][col].max()
                avg_val = round(result['dataframe'][col].mean(), 2)
                line = f"{col}: Min={min_val}, Max={max_val}, Avg={avg_val}"
                wrapped = wrap(line, width=90)
                for wl in wrapped:
                    pdf.multi_cell(0, 6, wl)
            pdf.ln(5)

        # ---------- ML Readiness & Suggested Algorithms ----------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "ML Readiness & Suggested Algorithms:", ln=True)
        pdf.set_font("Arial", "", 12)
        ml_score = round(result.get('completeness', 0) * 0.7 + 0.3 * (result.get('numeric_ratio',0)), 2)
        line = f"ML Readiness Score: {ml_score} / 100"
        pdf.multi_cell(0, 6, line)

        suggested_algos = ["Regression: Linear, Random Forest, Gradient Boosting",
                           "Classification: Decision Tree, Random Forest, XGBoost",
                           "Clustering: KMeans, DBSCAN, Hierarchical"]
        pdf.multi_cell(0,6, "Suggested Algorithms:")
        for algo in suggested_algos:
            wrapped = wrap(algo, width=90)
            for wl in wrapped:
                pdf.multi_cell(0,6, f"- {wl}")
        pdf.ln(5)

        # ---------- Correlations & Warnings ----------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Warnings / Correlations:", ln=True)
        pdf.set_font("Arial", "", 12)
        warnings = result.get('warnings', [])
        if warnings:
            for w in warnings:
                wrapped = wrap(f"Warning: {w}", width=90)
                for wl in wrapped:
                    pdf.multi_cell(0, 6, wl)
        else:
            pdf.multi_cell(0, 6, "No major warnings detected.")

        # ---------- SAVE PDF ----------
        os.makedirs("output", exist_ok=True)
        pdf_path = os.path.join("output", "Auto_Documenter_Report.pdf")
        pdf.output(pdf_path)

        # ---------- DOWNLOAD BUTTON ----------
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="📥 Download Full PDF Report",
            data=pdf_bytes,
            file_name="Auto_Documenter_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
