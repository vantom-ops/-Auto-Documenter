import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from parser import analyze_file
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# --- OPTIMIZED CSS FOR TRANSPARENT HORIZONTAL BUTTON ---
st.markdown("""
    <style>
    .main .block-container { padding-bottom: 220px !important; }
    .stApp { background-color: #0E1117; }
    
    .footer-container {
        position: fixed !important;
        left: 0 !important; bottom: 0 !important;
        width: 100% !important;
        background: rgba(14, 17, 23, 0.95) !important;
        padding: 30px 0 !important;
        text-align: center !important;
        z-index: 999999 !important;
        border-top: 1px solid rgba(255, 75, 75, 0.3);
        backdrop-filter: blur(10px);
    }

    div.stDownloadButton { display: flex !important; justify-content: center !important; }

    div.stDownloadButton > button {
        width: 85% !important;
        height: 75px !important;
        background-color: transparent !important;
        color: #ff4b4b !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        border: 2px solid #ff4b4b !important;
        border-radius: 12px !important;
        transition: all 0.3s ease-in-out;
    }
    
    div.stDownloadButton > button:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
        box-shadow: 0px 0px 30px rgba(255, 75, 75, 0.4) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align: center;'>📄 Auto-Documenter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Upload CSV, Excel, or JSON for instant interactive documentation.</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 100, 10)

# ---------- FILE UPLOADER & PROCESSING ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # Memoize dataframe loading to prevent slow reloads
    @st.cache_data
    def load_data(file):
        ext = file.name.split('.')[-1]
        if ext == 'csv': return pd.read_csv(file)
        if ext in ['xlsx', 'xls']: return pd.read_excel(file)
        if ext == 'json': return pd.read_json(file)
        return None

    df = load_data(uploaded_file)
    
    if df is not None:
        st.markdown("## 🔍 File Preview")
        st.dataframe(df.head(preview_rows), use_container_width=True)

        # ---------- GENERATE METRICS ----------
        if st.button("🚀 Generate Documentation", use_container_width=True):
            with st.spinner("Processing file..."):
                os.makedirs("temp_upload", exist_ok=True)
                temp_path = os.path.join("temp_upload", uploaded_file.name)
                df.to_csv(temp_path, index=False) # Faster than re-writing buffer
                
                st.session_state['analysis_result'] = analyze_file(temp_path)
                st.rerun()

        if 'analysis_result' in st.session_state:
            result = st.session_state['analysis_result']
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.success("✅ Documentation generated successfully!")
                
                # --- DISPLAY METRICS ---
                st.markdown("## 📊 Dataset Metrics")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Rows", result['summary']['rows'])
                c2.metric("Columns", result['summary']['columns'])
                c3.metric("Numeric", result['numeric_count'])
                c4.metric("Categorical", result['categorical_count'])

                # --- COLUMN TYPES ---
                st.markdown("## 📌 Column Datatypes")
                type_df = pd.DataFrame(df.dtypes.astype(str).reset_index())
                type_df.columns = ["Column", "Data Type"]
                st.dataframe(type_df, use_container_width=True)

                numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
                categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

                # --- GRADIENT STATS BARS ---
                st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
                for col in numeric_cols:
                    m1, avg, m2 = df[col].min(), df[col].mean(), df[col].max()
                    st.markdown(f"**{col}**")
                    st.markdown(f"""
                        <div style="display:flex; gap:4px; margin-bottom:4px;">
                            <div style="flex:1; background:linear-gradient(to right, #ff4b4b, #ff9999); height:15px; border-radius:10px;"></div>
                            <div style="flex:1; background:linear-gradient(to right, #ffea00, #ffd700); height:15px; border-radius:10px;"></div>
                            <div style="flex:1; background:linear-gradient(to right, #00ff4b, #00cc33); height:15px; border-radius:10px;"></div>
                        </div>
                        <p style="font-size:12px; color:#aaa;">Min: {m1} | Avg: {round(avg,2)} | Max: {m2}</p>
                    """, unsafe_allow_html=True)

                # --- INTERACTIVE GRAPHS ---
                with st.expander("📊 Trend Graphs"):
                    for col in numeric_cols:
                        st.plotly_chart(px.line(df, y=col, title=f"{col} Trend"), use_container_width=True)

                # --- HEATMAP ---
                if len(numeric_cols) > 1:
                    with st.expander("🔥 Correlation Heatmap", expanded=True):
                        corr = df[numeric_cols].corr().round(2)
                        st.plotly_chart(px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r"), use_container_width=True)

                # --- ML READINESS ---
                missing_pct = (df.isna().sum() / len(df) * 100).round(2)
                ml_ready_score = round((100 - missing_pct.mean()) * 0.4 + (100 - (df.duplicated().mean()*100)) * 0.6, 2)

                st.markdown("## 🤖 ML Readiness Score")
                st.markdown(f"""
                    <div style="background:#262730; width:100%; height:30px; border-radius:15px; overflow:hidden; border: 1px solid #444;">
                        <div style="background:linear-gradient(90deg, #ff4b4b, #ffea00, #00ff4b); width:{ml_ready_score}%; height:100%; display:flex; align-items:center; justify-content:center;">
                            <span style="color:black; font-weight:bold;">{ml_ready_score}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # --- ALGORITHM SUGGESTIONS ---
                st.markdown("### 🧠 Algorithm Path")
                if ml_ready_score < 40: st.info("Low Readiness: Focus on cleaning and normalization.")
                elif 40 <= ml_ready_score < 70: st.warning("Moderate Readiness: Decision Trees or Random Forests suggested.")
                else: st.success("High Readiness: Gradient Boosting or Neural Networks ready.")

                # --- DOWNLOAD FOOTER ---
                pdf_path = "output/report.pdf"
                if os.path.exists(pdf_path):
                    st.markdown('<div class="footer-container">', unsafe_allow_html=True)
                    with open(pdf_path, "rb") as f:
                        st.download_button(label="📥 DOWNLOAD PDF REPORT", data=f, file_name="Report.pdf", mime="application/pdf")
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("Could not process file.")
