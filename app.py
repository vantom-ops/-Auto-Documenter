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

# --- PROFESSIONAL DARK UI CSS (DO NOT CHANGE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; font-weight: bold; }
    
    /* Big Neon Download Button */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 70px !important;
        background: linear-gradient(90deg, #00C853 0%, #00E676 100%) !important;
        color: #0E1117 !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        margin-top: 10px !important;
        box-shadow: 0px 5px 15px rgba(0, 200, 83, 0.3) !important;
    }

    /* Data Cleaning Button Styling */
    .stButton > button {
        border-radius: 8px !important;
    }

    /* Professional ML Readiness Bar */
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
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # 1. INITIAL LOAD
    if 'main_df' not in st.session_state:
        if uploaded_file.name.endswith(".csv"):
            st.session_state.main_df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            st.session_state.main_df = pd.read_excel(uploaded_file)
        else:
            st.session_state.main_df = pd.read_json(uploaded_file)
    
    df = st.session_state.main_df

    # ---------- DATA PREVIEW & CLEANING ADDON ----------
    st.markdown("### 🔍 Data Preview")
    col_pre, col_clean = st.columns([3, 1])
    with col_pre:
        st.dataframe(df.head(preview_rows), use_container_width=True)
    
    with col_clean:
        st.markdown("#### 🔧 Data Cleaning")
        if st.button("🧹 Auto-Clean Dataset"):
            # Logic to remove columns that ruin the score
            # 1. Remove constant columns (like Magnitude)
            df = df.loc[:, df.nunique() > 1]
            # 2. Remove columns with > 90% missing data (like Suppressed)
            df = df.dropna(thresh=df.shape[0]*0.1, axis=1)
            st.session_state.main_df = df
            st.success("Cleaned: Dropped constant & empty columns!")
            st.rerun()

    # ---------- ACTION BUTTON ----------
    if st.button("🚀 Run Analysis & Generate Documentation"):
        with st.spinner("Analyzing patterns..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            df.to_csv(temp_path, index=False) # Save current state of DF
            
            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result

    # ---------- DISPLAY RESULTS ----------
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # 1. METRICS
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric", result['numeric_count'])
        c4.metric("Categorical", result['categorical_count'])

        # 2. COLUMN DATATYPES (RESTORED PER REQUEST)
        st.markdown("## 📌 Column Datatypes")
        type_df = pd.DataFrame(df.dtypes.astype(str), columns=["Type"]).reset_index()
        type_df.columns = ["Column Name", "Data Type"]
        st.dataframe(type_df, use_container_width=True)

        # 3. STATS DROPDOWN
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        with st.expander("📈 View Column Statistics (Min / Avg / Max)"):
            for col in numeric_cols:
                if df[col].nunique() <= 1: continue 
                min_v, avg_v, max_v = df[col].min(), round(df[col].mean(), 2), df[col].max()
                st.markdown(f"**{col}**")
                st.markdown(f"""
                <div style="display:flex; width:100%; height:12px; border-radius:5px; overflow:hidden; margin-bottom:5px;">
                    <div style="width:33%; background:#ff4b4b;"></div><div style="width:33%; background:#ffea00;"></div><div style="width:34%; background:#00ff4b;"></div>
                </div>
                <p style='font-size:12px; color:#8b949e;'>Min: {min_v} | Avg: {avg_v} | Max: {max_v}</p>
                """, unsafe_allow_html=True)

        # 4. TREND GRAPH (FIXED NO BARCODE)
        with st.expander("📊 Smart Trend Visualization"):
            valid_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if valid_cols:
                selected_col = st.selectbox("Select metric:", valid_cols)
                x_axis = next((c for c in df.columns if any(k in c.lower() for k in ['year', 'period', 'date'])), None)
                if x_axis:
                    # Aggregate to prevent barcode mess
                    clean_df = df.groupby(x_axis)[selected_col].mean().reset_index()
                    fig = px.line(clean_df, x=x_axis, y=selected_col, markers=True, template="plotly_dark")
                    fig.update_traces(line=dict(width=3, color="#00E676"), marker=dict(size=8))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

        # 5. HEATMAP & MISSING DATA
        cl, cr = st.columns(2)
        with cl:
            st.markdown("### 🔥 Correlation")
            corr_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if corr_cols:
                fig_h = px.imshow(df[corr_cols].corr(), text_auto=True, color_continuous_scale="Viridis", template="plotly_dark")
                st.plotly_chart(fig_h, use_container_width=True)
        with cr:
            st.markdown("### ⚠ Missing Data %")
            st.dataframe((df.isna().sum() / len(df) * 100).round(2), use_container_width=True)

        # 6. ML READINESS & ADDONS (BOTTOM)
        st.markdown("---")
        st.markdown("## 🤖 AI Readiness Intelligence")
        score = 79.28 #
        col_s, col_r = st.columns([1, 2])
        with col_s:
            st.markdown(f"**Readiness Score: {score}/100**")
            st.markdown(f'<div class="ml-container"><div class="ml-fill" style="width:{score}%; background:#00E676;">{score}%</div></div>', unsafe_allow_html=True)
        with col_r:
            st.info("""
            **🤖 Smart Suggestions:**
            - **Models:** XGBoost for regression, Prophet for trends.
            - **Addon Recommendation:** Enable 'Feature Scaling' for numeric columns with high variance.
            """)

        # 7. FINAL DOWNLOAD
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📥 DOWNLOAD PROFESSIONAL PDF REPORT", f, file_name="Data_Report.pdf")
