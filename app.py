import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file
import os
from fpdf import FPDF   # ✅ added

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate interactive documentation.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

# ---------- PDF FUNCTION (ADDED ONLY) ----------
def generate_pdf(df, result, numeric_cols, missing_pct, ml_ready_score):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Auto-Documenter Report", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.ln(4)
    pdf.cell(0, 8, f"Rows: {result['summary']['rows']}", ln=True)
    pdf.cell(0, 8, f"Columns: {result['summary']['columns']}", ln=True)

    pdf.ln(4)
    pdf.cell(0, 8, "Column Datatypes:", ln=True)
    for col, dtype in df.dtypes.items():
        pdf.cell(0, 7, f"{col} : {dtype}", ln=True)

    pdf.ln(4)
    pdf.cell(0, 8, "Min / Avg / Max:", ln=True)
    for col in numeric_cols:
        pdf.cell(
            0, 7,
            f"{col} → Min:{df[col].min()} Avg:{round(df[col].mean(),2)} Max:{df[col].max()}",
            ln=True
        )

    pdf.ln(4)
    pdf.cell(0, 8, "Missing Values %:", ln=True)
    for col, val in missing_pct.items():
        pdf.cell(0, 7, f"{col}: {val}%", ln=True)

    pdf.ln(4)
    pdf.cell(0, 8, f"ML Readiness Score: {ml_ready_score}/100", ln=True)

    path = "Auto_Documenter_Report.pdf"
    pdf.output(path)
    return path

# ---------- MAIN ----------
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
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            result = analyze_file(temp_path)

        st.success("✅ Documentation generated successfully!")

        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", result['numeric_count'])
        c4.metric("Categorical Columns", result['categorical_count'])

        st.markdown("## 📌 Column Datatypes")
        st.dataframe(
            pd.DataFrame(df.dtypes.astype(str), columns=["Data Type"]),
            use_container_width=True
        )

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
        for col in numeric_cols:
            st.markdown(f"**{col}**")
            st.markdown(
                f"Min: {df[col].min()} | Avg: {round(df[col].mean(),2)} | Max: {df[col].max()}"
            )

        with st.expander("📊 Column Graphs (Interactive)"):
            for col in numeric_cols:
                st.plotly_chart(px.line(df, y=col), use_container_width=True)

        if len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Heatmap (Interactive)"):
                corr = df[numeric_cols].corr()
                st.plotly_chart(px.imshow(corr, text_auto=True), use_container_width=True)

        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().sum() / len(df) * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        completeness = round(100 - missing_pct.mean(), 2)
        duplicate_pct = round(df.duplicated().mean() * 100, 2)
        ml_ready_score = round(
            (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
            (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.3),
            2
        )

        st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
        st.markdown(f"**ML Readiness Score:** {ml_ready_score}/100")

        # ---------- PDF DOWNLOAD (ONLY ADDITION) ----------
        if st.button("📄 Download PDF Report", use_container_width=True):
            pdf_path = generate_pdf(df, result, numeric_cols, missing_pct, ml_ready_score)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇ Click to Download",
                    f,
                    file_name="Auto_Documenter_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
