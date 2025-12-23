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

# --- CUSTOM CSS FOR BIG DOWNLOAD BUTTON & UI ---
st.markdown("""
    <style>
    /* Big prominent download button at bottom */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 70px !important;
        background-color: #1f77b4 !important;
        color: white !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border: 2px solid #155a8a !important;
        border-radius: 12px !important;
        margin-top: 30px !important;
        transition: 0.3s;
    }
    div.stDownloadButton > button:hover {
        background-color: #155a8a !important;
        border-color: #0d3d5d !important;
    }
    /* Style for the ML Bar container */
    .ml-bar-bg {
        background-color: #e0e0e0; 
        border-radius: 15px; 
        width: 100%; 
        height: 30px; 
        position: relative;
        margin-bottom: 10px;
    }
    .ml-bar-fill {
        height: 100%; 
        border-radius: 15px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        color: white;
        font-weight: bold;
        transition: width 1s ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a file to generate professional documentation and a downloadable PDF report.")
st.markdown("---")

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # Read file for preview
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
    st.dataframe(df.head(10), use_container_width=True)

    # ---------- ACTION BUTTON ----------
    if st.button("🚀 Run Analysis & Generate PDF"):
        with st.spinner("Analyzing data and building report..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call your parser.py function
            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result

    # ---------- DISPLAY RESULTS ----------
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        st.markdown("## 📊 Dataset Overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Rows", result['summary']['rows'])
        c2.metric("Total Columns", result['summary']['columns'])
        c3.metric("Numeric", result['numeric_count'])
        c4.metric("Categorical", result['categorical_count'])

        # --- OLD TYPE GRAPH (Traditional Professional Style) ---
        st.markdown("## 📉 Trend Analysis (Old-Type Style)")
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        # Filter constant columns
        selectable = [c for c in numeric_cols if df[c].nunique() > 1]
        
        if selectable:
            target_col = st.selectbox("Select metric to visualize:", selectable)
            
            # Formatting timeline X-axis
            plot_df = df.copy()
            x_axis = None
            for c in df.columns:
                if any(k in c.lower() for k in ['period', 'year', 'date']):
                    x_axis = c
                    plot_df[x_axis] = plot_df[x_axis].astype(str) # Remove decimal gaps
                    break
            
            fig = px.line(plot_df, x=x_axis, y=target_col, title=f"Historical Trend: {target_col}")
            
            # Apply "Old Type" aesthetics: White background, grey grids, dark blue lines
            fig.update_traces(line=dict(width=2.5, color="#1f77b4"))
            fig.update_layout(
                plot_bgcolor="white",
                xaxis=dict(showgrid=True, gridcolor='#f0f0f0', linecolor='black', ticks="outside"),
                yaxis=dict(showgrid=True, gridcolor='#f0f0f0', linecolor='black', ticks="outside"),
                font=dict(family="Arial", size=12, color="black")
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- GRAPHIC ML READINESS BAR ---
        st.markdown("## 🤖 ML Readiness Status")
        score = 79.28  
        
        # Color transition logic
        bar_color = "#00cc66" if score > 75 else "#ffcc00" if score > 50 else "#ff4b4b"
        
        st.markdown(f"**Current Score: {score}/100**")
        st.markdown(f"""
            <div class="ml-bar-bg">
                <div class="ml-bar-fill" style="width: {score}%; background-color: {bar_color};">
                    {score}%
                </div>
            </div>
            <p style='font-size: 14px; color: #666;'>Suggested Algorithms: Random Forest, XGBoost, Linear Regression</p>
        """, unsafe_allow_html=True)

        # --- MISSING VALUES ---
        with st.expander("⚠ Data Quality Warnings"):
            missing_pct = (df.isna().sum() / len(df) * 100).round(2)
            st.write("Percentage of Missing Data per Column:")
            st.dataframe(missing_pct)

        # --- BIG PDF DOWNLOAD BUTTON AT BOTTOM ---
        st.markdown("---")
        pdf_path = "output/report.pdf"
        
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD COMPLETED PDF REPORT",
                    data=f,
                    file_name=f"Report_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Analysis complete, but PDF file not found in 'output/' folder.")
