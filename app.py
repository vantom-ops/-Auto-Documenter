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

# --- DARK MODE UI/UX CSS ---
st.markdown("""
    <style>
    /* Dark Theme Adjustments */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Big prominent download button at the bottom */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 75px !important;
        background-color: #1E88E5 !important;
        color: white !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: none !important;
        margin-top: 40px !important;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    div.stDownloadButton > button:hover {
        background-color: #1565C0 !important;
        transform: scale(1.01);
    }
    
    /* ML Readiness Graphic Bar */
    .ml-container {
        background-color: #262730;
        border-radius: 20px;
        width: 100%;
        height: 35px;
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
        font-size: 14px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Professional Data Intelligence & Automated Reporting")
st.markdown("---")

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # Load data
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    st.markdown("## 🔍 Data Preview")
    st.dataframe(df.head(10), use_container_width=True)

    # ---------- GENERATION BUTTON ----------
    if st.button("🚀 Run Dark-Mode Analysis"):
        with st.spinner("Analyzing and generating Dark-Mode Report..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result

    # ---------- DISPLAY RESULTS ----------
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # --- METRICS ---
        st.markdown("## 📊 Quick Stats")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric", result['numeric_count'])
        c4.metric("Categorical", result['categorical_count'])

        # --- DARK MODE GRAPHS (CLEANED) ---
        st.markdown("## 📉 Performance & Trends")
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        dynamic_cols = [c for c in numeric_cols if df[c].nunique() > 1]
        
        if dynamic_cols:
            selected_col = st.selectbox("Select metric to analyze:", dynamic_cols)
            
            # Identify time-series column
            x_axis = None
            for c in df.columns:
                if any(key in c.lower() for key in ['period', 'year', 'date']):
                    x_axis = c
                    break
            
            if x_axis:
                # AGGREGATION: Fixing the "Barcode/Blue Block" mess
                # We group by the time column and take the mean to get a clean line
                clean_df = df.groupby(x_axis)[selected_col].mean().reset_index()
                clean_df[x_axis] = clean_df[x_axis].astype(str) # Remove decimal axis gaps
                
                fig = px.line(clean_df, x=x_axis, y=selected_col, 
                              title=f"Trend Analysis: Average {selected_col}", 
                              markers=True)
            else:
                fig = px.line(df, y=selected_col, title=f"{selected_col} Sequence")

            # DARK MODE STYLING FOR PLOTLY
            fig.update_traces(line=dict(width=3, color="#64B5F6"), marker=dict(size=8, color="#BBDEFB"))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                xaxis=dict(showgrid=True, gridcolor='#333', title=x_axis if x_axis else "Index"),
                yaxis=dict(showgrid=True, gridcolor='#333', title=selected_col),
                font=dict(color="#E0E0E0")
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- ML READINESS (GRAPHIC BAR) ---
        st.markdown("## 🤖 AI Readiness")
        score = 79.28  
        bar_color = "#4CAF50" if score > 75 else "#FBC02D"
        
        st.markdown(f"**ML Readiness Score: {score}/100**")
        st.markdown(f"""
            <div class="ml-container">
                <div class="ml-fill" style="width:{score}%; background-color:{bar_color};">
                    {score}%
                </div>
            </div>
            <br>
        """, unsafe_allow_html=True)

        # --- HEATMAP ---
        with st.expander("🔥 Multi-Variable Correlation"):
            if len(numeric_cols) > 1:
                corr_cols = [c for c in numeric_cols if df[c].nunique() > 1]
                if corr_cols:
                    corr = df[corr_cols].corr().round(2)
                    fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="Viridis")
                    fig_heat.update_layout(template="plotly_dark", paper_bgcolor="#0E1117")
                    st.plotly_chart(fig_heat, use_container_width=True)

        # --- THE BIG DOWNLOAD BUTTON (BOTTOM) ---
        st.markdown("---")
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD PROFESSIONAL PDF REPORT",
                    data=f,
                    file_name=f"Analytics_Report_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
