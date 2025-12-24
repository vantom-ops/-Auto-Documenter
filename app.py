import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file  
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# --- SAME UI, FORCED PC VISIBILITY ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #0E1117; 
        padding-bottom: 180px; 
    }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-weight: bold; }
    
    /* Centered Fixed Footer */
    .footer-container {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(14, 17, 23, 0.95); 
        padding: 30px 0;
        text-align: center;
        /* Forced PC Visibility Fixes below */
        z-index: 99999 !important; 
        display: block !important;
        visibility: visible !important;
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
        box-shadow: 0px 0px 15px rgba(0, 230, 118, 0.1) !important;
        transition: all 0.4s ease-in-out;
        text-transform: uppercase;
    }
    
    div.stDownloadButton > button:hover {
        background: rgba(0, 230, 118, 0.1) !important;
        box-shadow: 0px 0px 30px rgba(0, 230, 118, 0.4) !important;
        transform: translateY(-3px);
        color: #ffffff !important;
        border-color: #ffffff !important;
    }

    .ml-container {
        background-color: #1c1e26;
        border-radius: 30px;
        width: 100%;
        height: 35px;
        border: 1px solid #333;
        overflow: hidden;
    }
    .ml-fill {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0E1117;
        font-weight: 900;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center; color: white;'>📊 Auto-Documenter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>Intelligent Data Intelligence Engine</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 100, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Upload Data (CSV, Excel, JSON)", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get('current_file_id') != file_id:
        st.session_state.current_file_id = file_id
        try:
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith((".xlsx", ".xls")):
                df_raw = pd.read_excel(uploaded_file)
            else:
                df_raw = pd.read_json(uploaded_file)
            
            for col in df_raw.columns:
                if df_raw[col].dtype == 'object':
                    try:
                        cleaned = df_raw[col].astype(str).str.replace(',', '')
                        df_raw[col] = pd.to_numeric(cleaned, errors='ignore')
                    except: pass
            
            st.session_state.main_df = df_raw
            if 'analysis_result' in st.session_state:
                del st.session_state['analysis_result']
        except Exception as e:
            st.error(f"Error: {e}"); st.stop()
    
    df = st.session_state.main_df

    st.markdown("### 🔍 Data Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    if st.button("🚀 Run Intelligent Analysis"):
        with st.spinner("Decoding Data Patterns..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            df.to_csv(temp_path, index=False)
            st.session_state['analysis_result'] = analyze_file(temp_path)
            st.rerun() # This is critical for PC to refresh the file check

    # ---------- DISPLAY RESULTS ----------
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # (Metric and Chart Code Kept Same)
        st.markdown("## 📊 Dataset Metrics")
        summary = result.get('summary', {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Rows", summary.get('rows', df.shape[0]))
        c2.metric("Total Columns", summary.get('columns', df.shape[1]))
        c3.metric("Numeric Fields", result.get('numeric_count', 0))
        c4.metric("Categorical Fields", result.get('categorical_count', 0))

        # --- THE DOWNLOAD BUTTON SECTION ---
        st.markdown('<div class="footer-container">', unsafe_allow_html=True)
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📥 DOWNLOAD DATA REPORT (PDF)", f, file_name="Report.pdf")
        else:
            # Helpful if it fails on PC
            st.warning("Analysis done but PDF file missing from output folder.")
        st.markdown('</div>', unsafe_allow_html=True)
