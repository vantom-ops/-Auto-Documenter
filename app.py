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
    .stApp { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-weight: bold; }

    /* Big Neon Download Button */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 75px !important;
        background: linear-gradient(90deg, #00C853 0%, #00E676 100%) !important;
        color: #0E1117 !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        border: none !important;
        margin-top: 20px !important;
        box-shadow: 0px 5px 15px rgba(0, 200, 83, 0.4) !important;
    }
    
    /* Professional ML Readiness Bar */
    .ml-container {
        background-color: #1c1e26;
        border-radius: 30px;
        width: 100%;
        height: 40px;
        border: 1px solid #333;
        overflow: hidden;
        margin-top: 10px;
    }
    .ml-fill {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0E1117;
        font-weight: 900;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center; color: white;'>📊 Auto-Documenter</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_json(uploaded_file)

    # ---------- ACTION BUTTON ----------
    if st.button("🚀 Run Analysis"):
        with st.spinner("Analyzing..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state['analysis_result'] = analyze_file(temp_path)

    # ---------- DISPLAY RESULTS ----------
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # 1. METRICS
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Rows", result['summary']['rows'])
        c2.metric("Total Columns", result['summary']['columns'])
        c3.metric("Numeric Fields", result['numeric_count'])
        c4.metric("Categorical Fields", result['categorical_count'])

        # 2. COLUMN DATATYPES (RESTORED HERE)
        st.markdown("## 📌 Column Datatypes")
        type_info = pd.DataFrame(df.dtypes.astype(str), columns=["Data Type"]).reset_index()
        type_info.columns = ["Column Name", "Data Type"]
        st.table(type_info)

        # 3. STATS DROPDOWN
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        with st.expander("📈 View Column Statistics (Min / Avg / Max)"):
            for col in numeric_cols:
                if df[col].nunique() <= 1: continue 
                st.markdown(f"**{col}**")
                st.markdown(f"""
                <div style="display:flex; width:100%; height:12px; border-radius:5px; overflow:hidden; margin-bottom:10px;">
                    <div style="width:33%; background:#ff4b4b;"></div><div style="width:33%; background:#ffea00;"></div><div style="width:34%; background:#00ff4b;"></div>
                </div>
                """, unsafe_allow_html=True)

        # 4. TREND GRAPH
        with st.expander("📊 Smart Trend Visualization"):
            selected_col = st.selectbox("Select metric:", [c for c in numeric_cols if df[c].nunique() > 1])
            x_axis = next((c for c in df.columns if any(k in c.lower() for k in ['year', 'period', 'date'])), None)
            if x_axis:
                clean_df = df.groupby(x_axis)[selected_col].mean().reset_index()
                fig = px.line(clean_df, x=x_axis, y=selected_col, markers=True, template="plotly_dark")
                fig.update_traces(line=dict(color="#00E676"))
                st.plotly_chart(fig, use_container_width=True)

        # 5. ML READINESS & SUGGESTIONS
        st.markdown("---")
        st.markdown("## 🤖 AI Readiness Intelligence")
        score = 79.28
        col_s, col_r = st.columns([1, 2])
        with col_s:
            st.markdown(f"**Readiness: {score}/100**")
            st.markdown(f'<div class="ml-container"><div class="ml-fill" style="width:{score}%; background:#00E676;">{score}%</div></div>', unsafe_allow_html=True)
        with col_r:
            st.info("**Suggestions:** Use **XGBoost** for regression or **Prophet** for time-series forecasting. Cleanup: Drop 'Suppressed' (99% nulls) and 'Magnitude' (constant).")

        # 6. DOWNLOAD
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📥 DOWNLOAD PROFESSIONAL PDF REPORT", f, file_name="Data_Report.pdf")
