import streamlit as st
import pandas as pd
import numpy as np
import os
from parser import analyze_file  # your phraiser.py or parser.py
from fpdf import FPDF
import matplotlib.pyplot as plt
import seaborn as sns

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate documentation and PDF report.")
st.markdown("---")

with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

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

    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            # Save temp file for parser
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        st.success("✅ Documentation generated successfully!")

        # ---------- DISPLAY METRICS ----------
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

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        # ---------- PDF REPORT ----------
        st.markdown("## 📝 PDF Report")
        os.makedirs("output", exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Auto-Documenter Report", ln=True, align="C")
        pdf.ln(5)

        # Column datatypes
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Column Datatypes", ln=True)
        pdf.set_font("Arial", "", 12)
        for col, dtype in col_types.items():
            pdf.multi_cell(0, 6, f"{col}: {dtype}")
        pdf.ln(5)

        # Dataset metrics
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Dataset Metrics", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(
            0, 6,
            f"Rows: {result['summary']['rows']}\n"
            f"Columns: {result['summary']['columns']}\n"
            f"Numeric Columns: {result['numeric_count']}\n"
            f"Categorical Columns: {result['categorical_count']}"
        )
        pdf.ln(5)

        # Graphs: Min/Max/Avg
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Column Graphs (Min/Max/Avg)", ln=True)
        pdf.set_font("Arial", "", 12)

        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            col_avg = round(df[col].mean(), 2)

            # Create line graph
            plt.figure(figsize=(6, 3))
            plt.plot(df[col], marker='o', linestyle='-', label=col)
            plt.axhline(col_min, color='red', linestyle='--', label=f'Min={col_min}')
            plt.axhline(col_max, color='green', linestyle='--', label=f'Max={col_max}')
            plt.axhline(col_avg, color='blue', linestyle='-.', label=f'Avg={col_avg}')
            plt.title(f"{col} Min/Max/Avg")
            plt.tight_layout()
            plt.legend()
            graph_file = f"output/{col}_graph.png"
            plt.savefig(graph_file)
            plt.close()

            pdf.multi_cell(0, 6, f"{col}: Min={col_min}, Max={col_max}, Avg={col_avg}")
            pdf.image(graph_file, x=10, w=180)
            pdf.ln(5)

        # Correlation heatmap
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            plt.figure(figsize=(6, 5))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
            plt.title("Correlation Heatmap")
            plt.tight_layout()
            heatmap_file = "output/correlation_heatmap.png"
            plt.savefig(heatmap_file)
            plt.close()

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, "Correlation Heatmap", ln=True)
            pdf.image(heatmap_file, x=10, w=180)
            pdf.ln(5)

        # Save PDF
        pdf_path = os.path.join("output", "report.pdf")
        pdf.output(pdf_path)

        # Download button
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name="Auto_Documenter_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("PDF generation failed.")
