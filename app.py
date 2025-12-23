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

# --- PROFESSIONAL DARK UI STYLING ---
st.markdown("""
    <style>
    /* Global Dark Background */
    .stApp {
        background-color: #0E1117;
    }

    /* Professional Glass-Effect Download Button */
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
        transition: 0.3s ease-in-out;
    }
    div.stDownloadButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0px 8px 20px rgba(0, 200, 83, 0.6) !important;
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
        font-size: 16px;
        box-shadow: 5px 0 15px rgba(0, 200, 83, 0.5);
    }

    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        color: #00E676 !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center; color: white;'>📄 Auto-Documenter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>Advanced Data Analytics & ML Intelligence</p>", unsafe_allow_html=True)
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

    st.markdown("### 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    if st.button("🚀 Run Analysis & Generate Documentation"):
        with st.spinner("Processing data..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result

    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        st.success("✅ Documentation generated successfully!")

        # --- METRICS ---
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric", result['numeric_count'])
        c4.metric("Categorical", result['categorical_count'])

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        # --- DROPDOWN COLUMN STATISTICS ---
        with st.expander("📈 View Column Statistics (Min / Avg / Max)"):
            for col in numeric_cols:
                if df[col].nunique() <= 1: continue 
                min_val, avg_val, max_val = df[col].min(), round(df[col].mean(), 2), df[col].max()
                st.markdown(f"**{col}**")
                st.markdown(f"""
                <div style="display:flex; width:100%; height:12px; border-radius:5px; overflow:hidden; margin-bottom:12px;">
                    <div style="width:33%; background:#ff4b4b;"></div><div style="width:33%; background:#ffea00;"></div><div style="width:34%; background:#00ff4b;"></div>
                </div>
                <p style='font-size:12px; color:#8b949e;'>Min: {min_val} | Avg: {avg_val} | Max: {max_val}</p>
                """, unsafe_allow_html=True)

        # --- PROFESSIONAL DARK TREND GRAPH ---
        with st.expander("📊 Column Trends (Interactive Dark Mode)"):
            dynamic_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if dynamic_cols:
                selected_col = st.selectbox("Select metric to analyze trend:", dynamic_cols)
                x_axis = next((c for c in df.columns if any(k in c.lower() for k in ['year', 'period', 'date'])), None)
                
                if x_axis:
                    # Fix messy lines by grouping the average per period
                    clean_df = df.groupby(x_axis)[selected_col].mean().reset_index()
                    clean_df[x_axis] = clean_df[x_axis].astype(str)
                    fig = px.line(clean_df, x=x_axis, y=selected_col, markers=True, template="plotly_dark")
                else:
                    fig = px.line(df, y=selected_col, template="plotly_dark")

                fig.update_traces(line=dict(width=3, color="#00E676"), marker=dict(size=8, color="white"))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

        # --- HEATMAP & MISSING DATA ---
        cl, cr = st.columns(2)
        with cl:
            st.markdown("### 🔥 Correlation")
            corr_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if corr_cols:
                fig_heat = px.imshow(df[corr_cols].corr(), text_auto=True, color_continuous_scale="Viridis", template="plotly_dark")
                st.plotly_chart(fig_heat, use_container_width=True)
        with cr:
            st.markdown("### ⚠ Missing Data %")
            st.dataframe((df.isna().sum() / len(df) * 100).round(2), use_container_width=True)

        # --- ML READINESS SCORE (BOTTOM) ---
        st.markdown("---")
        st.markdown("## 🤖 ML Readiness Score")
        score = 79.28  
        st.markdown(f"**Readiness Level: {score}/100**")
        st.markdown(f"""
            <div class="ml-container">
                <div class="ml-fill" style="width:{score}%; background: #00E676;">{score}%</div>
            </div>
        """, unsafe_allow_html=True)

        # --- PDF DOWNLOAD ---
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(label="📥 DOWNLOAD FULL DOCUMENTATION REPORT (PDF)", data=f, file_name="Data_Report.pdf", mime="application/pdf")
