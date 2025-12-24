import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file  
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# --- CSS FOR TRANSPARENT HORIZONTAL BUTTON & PC VISIBILITY + FOOTER ---
st.markdown("""
<style>
.main .block-container {
    padding-bottom: 200px !important;
}

/* Centered Fixed Footer Wrapper */
.footer-container {
    position: fixed !important;
    left: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    background-color: rgba(14, 17, 23, 0.9) !important; 
    padding: 25px 0 !important;
    text-align: center !important;
    z-index: 999999 !important;
    border-top: 1px solid rgba(255, 75, 75, 0.4);
    font-size: 14px !important;
    color: white !important;
}

/* Hide footer on small screens (mobile) */
@media only screen and (max-width: 768px) {
    .footer-container {
        display: none !important;
    }
}

/* Horizontal Transparent Button */
div.stDownloadButton {
    display: flex !important;
    justify-content: center !important;
}

div.stDownloadButton > button {
    width: 85% !important;
    height: 70px !important;
    background-color: transparent !important;
    color: #ff4b4b !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    border: 2px solid #ff4b4b !important;
    border-radius: 12px !important;
    transition: 0.3s;
}

div.stDownloadButton > button:hover {
    background-color: rgba(255, 75, 75, 0.15) !important;
    border-color: white !important;
    color: white !important;
    box-shadow: 0px 0px 25px rgba(255, 75, 75, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- CENTERED HEADER ----------
st.markdown("""
<div style="text-align:center;">
    <h1>📄 Auto-Documenter</h1>
    <p style="font-size:18px;">
        📤 Upload a CSV or Excel to generate interactive documentation.
    </p>
    <hr>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls'])

if uploaded_file:
    # --- LOAD DATA WITH ENGINE FIX ---
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    elif uploaded_file.name.endswith(".xls"):
        df = pd.read_excel(uploaded_file, engine='xlrd')
    else:
        st.error("Unsupported file type!")
        st.stop()

    # --- DATA CLEANING ---
    if 'Value' in df.columns:
        df['Value'] = pd.to_numeric(df['Value'].astype(str).str.replace(',', ''), errors='coerce')

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- GENERATE METRICS ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result
            st.rerun()

    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        # ---------- DISPLAY METRICS ----------
        st.success("✅ Documentation generated successfully!")
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", result['numeric_count'])
        c4.metric("Categorical Columns", result['categorical_count'])

        # ---------- COLUMN DATATYPES ----------
        st.markdown("## 📌 Column Datatypes")
        col_types = pd.Series(df.dtypes).astype(str)
        type_df = pd.DataFrame(list(col_types.items()), columns=["Column", "Data Type"])
        st.dataframe(type_df, use_container_width=True)

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        # ---------- MIN / AVG / MAX GRADIENT BAR ----------
        st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
        for col in numeric_cols:
            min_val = df[col].min()
            avg_val = round(df[col].mean(), 2)
            max_val = df[col].max()
            st.markdown(f"**{col}**")
            st.markdown(f"""
            <div style="display:flex; gap:4px; margin-bottom:4px;">
                <div style="flex:1; background:linear-gradient(to right, #ff4b4b, #ff9999); height:20px;"></div>
                <div style="flex:1; background:linear-gradient(to right, #ffea00, #ffd700); height:20px;"></div>
                <div style="flex:1; background:linear-gradient(to right, #00ff4b, #00cc33); height:20px;"></div>
            </div>
            <div style="margin-bottom:10px;">Red: Min ({min_val}) | Yellow: Avg ({avg_val}) | Green: Max ({max_val})</div>
            """, unsafe_allow_html=True)

        # ---------- DATA VISUALIZATIONS ----------
        with st.expander("📊 Data Visualizations & Analysis", expanded=True):
            # Correlation
            st.markdown("### 🔥 Correlation Analysis")
            corr_option = st.selectbox("Select Correlation View", ["None", "View Heatmap & Table"])
            if corr_option == "View Heatmap & Table":
                if len(numeric_cols) > 1:
                    corr = df[numeric_cols].corr().round(2)
                    st.dataframe(corr, use_container_width=True)
                    fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", aspect="auto")
                    st.plotly_chart(fig_heat, use_container_width=True)
                else:
                    st.warning("Not enough numeric columns for correlation analysis.")

            # Column Graphs
            st.markdown("### 📈 Column Graphs")
            if numeric_cols:
                graph_col = st.selectbox("Select Column to Visualize", ["Select a column..."] + numeric_cols)
                if graph_col != "Select a column...":
                    fig_ind = px.line(df, y=graph_col, title=f"{graph_col} Trend Analysis")
                    st.plotly_chart(fig_ind, use_container_width=True)
            else:
                st.info("No numeric columns available.")

        # ---------- WARNINGS ----------
        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().sum() / len(df) * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        # ---------- ML READINESS SCORE ----------
        completeness = round(100 - missing_pct.mean(), 2)
        duplicate_pct = round(df.duplicated().mean() * 100, 2)
        ml_ready_score = round(
            (completeness * 0.4) +
            ((100 - duplicate_pct) * 0.3) +
            (min(len(numeric_cols)/df.shape[1] if df.shape[1] > 0 else 0, 1) * 100 * 0.15) +
            (min(len(categorical_cols)/df.shape[1] if df.shape[1] > 0 else 0, 1) * 100 * 0.15),
            2
        )

        st.markdown("## 🤖 ML Readiness Score ")
        st.markdown(f"""
        <div style="background:linear-gradient(to right, #ff4b4b, #ff9999, #00ff4b); 
                    width:100%; height:25px; border-radius:5px; position:relative;">
            <div style="position:absolute; left:{ml_ready_score}%; top:0; transform:translateX(-50%);
                        color:black; font-weight:bold;">{ml_ready_score}/100</div>
        </div>
        """, unsafe_allow_html=True)

        # ---------- ML ALGORITHM SUGGESTIONS ----------
        st.markdown("### 🧠 Suggested ML Algorithms")
        if ml_ready_score < 40:
            st.info("**Low ML Readiness**\n\n**Suggested:** Linear/Logistic Regression, Naive Bayes")
        elif 40 <= ml_ready_score < 70:
            st.warning("**Moderate ML Readiness**\n\n**Suggested:** Decision Tree, Random Forest, KNN, SVM")
        else:
            st.success("**High ML Readiness 🚀**\n\n**Suggested:** XGBoost, Neural Networks, Ensemble Models, AutoML")

        # ---------- DOWNLOAD BUTTON ----------
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            st.markdown('<div class="footer-container">', unsafe_allow_html=True)

            # Center the button
            st.markdown('<div style="text-align:center; margin-bottom:10px;">', unsafe_allow_html=True)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD PDF REPORT",
                    data=f,
                    file_name="Documentation_Report.pdf",
                    mime="application/pdf"
                )
            st.markdown('</div>', unsafe_allow_html=True)

            # Footer text with copyright + license + GitHub
            st.markdown("""
            <div style="text-align:center; font-size:12px; margin-top:5px;">
                © 2025 Auto-Documenter | Apache License 2.0 | 
                <a href="https://github.com/vantom-ops" target="_blank" style="color:white;">GitHub</a>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)





