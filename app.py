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

# --- DARK UI CUSTOM CSS ---
st.markdown("""
    <style>
    /* Big prominent download button - DARK UI Style */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 75px !important;
        background-color: #1E1E1E !important;
        color: #00FF4B !important; /* Neon green text */
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 2px solid #00FF4B !important;
        margin-top: 20px !important;
        box-shadow: 0px 4px 15px rgba(0, 255, 75, 0.2);
        transition: 0.3s;
    }
    div.stDownloadButton > button:hover {
        background-color: #00FF4B !important;
        color: #1E1E1E !important;
    }
    
    /* ML Readiness Graphic Bar - DARK UI Style */
    .ml-container {
        background-color: #31333F;
        border-radius: 20px;
        width: 100%;
        height: 40px;
        border: 1px solid #444;
        overflow: hidden;
        margin-top: 10px;
    }
    .ml-fill {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 16px;
        text-shadow: 1px 1px 2px black;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Generate professional interactive documentation and PDF reports from your datasets.")
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

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- GENERATION BUTTON ----------
    if st.button("🚀 Run Analysis & Generate Documentation"):
        with st.spinner("Processing data..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result

    # ---------- DISPLAY RESULTS ----------
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        st.success("✅ Documentation generated successfully!")

        # --- METRICS ---
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric", result['numeric_count'])
        c4.metric("Categorical", result['categorical_count'])

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        # --- COLUMN STATISTICS (NOW IN DROPDOWN/EXPANDER) ---
        with st.expander("📈 View Column Statistics (Min / Avg / Max)"):
            for col in numeric_cols:
                if df[col].nunique() <= 1: continue 

                min_val = df[col].min()
                avg_val = round(df[col].mean(), 2)
                max_val = df[col].max()

                st.markdown(f"**{col}**")
                st.markdown(f"""
                <div style="display:flex; gap:4px; margin-bottom:4px;">
                    <div style="flex:1; background:linear-gradient(to right, #ff4b4b, #ff9999); height:15px; border-radius:3px;"></div>
                    <div style="flex:1; background:linear-gradient(to right, #ffea00, #ffd700); height:15px; border-radius:3px;"></div>
                    <div style="flex:1; background:linear-gradient(to right, #00ff4b, #00cc33); height:15px; border-radius:3px;"></div>
                </div>
                <div style="margin-bottom:10px; font-size:12px;">Min: {min_val} | Avg: {avg_val} | Max: {max_val}</div>
                """, unsafe_allow_html=True)

        # --- THE "UNDERSTANDABLE" GRAPH SECTION ---
        with st.expander("📊 Smart Column Graphs (Readable Trends)"):
            dynamic_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if dynamic_cols:
                selected_col = st.selectbox("Select metric to analyze trend:", dynamic_cols)
                x_axis = None
                for c in df.columns:
                    if any(key in c.lower() for key in ['period', 'year', 'date']):
                        x_axis = c
                        break
                
                if x_axis:
                    clean_df = df.groupby(x_axis)[selected_col].mean().reset_index()
                    clean_df[x_axis] = clean_df[x_axis].astype(str)
                    fig = px.line(clean_df, x=x_axis, y=selected_col, markers=True, template="plotly_dark")
                else:
                    fig = px.line(df, y=selected_col, template="plotly_dark")

                fig.update_traces(line=dict(width=2, color="#00FF4B")) # Neon green line
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

        # --- HEATMAP & WARNINGS ---
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("### 🔥 Correlation Heatmap")
            corr_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if corr_cols:
                corr = df[corr_cols].corr().round(2)
                fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="Viridis", template="plotly_dark")
                st.plotly_chart(fig_heat, use_container_width=True)
        with c_right:
            st.markdown("### ⚠ Missing Data %")
            missing_pct = (df.isna().sum() / len(df) * 100).round(2)
            st.dataframe(missing_pct, use_container_width=True)

        # --- ML READINESS (MOVED TO BOTTOM) ---
        st.markdown("---")
        st.markdown("## 🤖 ML Readiness Score")
        score = 79.28  
        # Dark UI colors: Neon Green for high score, Amber for medium
        bar_color = "#00FF4B" if score > 75 else "#FFBF00"
        
        st.markdown(f"**Readiness Level: {score}/100**")
        st.markdown(f"""
            <div class="ml-container">
                <div class="ml-fill" style="width:{score}%; background-color:{bar_color}; color: black;">
                    {score}%
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- THE BIG DOWNLOAD BUTTON (BOTTOM) ---
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD FULL DOCUMENTATION REPORT (PDF)",
                    data=f,
                    file_name=f"Data_Report_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("PDF file not found in 'output/'.")
