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

# --- AGGRESSIVE CSS FOR PC VISIBILITY ---
st.markdown("""
    <style>
    /* 1. Add massive padding to the bottom of the page so content doesn't get stuck behind the button */
    .main .block-container {
        padding-bottom: 250px !important;
    }
    
    .stApp { background-color: #0E1117; }

    /* 2. Transparent Fixed Footer - Forced to front with Z-INDEX */
    .footer-container {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: rgba(14, 17, 23, 0.85); /* Semi-transparent dark blur */
        backdrop-filter: blur(10px); /* Modern glass effect for PC */
        padding: 40px 0;
        text-align: center;
        z-index: 999999; /* Higher than any Streamlit element */
        border-top: 1px solid rgba(0, 230, 118, 0.3);
    }

    /* 3. Centering the Button */
    div.stDownloadButton {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* 4. The BIG TRANSPARENT Button */
    div.stDownloadButton > button {
        width: 80% !important; /* Horizontal/Wide */
        max-width: 1200px;
        height: 85px !important; /* Big/Tall */
        background-color: transparent !important; /* Transparent */
        color: #00E676 !important; /* Neon Green */
        font-size: 24px !important;
        font-weight: 900 !important;
        letter-spacing: 3px;
        border: 2px solid #00E676 !important; /* Neon Border */
        border-radius: 20px !important;
        box-shadow: 0px 0px 20px rgba(0, 230, 118, 0.2) !important;
        transition: all 0.4s ease;
        text-transform: uppercase;
    }
    
    /* Glow effect on hover */
    div.stDownloadButton > button:hover {
        background: rgba(0, 230, 118, 0.15) !important;
        box-shadow: 0px 0px 40px rgba(0, 230, 118, 0.6) !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
        transform: translateY(-5px);
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center; color: white;'>📊 Auto-Documenter</h1>", unsafe_allow_html=True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Upload Data", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # State management
    if 'main_df' not in st.session_state:
        if uploaded_file.name.endswith(".csv"):
            st.session_state.main_df = pd.read_csv(uploaded_file)
        else:
            st.session_state.main_df = pd.read_excel(uploaded_file)
    
    df = st.session_state.main_df
    st.dataframe(df.head(10), use_container_width=True)

    if st.button("🚀 Run Intelligent Analysis"):
        with st.spinner("Decoding Data Patterns..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            df.to_csv(temp_path, index=False)
            
            # This calls your parser.py
            st.session_state['analysis_result'] = analyze_file(temp_path)
            st.rerun()

    # ---------- THE DOWNLOAD SECTION ----------
    if 'analysis_result' in st.session_state:
        # Wrap button in our custom CSS class
        st.markdown('<div class="footer-container">', unsafe_allow_html=True)
        
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD PROFESSIONAL DATA REPORT (PDF)",
                    data=f,
                    file_name="Data_Intelligence_Report.pdf",
                    mime="application/pdf"
                )
        else:
            # If the file isn't found on PC, show a warning
            st.warning("Analysis finished, but 'output/report.pdf' was not found on your PC disk.")
            
        st.markdown('</div>', unsafe_allow_html=True)
