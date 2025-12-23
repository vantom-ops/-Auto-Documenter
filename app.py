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

# --- CUSTOM UI/UX CSS ---
st.markdown("""
    <style>
    /* Big prominent download button at the very bottom */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 75px !important;
        background-color: #0047AB !important;
        color: white !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: 3px solid #002D62 !important;
        margin-top: 40px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    
    /* ML Readiness Graphic Bar */
    .ml-container {
        background-color: #f0f2f6;
        border-radius: 20px;
        width: 100%;
        height: 35px;
        border: 1px solid #d1d5db;
        overflow: hidden;
        margin-top: 10px;
    }
    .ml-fill {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: black;
        font-weight: bold;
        font-size: 14px;
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
    # 1. Load data for UI
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
        with st.spinner("Processing data and generating PDF..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call parser and store result in session state
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

        # --- STATISTICS ---
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        st.markdown("## 📈 Column Statistics")
        for col in numeric_cols:
            # We skip columns that are constant (like Magnitude) to keep UI clean
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
            # Filter columns that actually change
            dynamic_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            
            if dynamic_cols:
                selected_col = st.selectbox("Select metric to analyze trend:", dynamic_cols)
                
                # Search for a Time/Period column
                x_axis = None
                for c in df.columns:
                    if any(key in c.lower() for key in ['period', 'year', 'date']):
                        x_axis = c
                        break
                
                if x_axis:
                    # AGGREGATION: Solve the "Barcode" messy line issue
                    clean_df = df.groupby(x_axis)[selected_col].mean().reset_index()
                    clean_df[x_axis] = clean_df[x_axis].astype(str) # Remove decimal gaps
                    
                    fig = px.line(clean_df, x=x_axis, y=selected_col, 
                                  title=f"Trend: Average {selected_col} by {x_axis}", 
                                  markers=True)
                else:
                    fig = px.line(df, y=selected_col, title=f"{selected_col} Values (Index View)")

                # Apply "Old-School" Professional Styling
                fig.update_traces(line=dict(width=2, color="#1f77b4"), marker=dict(size=6))
                fig.update_layout(
                    plot_bgcolor="white",
                    xaxis=dict(showgrid=True, gridcolor='#f0f0f0', linecolor='black'),
                    yaxis=dict(showgrid=True, gridcolor='#f0f0f0', linecolor='black'),
                    font=dict(family="Arial")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No variable numeric data found for trending.")

        # --- ML READINESS (GRAPHIC BAR) ---
        st.markdown("## 🤖 ML Readiness Score")
        score = 79.28  # Static as requested
        bar_color = "#00cc66" if score > 75 else "#ffea00"
        
        st.markdown(f"**Readiness Level: {score}/100**")
        st.markdown(f"""
            <div class="ml-container">
                <div class="ml-fill" style="width:{score}%; background-color:{bar_color};">
                    {score}%
                </div>
            </div>
            <br>
        """, unsafe_allow_html=True)

        # --- HEATMAP & WARNINGS ---
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("### 🔥 Correlation Heatmap")
            if len(numeric_cols) > 1:
                # Filter constant columns from correlation to avoid 'None'
                corr_cols = [c for c in numeric_cols if df[c].nunique() > 1]
                if corr_cols:
                    corr = df[corr_cols].corr().round(2)
                    fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
                    st.plotly_chart(fig_heat, use_container_width=True)
        with c_right:
            st.markdown("### ⚠ Missing Data %")
            missing_pct = (df.isna().sum() / len(df) * 100).round(2)
            st.dataframe(missing_pct, use_container_width=True)

        # --- THE BIG DOWNLOAD BUTTON (BOTTOM) ---
        st.markdown("---")
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
            st.error("PDF file not found. Ensure your parser.py saves the file to 'output/report.pdf'.")
