import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file  # your phraiser.py / parser.py
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# --- CSS FOR TRANSPARENT HORIZONTAL BUTTON ---
st.markdown("""
    <style>
    .main .block-container {
        padding-bottom: 200px !important;
    }
    
    /* Fixed Footer Wrapper */
    .footer-container {
        position: fixed !important;
        left: 0 !important;
        bottom: 0 !important;
        width: 100% !important;
        background-color: rgba(14, 17, 23, 0.85) !important; /* Semi-transparent dark bg */
        padding: 30px 0 !important;
        text-align: center !important;
        z-index: 999999 !important;
        border-top: 1px solid rgba(255, 75, 75, 0.3);
    }

    /* Horizontal Transparent Button Styling */
    div.stDownloadButton {
        display: flex !important;
        justify-content: center !important;
    }

    div.stDownloadButton > button {
        width: 80% !important; /* Makes it horizontal and wide */
        height: 70px !important;
        background-color: transparent !important; /* Transparent */
        color: #ff4b4b !important; /* Red Text */
        font-size: 20px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        border: 2px solid #ff4b4b !important; /* Red Border */
        border-radius: 12px !important;
        transition: all 0.3s ease-in-out;
    }
    
    /* Hover effect */
    div.stDownloadButton > button:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: white !important;
        border-color: white !important;
        box-shadow: 0px 0px 20px rgba(255, 75, 75, 0.4) !important;
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

    # ---------- GENERATE METRICS ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call parser
            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result
            st.rerun()

    # Check if results exist
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']

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

        # ---------- COLUMN DATATYPES ----------
        st.markdown("## 📌 Column Datatypes")
        col_types = pd.Series(df.dtypes).astype(str)
        type_df = pd.DataFrame(list(col_types.items()), columns=["Column", "Data Type"])
        st.dataframe(type_df, use_container_width=True)

        # ---------- NUMERIC & CATEGORICAL ----------
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        # ---------- MIN / AVG / MAX GRADIENT BAR ----------
        st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
        for col in numeric_cols:
            min_val = df[col].min()
            avg_val = round(df[col].mean(), 2)
            max_val = df[col].max()
            st.markdown(f"**{col}**")
            st.markdown(f"""
            <div style="display:flex; gap:4px; margin-bottom:4px;">
                <div style="flex:1; background:linear-gradient(to right, #ff4b4b, #ff9999); height:20px;"></div>
                <div style="flex:1; background:linear-gradient(to right, #ffea00, #ffd700); height:20px;"></div>
                <div style="flex:1; background:linear-gradient(to right, #00ff4b, #00cc33); height:20px;"></div>
            </div>
            <div style="margin-bottom:10px;">Min: {min_val} | Avg: {avg_val} | Max: {max_val}</div>
            """, unsafe_allow_html=True)

        # ---------- COLUMN GRAPHS ----------
        with st.expander("📊 Column Graphs (Interactive)"):
            for col in numeric_cols:
                fig = px.line(df, y=col, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- ML READINESS SCORE ----------
        missing_pct = (df.isna().sum() / len(df) * 100).round(2)
        completeness = round(100 - missing_pct.mean(), 2)
        ml_ready_score = round(completeness, 2) # simplified for example

        st.markdown("## 🤖 ML Readiness Score")
        st.markdown(f"""
        <div style="background:linear-gradient(to right, #ff4b4b, #ff9999, #00ff4b); 
                    width:100%; height:25px; border-radius:5px; position:relative;">
            <div style="position:absolute; left:{ml_ready_score}%; top:0; transform:translateX(-50%);
                        color:black; font-weight:bold;">{ml_ready_score}/100</div>
        </div>
        """, unsafe_allow_html=True)

        # ---------- FIXED HORIZONTAL TRANSPARENT DOWNLOAD BUTTON ----------
        pdf_path = "output/report.pdf" 
        if os.path.exists(pdf_path):
            st.markdown('<div class="footer-container">', unsafe_allow_html=True)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD PDF REPORT",
                    data=f,
                    file_name="Documentation_Report.pdf",
                    mime="application/pdf"
                )
            st.markdown('</div>', unsafe_allow_html=True)
