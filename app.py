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

# --- PROFESSIONAL UI CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; padding-bottom: 180px; }
    
    .footer-container {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(14, 17, 23, 0.95); 
        padding: 30px 0;
        text-align: center;
        z-index: 9999;
        border-top: 1px solid rgba(0, 230, 118, 0.3);
    }

    div.stDownloadButton { display: flex; justify-content: center; }

    div.stDownloadButton > button {
        width: 85% !important;
        height: 80px !important;
        background: transparent !important;
        color: #00E676 !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        border: 2px solid #00E676 !important;
        border-radius: 15px !important;
        transition: all 0.4s ease-in-out;
    }
    
    div.stDownloadButton > button:hover {
        background: rgba(0, 230, 118, 0.1) !important;
        box-shadow: 0px 0px 30px rgba(0, 230, 118, 0.4) !important;
        color: white !important;
        border-color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center; color: white;'>📊 Auto-Documenter</h1>", unsafe_allow_html=True)
st.markdown("---")

uploaded_file = st.file_uploader("Upload Data", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # State Management
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get('current_file_id') != file_id:
        st.session_state.current_file_id = file_id
        # Reset data for new file
        if uploaded_file.name.endswith(".csv"):
            st.session_state.main_df = pd.read_csv(uploaded_file)
        else:
            st.session_state.main_df = pd.read_excel(uploaded_file)
        if 'analysis_result' in st.session_state:
            del st.session_state['analysis_result']
    
    df = st.session_state.main_df
    st.dataframe(df.head(10), use_container_width=True)

    if st.button("🚀 Run Intelligent Analysis"):
        with st.spinner("Analyzing..."):
            # Ensure output directory exists
            if not os.path.exists("output"):
                os.makedirs("output")
            
            temp_path = f"temp_{uploaded_file.name}"
            df.to_csv(temp_path, index=False)
            
            # RUN PARSER
            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result
            st.rerun() # Force UI refresh to show button

    # ---------- DOWNLOAD SECTION ----------
    if 'analysis_result' in st.session_state:
        st.markdown("### Analysis Results Ready")
        
        # This wrapper ensures the button is centered at bottom
        st.markdown('<div class="footer-container">', unsafe_allow_html=True)
        
        # IMPORTANT: Path check
        report_path = "output/report.pdf" 
        
        if os.path.exists(report_path):
            with open(report_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD DATA REPORT (PDF)",
                    data=f,
                    file_name=f"Report_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
        else:
            # Fallback if the PDF isn't generated yet by your parser
            st.warning("Analysis finished, but PDF file was not found in 'output/report.pdf'. Check your parser.py code.")
        
        st.markdown('</div>', unsafe_allow_html=True)
