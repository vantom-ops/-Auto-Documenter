import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file
import os
from datetime import datetime

# PDF watermark (added safely)
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- CSS ----------
st.markdown("""
<style>
.main .block-container {
    padding-bottom: 220px !important;
}

/* Footer */
.footer-container {
    position: fixed !important;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: rgba(14, 17, 23, 0.95);
    padding: 25px 0;
    text-align: center;
    z-index: 999999;
    border-top: 1px solid rgba(255, 75, 75, 0.4);
}

/* Hide footer on mobile */
@media (max-width: 768px) {
    .footer-container {
        display: none !important;
    }
}

/* Download button */
div.stDownloadButton {
    display: flex !important;
    justify-content: center !important;
}

div.stDownloadButton > button {
    width: 92% !important;
    height: 80px !important;
    background-color: transparent !important;
    color: #ff4b4b !important;
    font-size: 22px !important;
    font-weight: 900 !important;
    letter-spacing: 2.5px;
    border: 2px solid #ff4b4b !important;
    border-radius: 14px !important;
    transition: 0.3s;
}

div.stDownloadButton > button:hover {
    background-color: rgba(255, 75, 75, 0.15) !important;
    color: white !important;
    box-shadow: 0px 0px 25px rgba(255, 75, 75, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

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

    # ---------- GENERATE ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result
            st.rerun()

    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']

        if "error" in result:
            st.error(result["error"])
            st.stop()

        st.success("✅ Documentation generated successfully!")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", result['numeric_count'])
        c4.metric("Categorical Columns", result['categorical_count'])

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            st.plotly_chart(fig, use_container_width=True)

# ---------- PDF WATERMARK (ADD-ON ONLY) ----------
def add_watermark(input_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    c.setFont("Helvetica-Bold", 36)
    c.setFillGray(0.85, 0.3)
    c.saveState()
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, "AUTO-DOCUMENTER")
    c.restoreState()
    c.save()

    packet.seek(0)
    watermark = PdfReader(packet).pages[0]

    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# ---------- FOOTER ----------
pdf_path = "output/report.pdf"
watermarked_pdf = "output/report_watermarked.pdf"

if os.path.exists(pdf_path):
    add_watermark(pdf_path, watermarked_pdf)

    year = datetime.now().year

    st.markdown('<div class="footer-container">', unsafe_allow_html=True)

    with open(watermarked_pdf, "rb") as f:
        st.download_button(
            "📥 DOWNLOAD PDF REPORT",
            f,
            "Documentation_Report.pdf",
            "application/pdf"
        )

    st.markdown(f"""
    <div style="margin-top:18px; font-size:13px; color:#bbbbbb; line-height:1.6;">
        © {year} Auto-Documenter<br>
        Apache License – Version 2.0, January 2004<br>
        <a href="http://www.apache.org/licenses/" target="_blank" style="color:#ff4b4b;">Apache License</a><br>
        <a href="https://github.com/your-username/auto-documenter" target="_blank" style="color:#ff4b4b;">
            GitHub Repository
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
