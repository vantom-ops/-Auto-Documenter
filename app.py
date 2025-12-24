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

# --- CSS FOR BIG HORIZONTAL TRANSPARENT BUTTON ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #0E1117; 
        padding-bottom: 180px; 
    }
    
    /* Centered Fixed Footer */
    .footer-container {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(14, 17, 23, 0.9); 
        padding: 30px 0;
        text-align: center;
        z-index: 9999;
        border-top: 1px solid rgba(0, 230, 118, 0.2);
    }

    /* BIG HORIZONTAL TRANSPARENT BUTTON */
    div.stDownloadButton {
        display: flex;
        justify-content: center;
    }

    div.stDownloadButton > button {
        width: 85% !important;
        height: 80px !important;
        background: transparent !important;
        color: #00E676 !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        letter-spacing: 2px;
        border: 2px solid #00E676 !important;
        border-radius: 15px !important;
        transition: all 0.4s ease-in-out;
        text-transform: uppercase;
    }
    
    div.stDownloadButton > button:hover {
        background: rgba(0, 230, 118, 0.1) !important;
        box-shadow: 0px 0px 30px rgba(0, 230, 118, 0.4) !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
    }

    .ml-container {
        background-color: #1c1e26;
        border-radius: 30px;
        width: 100%; height: 35px;
        border: 1px solid #333;
        overflow: hidden;
    }
    .ml-fill {
        height: 100%; display: flex; align-items: center; justify-content: center;
        color: #0E1117; font-weight: 900; font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: white;'>📊 Auto-Documenter</h1>", unsafe_allow_html=True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Upload Data (CSV, Excel, JSON)", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # Reset logic for switching between CSV/Excel
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get('current_file_id') != file_id:
        st.session_state.current_file_id = file_id
        if 'analysis_result' in st.session_state:
            del st.session_state['analysis_result']
            
        # Clean data immediately on upload
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
                except: pass
        st.session_state.main_df = df

    df = st.session_state.main_df
    st.dataframe(df.head(10), use_container_width=True)

    if st.button("🚀 Run Intelligent Analysis"):
        with st.spinner("Generating Report & Graphs..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            df.to_csv(temp_path, index=False)
            
            # This calls your parser.py
            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result
            st.rerun()

    # ---------- RESULTS & DOWNLOAD ----------
    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", res['summary']['rows'])
        c2.metric("Columns", res['summary']['columns'])
        c3.metric("Completeness", f"{res['completeness']}%")
        c4.metric("Numeric Ratio", f"{res['numeric_ratio']}%")

        # FIX: THE DOWNLOAD BUTTON
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            st.markdown('<div class="footer-container">', unsafe_allow_html=True)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD DATA REPORT (PDF)",
                    data=f,
                    file_name="Data_Intelligence_Report.pdf",
                    mime="application/pdf"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Report generated but file not found. Ensure parser.py saves to 'output/report.pdf'")
