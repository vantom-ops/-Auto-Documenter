import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file
import os
from fpdf import FPDF
import tempfile

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

    # ---------- GENERATE METRICS ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        st.success("✅ Documentation generated successfully!")

        # ---------- DATA ----------
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        # ---------- DATASET METRICS ----------
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", len(numeric_cols))
        c4.metric("Categorical Columns", len(categorical_cols))

        # ---------- COLUMN DATATYPES ----------
        st.markdown("## 📌 Column Datatypes")
        dtype_df = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str)
        })
        st.dataframe(dtype_df, use_container_width=True)

        # ---------- MIN / AVG / MAX ----------
        st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
        stats_data = []
        for col in numeric_cols:
            stats_data.append({
                "Column": col,
                "Min": df[col].min(),
                "Avg": round(df[col].mean(), 2),
                "Max": df[col].max()
            })
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)

        # ---------- COLUMN GRAPHS ----------
        st.markdown("## 📊 Column Graphs (Interactive)")
        graph_images = []
        for col in numeric_cols:
            fig = px.line(df, y=col, title=f"{col} Trend")
            st.plotly_chart(fig, use_container_width=True)

            img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            fig.write_image(img_path)
            graph_images.append(img_path)

        # ---------- CORRELATION ----------
        st.markdown("## 🔥 Correlation Heatmap")
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().round(2)
            st.dataframe(corr, use_container_width=True)
            fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            st.plotly_chart(fig_corr, use_container_width=True)

            corr_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            fig_corr.write_image(corr_img)
        else:
            corr_img = None

        # ---------- MISSING ----------
        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().mean() * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        # ---------- ML READINESS ----------
        completeness = round(100 - missing_pct.mean(), 2)
        duplicate_pct = round(df.duplicated().mean() * 100, 2)
        ml_ready_score = round(
            (completeness * 0.4) +
            ((100 - duplicate_pct) * 0.3) +
            (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
            (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15),
            2
        )

        st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
        st.markdown(f"""
        <div style="background:linear-gradient(to right,#ff4b4b,#ffd700,#00cc66);
        height:30px;border-radius:6px;position:relative;">
        <div style="position:absolute;left:{ml_ready_score}%;
        transform:translateX(-50%);font-weight:bold;">
        {ml_ready_score}/100
        </div></div>
        """, unsafe_allow_html=True)

        # ---------- PDF GENERATION ----------
        def generate_pdf():
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Auto-Documenter Report", ln=True)

            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, f"Rows: {df.shape[0]} | Columns: {df.shape[1]}", ln=True)

            pdf.ln(5)
            pdf.cell(0, 8, "Column Statistics:", ln=True)
            for _, r in stats_df.iterrows():
                pdf.cell(0, 8, f"{r['Column']} → Min:{r['Min']} Avg:{r['Avg']} Max:{r['Max']}", ln=True)

            pdf.ln(5)
            pdf.cell(0, 8, f"ML Readiness Score: {ml_ready_score}/100", ln=True)

            for img in graph_images:
                pdf.add_page()
                pdf.image(img, w=180)

            if corr_img:
                pdf.add_page()
                pdf.image(corr_img, w=180)

            pdf_path = "Auto_Documenter_Report.pdf"
            pdf.output(pdf_path)
            return pdf_path

        # ---------- BIG DOWNLOAD BUTTON ----------
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 DOWNLOAD PDF REPORT", use_container_width=True):
            pdf_file = generate_pdf()
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="⬇ Click to Download PDF",
                    data=f,
                    file_name="Auto_Documenter_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
