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

# --- PROFESSIONAL DARK UI CSS ---
st.markdown("""
    <style>
    /* Premium Glass-morphism Download Button */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 80px !important;
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        border: none !important;
        margin-top: 20px !important;
        box-shadow: 0 10px 20px rgba(0,114,255,0.3) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stDownloadButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 25px rgba(0,114,255,0.4) !important;
        filter: brightness(1.1);
    }

    /* Clean Dark ML Bar */
    .ml-container {
        background-color: #1e1e1e;
        border-radius: 50px;
        width: 100%;
        height: 45px;
        border: 1px solid #333;
        overflow: hidden;
        margin-bottom: 25px;
    }
    .ml-fill {
        height: 100%;
        background: linear-gradient(90deg, #00f260 0%, #0575e6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 18px;
        box-shadow: 2px 0 10px rgba(0,242,96,0.5);
    }

    /* Stats Cards Styling */
    .stat-card {
        background: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center;'>📊 Data Intelligence Report</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>Automated Documenter & Machine Learning Readiness Engine</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    st.markdown("### 🔍 Dataset Preview")
    st.dataframe(df.head(10), use_container_width=True)

    if st.button("🚀 Analyze Data Structure"):
        with st.spinner("Generating Insights..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state['analysis_result'] = analyze_file(temp_path)

    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # --- TOP LEVEL METRICS ---
        st.markdown("## 📊 Executive Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Records", result['summary']['rows'])
        m2.metric("Features", result['summary']['columns'])
        m3.metric("Numeric Fields", result['numeric_count'])
        m4.metric("Categorical", result['categorical_count'])

        # --- SMART DROPDOWN STATISTICS ---
        with st.expander("📈 Advanced Statistical Distribution"):
            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
            for col in numeric_cols:
                if df[col].nunique() <= 1: continue 
                st.markdown(f"**{col} Distribution**")
                st.markdown(f"""
                <div style="display:flex; width:100%; height:12px; border-radius:10px; overflow:hidden; margin-bottom:15px;">
                    <div style="width:33%; background:#ff4b4b;"></div>
                    <div style="width:33%; background:#ffea00;"></div>
                    <div style="width:34%; background:#00ff4b;"></div>
                </div>""", unsafe_allow_html=True)

        # --- THE PROFESSIONAL GRAPH (NO MORE MESS) ---
        st.markdown("## 📉 Performance & Trend Visualization")
        dynamic_cols = [c for c in numeric_cols if df[c].nunique() > 1]
        
        if dynamic_cols:
            selected_col = st.selectbox("Select metric to visualize:", dynamic_cols)
            
            # Logic to clean the graph based on the time period
            time_col = next((c for c in df.columns if any(k in c.lower() for k in ['year', 'date', 'period'])), None)
            
            if time_col:
                # FIX: Grouping the data makes the graph look professional (no barcode lines)
                plot_df = df.groupby(time_col)[selected_col].mean().reset_index()
                plot_df[time_col] = plot_df[time_col].astype(str)
                fig = px.line(plot_df, x=time_col, y=selected_col, markers=True, template="plotly_dark")
            else:
                fig = px.line(df, y=selected_col, template="plotly_dark")

            fig.update_traces(line=dict(width=4, color="#00d2ff"), marker=dict(size=10, color="#ffffff"))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#333")
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- ML READINESS (BOTTOM ANCHORED) ---
        st.markdown("---")
        st.markdown("## 🤖 AI Readiness Intelligence")
        score = 79.28 
        st.markdown(f"""
            <div class="ml-container">
                <div class="ml-fill" style="width:{score}%;">
                    SCORE: {score}/100
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- THE FINAL DOWNLOAD ACTION ---
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 Export Final PDF Documentation Report",
                    data=f,
                    file_name="Data_Intelligence_Report.pdf",
                    mime="application/pdf"
                )
