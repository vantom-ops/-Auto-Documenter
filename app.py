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

# Custom CSS for the Big Download Button
st.markdown("""
    <style>
    div.stDownloadButton > button {
        width: 100% !important;
        height: 60px !important;
        background-color: #007bff !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        margin-top: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate interactive documentation.")
st.markdown("---")

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
    st.dataframe(df.head(10), use_container_width=True)

    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result

    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # ---------- DATASET METRICS ----------
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

        # ---------- "OLD TYPE" GRAPH SECTION ----------
        st.markdown("## 📊 Column Trends")
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        selectable_cols = [c for c in numeric_cols if df[c].nunique() > 1]
        
        if selectable_cols:
            selected_col = st.selectbox("Select column to view trend:", selectable_cols)
            
            # Formatting x-axis to fix decimal issues seen in previous version
            plot_df = df.copy()
            x_col = None
            for c in df.columns:
                if any(k in c.lower() for k in ['period', 'year', 'date']):
                    x_col = c
                    plot_df[x_col] = plot_df[x_col].astype(str)
                    break
            
            # "Old Type" Aesthetics: High contrast, grid lines, and simple markers
            fig = px.line(plot_df, x=x_col, y=selected_col, title=f"{selected_col} Trend")
            fig.update_traces(line=dict(width=2, color="#000080"), marker=dict(size=4))
            fig.update_layout(
                plot_bgcolor="white",
                xaxis=dict(showgrid=True, gridcolor='lightgrey', linecolor='black'),
                yaxis=dict(showgrid=True, gridcolor='lightgrey', linecolor='black'),
                title_font=dict(size=18, family="Arial"),
            )
            st.plotly_chart(fig, use_container_width=True)

        # ---------- ML READINESS SCORE (GRAPHIC BAR) ----------
        st.markdown("## 🤖 Machine Learning Insights")
        score = 79.28 # Fixed score as requested
        
        # Color logic based on score
        bar_color = "#ff4b4b" if score < 50 else "#ffea00" if score < 75 else "#00ff4b"
        
        st.markdown(f"**ML Readiness Score: {score}/100**")
        st.markdown(f"""
            <div style="background-color: #e0e0e0; border-radius: 13px; padding: 3px; width: 100%;">
                <div style="background-color: {bar_color}; width: {score}%; height: 20px; border-radius: 10px; transition: width 0.5s ease-in-out;">
                </div>
            </div>
            <br>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Suggested Algorithms:**
        - **Regression:** Linear Regression, Random Forest
        - **Classification:** XGBoost, Logistic Regression
        """)

        # ---------- BIG PDF DOWNLOAD BUTTON AT BOTTOM ----------
        st.markdown("---")
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD FULL DOCUMENTATION REPORT (PDF)",
                    data=f,
                    file_name=f"Analysis_Report_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("Report PDF not found. Please regenerate documentation.")
